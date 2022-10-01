#%%
from ast import fix_missing_locations
import pandas as pd
from pathlib import Path

# %%

INDATA_DIR = Path(__file__).parent / "indata"

fixation_coefficients = pd.read_csv(
    INDATA_DIR / "nonsymbiotic-fixation-coefficients-kg-per-ha-harvest.csv",
    index_col="Item Code",
)[["Low", "Main", "High"]]

fixation_coefficients

#%%


def estimate_fixation_MgN(areas):
    assert isinstance(areas, pd.Series)
    assert areas.name == "Area_harvested_ha", areas.name
    return fixation_coefficients.mul(1e-3).mul(areas, level="Item Code", axis=0)
