# 1. Import
import os
import glob
import json
import math
import cv2 as cv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

def display(value):
    print(value.to_string() if hasattr(value, "to_string") else value)

print("OpenCV:", cv.__version__)

import argparse
parser=argparse.ArgumentParser(description="Kalibrasi chessboard 9x6; ekspor parameter dan error per-view.")
parser.add_argument("--images",type=Path,required=True)
parser.add_argument("--output",type=Path,default=Path("hasil"))
args=parser.parse_args()
if not args.images.is_dir():
    parser.error("Folder gambar tidak ditemukan.")

# 3. KONFIGURASI

IMAGE_DIR = str(args.images.resolve())
OUTPUT_DIR = str(args.output.resolve())
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SUDAH DIKUNCI SESUAI PAPAN YANG DIPAKAI
CHECKERBOARD = (9, 6)  # (kolom inner-corner, baris inner-corner)

# Ukur fisik satu kotak chessboard.
# Isi None jika belum diukur; intrinsic tetap dapat dihitung.
SQUARE_SIZE_MM = None

# Isi hanya jika focal length tertulis pada lensa fisik.
# Contoh: 25.0 atau 30.0. Jangan mengisi berdasarkan tebakan.
LENS_NOMINAL_FOCAL_MM = None

# Outlier tidak dibuang default.
REMOVE_OUTLIERS = False
MIN_IMAGES_AFTER_FILTER = 10

# Spesifikasi kamera
CAMERA_SPEC = {
    "brand": "HuaTeng Vision",
    "model": "HT-SUA501GC-T1V-C",
    "sensor": "Sony IMX264",
    "sensor_type": "CMOS",
    "shutter": "Global Shutter",
    "color": "Color",
    "resolution_w": 2448,
    "resolution_h": 2048,
    "megapixel": 5.0,
    "pixel_pitch_um_x": 3.45,
    "pixel_pitch_um_y": 3.45,
    "optical_format": '2/3"',
    "frame_rate_fps": 40.5,
    "dynamic_range_db": 73.6,
    "snr_db": 40.4,
    "bit_depth": "Bayer RG 8-bit / Bayer 12-bit",
    "ir_cut_nm": 650,
    "interface": "USB 3.0 Type-B",
    "lens_mount": "C-Mount",
    "exposure_time_ms": "0.0118–12377.1",
}

print("CHECKERBOARD:", CHECKERBOARD)
print("Camera:", CAMERA_SPEC["model"])


# 4. Cari dan validasi gambar

exts = ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG", "*.bmp", "*.BMP"]
image_paths = []
for ext in exts:
    image_paths.extend(glob.glob(os.path.join(IMAGE_DIR, ext)))
image_paths = sorted(set(image_paths))

if not image_paths:
    raise FileNotFoundError(f"Tidak ada gambar di: {IMAGE_DIR}")

print("Jumlah gambar:", len(image_paths))

resolutions = []
for p in image_paths:
    img = cv.imread(p)
    if img is None:
        continue
    h, w = img.shape[:2]
    resolutions.append((w, h))

unique_res = sorted(set(resolutions))
print("Resolusi ditemukan:", unique_res)

spec_res = (CAMERA_SPEC["resolution_w"], CAMERA_SPEC["resolution_h"])
if len(unique_res) == 1 and unique_res[0] == spec_res:
    print("✓ Resolusi dataset SESUAI spesifikasi kamera:", spec_res)
else:
    print("⚠ Resolusi dataset tidak identik dengan spesifikasi:", spec_res)
    print("  Jika gambar di-resize/crop/ROI, parameter K berlaku untuk resolusi tersebut.")


# 5. Fungsi deteksi chessboard 9x6

def detect_chessboard(gray, pattern=CHECKERBOARD):
    # SB: langsung menghasilkan sub-pixel corners dan umumnya lebih akurat.
    sb_flags = cv.CALIB_CB_NORMALIZE_IMAGE | cv.CALIB_CB_EXHAUSTIVE
    if hasattr(cv, "CALIB_CB_ACCURACY"):
        sb_flags |= cv.CALIB_CB_ACCURACY

    try:
        ok, corners = cv.findChessboardCornersSB(gray, pattern, flags=sb_flags)
        if ok:
            return True, corners.astype(np.float32), "SB"
    except cv.error:
        pass

    # Fallback klasik
    flags = cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_NORMALIZE_IMAGE
    ok, corners = cv.findChessboardCorners(gray, pattern, flags)

    if ok:
        criteria = (
            cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER,
            100,
            1e-6
        )
        corners = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        return True, corners.astype(np.float32), "Classic+SubPix"

    return False, None, None


