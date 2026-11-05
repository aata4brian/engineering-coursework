import numpy as np
import pandas as pd

from preprocessing import Preprocessing, example

train, test = example()
prep = Preprocessing().fit(train)
assert prep.medians["Age"] == 27
assert prep.bounds == (60, 220)
np.testing.assert_allclose(prep.transform(train).iloc[:, :2].mean(), 0, atol=1e-12)
expected = prep.transform(test)
assert expected.shape == (2, 4)
assert expected.iloc[0, 0] == 0
assert expected.iloc[0, 2:].tolist() == [0, 0]
assert expected.iloc[1, 2:].tolist() == [1, 0]
assert prep.clean_numeric(test).iloc[0, 1] == 220
extreme = test.copy()
extreme.loc[0, "Annual_Spending"] = 1e9
pd.testing.assert_frame_equal(prep.transform(extreme), expected)
pd.testing.assert_frame_equal(prep.transform(test), expected)
for invalid in (train.assign(Age=np.nan), train.assign(Age=np.inf)):
    try:
        Preprocessing().fit(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Input latih tidak valid diterima.")

print("Lulus: imputasi, capping, standardisasi, kategori baru, dan input latih tidak valid.")
