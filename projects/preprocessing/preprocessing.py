"""Contoh preprocessing dengan data pelanggan fiktif."""

import json

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ["Age", "Annual_Spending"]
CATEGORY = ["Membership_Type"]


class Preprocessing:
    def fit(self, train):
        numeric = train[NUMERIC].astype(float)
        if np.isinf(numeric.to_numpy()).any():
            raise ValueError("Kolom numerik berisi nilai tak hingga.")
        self.medians = numeric.median()
        if self.medians.isna().any():
            raise ValueError("Setiap kolom numerik perlu minimal satu nilai latih.")
        spending = numeric["Annual_Spending"].dropna()
        q1, q3 = spending.quantile([0.25, 0.75])
        iqr = q3 - q1
        self.bounds = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        self.scaler = StandardScaler().fit(self.clean_numeric(train))
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.encoder.fit(self.clean_category(train))
        return self

    def clean_numeric(self, frame):
        values = frame[NUMERIC].astype(float).fillna(self.medians)
        if not np.isfinite(values.to_numpy()).all():
            raise ValueError("Kolom numerik harus berisi nilai berhingga.")
        values["Annual_Spending"] = values["Annual_Spending"].clip(*self.bounds)
        return values

    def clean_category(self, frame):
        return frame[CATEGORY].apply(
            lambda column: column.astype("string").str.strip().str.lower()
            .replace("", pd.NA).fillna("tidak diketahui")
        )

    def transform(self, frame):
        numeric = self.scaler.transform(self.clean_numeric(frame))
        category = self.encoder.transform(self.clean_category(frame))
        return pd.DataFrame(
            np.column_stack([numeric, category]),
            index=frame.index,
            columns=[*NUMERIC, *self.encoder.get_feature_names_out(CATEGORY)],
        )


def example():
    train = pd.DataFrame(
        [(20, 100, " Basic "), (24, 120, "basic"), (None, 140, "Plus"),
         (30, 160, "plus"), (34, 1000, "PLUS")],
        columns=[*NUMERIC, *CATEGORY],
    )
    test = pd.DataFrame([(None, 5000, "Premium"), (40, 130, "Basic")], columns=train.columns)
    return train, test


def main():
    train, test = example()
    prep = Preprocessing().fit(train)
    print(json.dumps({
        "train_rows": len(train),
        "test_rows": len(test),
        "age_median_train": prep.medians["Age"],
        "spending_bounds_train": list(prep.bounds),
        "train_spending_clipped": int(
            (train["Annual_Spending"] != prep.clean_numeric(train)["Annual_Spending"]).sum()
        ),
        "test": prep.transform(test).round(6).to_dict(orient="records"),
    }, indent=2))


if __name__ == "__main__":
    main()