# 6. Deteksi seluruh gambar

cols, rows = CHECKERBOARD

# Untuk intrinsic, skala object point boleh 1 unit/kotak.
# Jika ukuran fisik diketahui, gunakan mm agar tvec langsung dalam mm.
object_square = float(SQUARE_SIZE_MM) if SQUARE_SIZE_MM is not None else 1.0

objp = np.zeros((rows * cols, 3), np.float32)
objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
objp[:, :2] *= object_square

objpoints = []
imgpoints = []
valid_paths = []
methods = []
image_size = None

corner_dir = os.path.join(OUTPUT_DIR, "detected_corners")
os.makedirs(corner_dir, exist_ok=True)

for i, path in enumerate(image_paths, 1):
    img = cv.imread(path)
    if img is None:
        print("[SKIP]", os.path.basename(path), "- gagal dibaca")
        continue

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    current_size = gray.shape[::-1]

    if image_size is None:
        image_size = current_size
    elif current_size != image_size:
        print("[SKIP]", os.path.basename(path), "- resolusi berbeda", current_size)
        continue

    ok, corners, method = detect_chessboard(gray)

    if not ok:
        print("[GAGAL]", os.path.basename(path))
        continue

    objpoints.append(objp.copy())
    imgpoints.append(corners)
    valid_paths.append(path)
    methods.append(method)

    vis = img.copy()
    cv.drawChessboardCorners(vis, CHECKERBOARD, corners, True)
    cv.imwrite(
        os.path.join(corner_dir, f"{i:02d}_{os.path.basename(path)}"),
        vis
    )

    print("[OK]", os.path.basename(path), "-", method)

print("\n=== DETEKSI ===")
print("Total       :", len(image_paths))
print("Valid       :", len(valid_paths))
print("Tidak valid :", len(image_paths) - len(valid_paths))
print("Pattern     :", CHECKERBOARD, "inner corners")
print("Resolusi    :", image_size)

if len(valid_paths) < 10:
    print("⚠ OpenCV menyarankan secara praktis memakai setidaknya sekitar 10 snapshot yang baik dan berbeda.")


# 7. Visualisasi beberapa deteksi

n_show = min(9, len(valid_paths))
if n_show:
    rows_plot = int(np.ceil(n_show / 3))
    plt.figure(figsize=(15, 4.5 * rows_plot))

    for i in range(n_show):
        img = cv.imread(valid_paths[i])
        vis = img.copy()
        cv.drawChessboardCorners(vis, CHECKERBOARD, imgpoints[i], True)
        vis = cv.cvtColor(vis, cv.COLOR_BGR2RGB)

        plt.subplot(rows_plot, 3, i + 1)
        plt.imshow(vis)
        plt.title(os.path.basename(valid_paths[i]))
        plt.axis("off")

    plt.tight_layout()
    plt.show()


# 8. Diagnostik sebaran chessboard pada frame

centers = []
area_ratios = []

w, h = image_size

for pts in imgpoints:
    xy = pts.reshape(-1, 2)

    centers.append(xy.mean(axis=0))

    min_xy = xy.min(axis=0)
    max_xy = xy.max(axis=0)
    box_area = np.prod(max_xy - min_xy)
    area_ratios.append(float(box_area / (w * h)))

centers = np.array(centers)
area_ratios = np.array(area_ratios)

plt.figure(figsize=(8, 6))
plt.scatter(centers[:, 0], centers[:, 1], s=60)
plt.xlim(0, w)
plt.ylim(h, 0)
plt.axvline(w/2, linestyle="--")
plt.axhline(h/2, linestyle="--")
plt.xlabel("x (px)")
plt.ylabel("y (px)")
plt.title("Sebaran Pusat Chessboard pada Frame")
plt.grid(True)
plt.show()

print("Area bounding-box chessboard terhadap frame:")
print(f"  min  : {area_ratios.min()*100:.2f}%")
print(f"  mean : {area_ratios.mean()*100:.2f}%")
print(f"  max  : {area_ratios.max()*100:.2f}%")

margin_x = np.min(np.column_stack([centers[:,0], w-centers[:,0]]))
margin_y = np.min(np.column_stack([centers[:,1], h-centers[:,1]]))
print(f"Pusat chessboard terdekat ke tepi X: {margin_x:.1f} px")
print(f"Pusat chessboard terdekat ke tepi Y: {margin_y:.1f} px")
print("\nCatatan: untuk estimasi distorsi yang lebih kuat, ambil beberapa foto dengan chessboard lebih dekat ke tepi/corner frame dan tilt keluar bidang yang jelas.")


# 9. Kalibrasi awal dengan calibrateCameraExtended

if len(valid_paths) < 3:
    raise RuntimeError("Gambar valid terlalu sedikit untuk kalibrasi.")

rms, camera_matrix, dist_coeffs, rvecs, tvecs, std_intr, std_ext, per_view_errors = \
    cv.calibrateCameraExtended(
        objpoints,
        imgpoints,
        image_size,
        None,
        None
    )

per_view_errors = per_view_errors.ravel()

print("=== HASIL KALIBRASI AWAL ===")
print(f"RMS reprojection error: {rms:.6f} px")
print("\nCamera matrix K:")
print(camera_matrix)
print("\nDistortion coefficients [k1 k2 p1 p2 k3 ...]:")
print(dist_coeffs.ravel())

fx = float(camera_matrix[0, 0])
fy = float(camera_matrix[1, 1])
cx = float(camera_matrix[0, 2])
cy = float(camera_matrix[1, 2])

print("\nIntrinsik:")
print(f"fx = {fx:.6f} px")
print(f"fy = {fy:.6f} px")
print(f"cx = {cx:.6f} px")
print(f"cy = {cy:.6f} px")


# 10. Error per gambar + kandidat outlier robust

error_df = pd.DataFrame({
    "file": [os.path.basename(p) for p in valid_paths],
    "method": methods,
    "reprojection_error_px": per_view_errors
}).sort_values("reprojection_error_px", ascending=False).reset_index(drop=True)

display(error_df)

median_err = float(np.median(per_view_errors))
mad = float(np.median(np.abs(per_view_errors - median_err)))

# Robust sigma estimate
robust_sigma = 1.4826 * mad
outlier_threshold = median_err + 3.0 * robust_sigma

print(f"Median error       : {median_err:.4f} px")
print(f"MAD                : {mad:.4f} px")
print(f"Outlier threshold  : {outlier_threshold:.4f} px")

outlier_mask = per_view_errors > outlier_threshold
outlier_indices = np.where(outlier_mask)[0]

if len(outlier_indices) == 0:
    print("✓ Tidak ada outlier kuat menurut kriteria median + 3×MAD.")
else:
    print("⚠ Kandidat outlier:")
    for idx in outlier_indices:
        print(" -", os.path.basename(valid_paths[idx]), per_view_errors[idx])

plt.figure(figsize=(12, 4))
plt.plot(range(1, len(per_view_errors)+1), per_view_errors, marker="o")
plt.axhline(median_err, linestyle="--", label="median")
plt.axhline(outlier_threshold, linestyle=":", label="threshold outlier")
plt.xlabel("Gambar valid ke-")
plt.ylabel("Per-view RMS (px)")
plt.title("Reprojection Error per Gambar")
plt.grid(True)
plt.legend()
plt.show()


# 11. Opsional: recalibrate setelah membuang outlier kuat

if REMOVE_OUTLIERS and len(outlier_indices) > 0:
    keep = ~outlier_mask

    filtered_objpoints = [p for p, k in zip(objpoints, keep) if k]
    filtered_imgpoints = [p for p, k in zip(imgpoints, keep) if k]
    filtered_paths = [p for p, k in zip(valid_paths, keep) if k]
    filtered_methods = [p for p, k in zip(methods, keep) if k]

    if len(filtered_paths) < MIN_IMAGES_AFTER_FILTER:
        print("Outlier TIDAK dibuang karena gambar tersisa terlalu sedikit.")
    else:
        rms, camera_matrix, dist_coeffs, rvecs, tvecs, std_intr, std_ext, per_view_errors = \
            cv.calibrateCameraExtended(
                filtered_objpoints,
                filtered_imgpoints,
                image_size,
                None,
                None
            )

        objpoints = filtered_objpoints
        imgpoints = filtered_imgpoints
        valid_paths = filtered_paths
        methods = filtered_methods
        per_view_errors = per_view_errors.ravel()

        fx = float(camera_matrix[0, 0])
        fy = float(camera_matrix[1, 1])
        cx = float(camera_matrix[0, 2])
        cy = float(camera_matrix[1, 2])

        print("Recalibration selesai.")
        print("RMS baru:", rms)
else:
    print("REMOVE_OUTLIERS=False -> semua gambar valid tetap dipakai.")


# 12. Konversi ke satuan fisik dan hitung FOV

pixel_pitch_x_mm = CAMERA_SPEC["pixel_pitch_um_x"] / 1000.0
pixel_pitch_y_mm = CAMERA_SPEC["pixel_pitch_um_y"] / 1000.0

spec_w = CAMERA_SPEC["resolution_w"]
spec_h = CAMERA_SPEC["resolution_h"]

sensor_width_mm = spec_w * pixel_pitch_x_mm
sensor_height_mm = spec_h * pixel_pitch_y_mm
sensor_diagonal_mm = math.hypot(sensor_width_mm, sensor_height_mm)

focal_x_mm = fx * pixel_pitch_x_mm
focal_y_mm = fy * pixel_pitch_y_mm
focal_mean_mm = (focal_x_mm + focal_y_mm) / 2.0

fov_x_deg = math.degrees(2 * math.atan(image_size[0] / (2 * fx)))
fov_y_deg = math.degrees(2 * math.atan(image_size[1] / (2 * fy)))

center_x = image_size[0] / 2.0
center_y = image_size[1] / 2.0
principal_dx_px = cx - center_x
principal_dy_px = cy - center_y
principal_dx_mm = principal_dx_px * pixel_pitch_x_mm
principal_dy_mm = principal_dy_px * pixel_pitch_y_mm

fxy_diff_pct = abs(fx - fy) / ((fx + fy) / 2.0) * 100.0

std_intr = std_intr.ravel()
std_fx_px = float(std_intr[0]) if len(std_intr) > 0 else np.nan
std_fy_px = float(std_intr[1]) if len(std_intr) > 1 else np.nan

print("=== KONVERSI & SANITY CHECK ===")
print(f"Sensor aktif hitung : {sensor_width_mm:.4f} × {sensor_height_mm:.4f} mm")
print(f"Diagonal aktif      : {sensor_diagonal_mm:.4f} mm")
print(f"Optical format spec : {CAMERA_SPEC['optical_format']}")
print()
print(f"fx                  : {fx:.3f} px = {focal_x_mm:.4f} mm")
print(f"fy                  : {fy:.3f} px = {focal_y_mm:.4f} mm")
print(f"f mean              : {focal_mean_mm:.4f} mm")
print(f"|fx-fy| relatif     : {fxy_diff_pct:.3f}%")
print()
print(f"HFOV                : {fov_x_deg:.3f}°")
print(f"VFOV                : {fov_y_deg:.3f}°")
print()
print(f"Principal point     : ({cx:.2f}, {cy:.2f}) px")
print(f"Pusat frame         : ({center_x:.2f}, {center_y:.2f}) px")
print(f"Offset principal    : ({principal_dx_px:+.2f}, {principal_dy_px:+.2f}) px")
print(f"Offset fisik        : ({principal_dx_mm:+.4f}, {principal_dy_mm:+.4f}) mm")
print()
print(f"Std fx              : ±{std_fx_px:.3f} px")
print(f"Std fy              : ±{std_fy_px:.3f} px")

if fxy_diff_pct > 5:
    print("\n⚠ fx dan fy berbeda >5%. Periksa pattern, kualitas foto, crop/resize, dan variasi pose.")
else:
    print("\n✓ fx dan fy konsisten secara rasio untuk pixel pitch X=Y.")


# 13. Perbandingan otomatis dengan spesifikasi

rows_compare = [
    ["Model", CAMERA_SPEC["model"], CAMERA_SPEC["model"], "Sesuai"],
    ["Resolusi", f"{image_size[0]} × {image_size[1]} px",
     f"{spec_w} × {spec_h} px",
     "Sesuai" if tuple(image_size) == (spec_w, spec_h) else "Berbeda"],
    ["Sensor", CAMERA_SPEC["sensor"], CAMERA_SPEC["sensor"], "Sesuai"],
    ["Shutter", CAMERA_SPEC["shutter"], CAMERA_SPEC["shutter"], "Sesuai"],
    ["Pixel pitch", "dipakai untuk konversi", "3.45 × 3.45 µm", "Referensi spesifikasi"],
    ["Sensor aktif", f"{sensor_width_mm:.4f} × {sensor_height_mm:.4f} mm",
     "≈ 8.45 × 7.07 mm (IMX264)", "Konsisten"],
    ["Diagonal aktif", f"{sensor_diagonal_mm:.4f} mm",
     "≈ 11.01–11.02 mm (IMX264)", "Konsisten"],
    ["fx", f"{fx:.3f} px = {focal_x_mm:.4f} mm", "Tergantung lensa", "Butuh spec lensa"],
    ["fy", f"{fy:.3f} px = {focal_y_mm:.4f} mm", "Tergantung lensa", "Butuh spec lensa"],
    ["HFOV", f"{fov_x_deg:.3f}°", "Tergantung lensa", "Butuh spec lensa"],
    ["VFOV", f"{fov_y_deg:.3f}°", "Tergantung lensa", "Butuh spec lensa"],
    ["Principal point", f"({cx:.2f}, {cy:.2f}) px",
     f"pusat geometris ≈ ({center_x:.1f}, {center_y:.1f}) px",
     f"offset ({principal_dx_px:+.1f}, {principal_dy_px:+.1f}) px"],
    ["RMS reprojection", f"{rms:.4f} px", "Tidak dicantumkan datasheet",
     "Metrik kualitas kalibrasi"],
]

if LENS_NOMINAL_FOCAL_MM is not None:
    focal_error_pct = abs(focal_mean_mm - LENS_NOMINAL_FOCAL_MM) / LENS_NOMINAL_FOCAL_MM * 100.0
    rows_compare.append([
        "Focal length nominal lensa",
        f"{focal_mean_mm:.4f} mm (hasil kalibrasi)",
        f"{LENS_NOMINAL_FOCAL_MM:.4f} mm",
        f"error {focal_error_pct:.3f}%"
    ])
else:
    focal_error_pct = None
    rows_compare.append([
        "Focal length nominal lensa",
        f"{focal_mean_mm:.4f} mm (hasil kalibrasi)",
        "BELUM DIISI",
        "Baca angka mm pada lensa fisik"
    ])

comparison_df = pd.DataFrame(
    rows_compare,
    columns=["Parameter", "Hasil Kalibrasi", "Spesifikasi/Referensi", "Analisis"]
)

display(comparison_df)


# 14. Undistort contoh gambar

sample_path = valid_paths[0]
img = cv.imread(sample_path)
h_img, w_img = img.shape[:2]

new_K, roi = cv.getOptimalNewCameraMatrix(
    camera_matrix, dist_coeffs, (w_img, h_img), 1, (w_img, h_img)
)

und = cv.undistort(img, camera_matrix, dist_coeffs, None, new_K)

plt.figure(figsize=(16, 6))
plt.subplot(1, 2, 1)
plt.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
plt.title("Original")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(cv.cvtColor(und, cv.COLOR_BGR2RGB))
plt.title("Undistorted")
plt.axis("off")

plt.tight_layout()
plt.show()

und_path = os.path.join(OUTPUT_DIR, "contoh_undistorted.jpg")
cv.imwrite(und_path, und)
print("Saved:", und_path)


# 15. Pose estimation / jarak
# Hanya diberi satuan mm jika ukuran kotak fisik sudah diisi.

pose_img = cv.imread(valid_paths[0])
pose_gray = cv.cvtColor(pose_img, cv.COLOR_BGR2GRAY)
ok, pose_corners, _ = detect_chessboard(pose_gray)

if not ok:
    print("Pose estimation dilewati: corner gagal dideteksi.")
else:
    success, rvec, tvec = cv.solvePnP(
        objp, pose_corners, camera_matrix, dist_coeffs,
        flags=cv.SOLVEPNP_ITERATIVE
    )

    if not success:
        print("solvePnP gagal.")
    else:
        distance_units = float(np.linalg.norm(tvec))

        if SQUARE_SIZE_MM is None:
            print("Pose berhasil.")
            print("tvec:", tvec.ravel())
            print("Jarak masih dalam satuan 'jumlah kotak'.")
            print("Isi SQUARE_SIZE_MM dengan ukuran kotak fisik agar jarak menjadi mm/cm.")
        else:
            print("Pose berhasil.")
            print("tvec [mm]:", tvec.ravel())
            print(f"Jarak kamera ke origin chessboard: {distance_units:.2f} mm")
            print(f"Jarak kamera ke origin chessboard: {distance_units/10:.2f} cm")


# 16. Simpan semua hasil

npz_path = os.path.join(OUTPUT_DIR, "camera_calibration_v2.npz")
np.savez(
    npz_path,
    camera_matrix=camera_matrix,
    dist_coeffs=dist_coeffs,
    image_size=np.array(image_size),
    checkerboard=np.array(CHECKERBOARD),
    square_size_mm=np.array(np.nan if SQUARE_SIZE_MM is None else SQUARE_SIZE_MM),
    rms=np.array(rms),
    per_view_errors=np.array(per_view_errors)
)

json_path = os.path.join(OUTPUT_DIR, "camera_calibration_v2.json")
json_data = {
    "camera_spec": CAMERA_SPEC,
    "checkerboard_inner_corners": list(CHECKERBOARD),
    "square_size_mm": SQUARE_SIZE_MM,
    "valid_images": len(valid_paths),
    "image_size": list(image_size),
    "rms_reprojection_error_px": float(rms),
    "camera_matrix": camera_matrix.tolist(),
    "distortion_coefficients": dist_coeffs.ravel().tolist(),
    "fx_px": fx,
    "fy_px": fy,
    "cx_px": cx,
    "cy_px": cy,
    "focal_x_mm_from_pixel_pitch": focal_x_mm,
    "focal_y_mm_from_pixel_pitch": focal_y_mm,
    "focal_mean_mm_from_pixel_pitch": focal_mean_mm,
    "horizontal_fov_deg": fov_x_deg,
    "vertical_fov_deg": fov_y_deg,
    "sensor_width_mm": sensor_width_mm,
    "sensor_height_mm": sensor_height_mm,
    "sensor_diagonal_mm": sensor_diagonal_mm,
    "principal_point_offset_px": [principal_dx_px, principal_dy_px],
    "principal_point_offset_mm": [principal_dx_mm, principal_dy_mm],
    "lens_nominal_focal_mm": LENS_NOMINAL_FOCAL_MM,
    "focal_length_error_pct": focal_error_pct,
    "per_view_errors_px": {
        os.path.basename(p): float(e)
        for p, e in zip(valid_paths, per_view_errors)
    }
}

with open(json_path, "w") as f:
    json.dump(json_data, f, indent=2)

yaml_path = os.path.join(OUTPUT_DIR, "camera_calibration_v2.yaml")
fs = cv.FileStorage(yaml_path, cv.FILE_STORAGE_WRITE)
fs.write("camera_matrix", camera_matrix)
fs.write("distortion_coefficients", dist_coeffs)
fs.write("image_width", int(image_size[0]))
fs.write("image_height", int(image_size[1]))
fs.write("rms_reprojection_error_px", float(rms))
fs.write("focal_x_mm", float(focal_x_mm))
fs.write("focal_y_mm", float(focal_y_mm))
fs.release()

compare_csv = os.path.join(OUTPUT_DIR, "perbandingan_spesifikasi.csv")
comparison_df.to_csv(compare_csv, index=False)

error_csv = os.path.join(OUTPUT_DIR, "error_per_gambar.csv")
pd.DataFrame({
    "file": [os.path.basename(p) for p in valid_paths],
    "reprojection_error_px": per_view_errors
}).to_csv(error_csv, index=False)

print("=== FILE OUTPUT ===")
for p in [npz_path, json_path, yaml_path, compare_csv, error_csv, und_path]:
    print("-", p)

