#%%

import pandas as pd
from pathlib import Path
import zipfile
import grainleg

#%%

FAO_ELEMENT_AREA_HARVESTED = 5312
FAO_ELEMENT_PRODUCTION = 5510
INDATA_DIR = Path(__file__).parent / "indata"
OUTDATA_DIR = Path(__file__).parent / "outdata"

if OUTDATA_DIR.exists():
    print(f"Not doing anything because outdata directory exists: '{OUTDATA_DIR}'")
    exit(1)
OUTDATA_DIR.mkdir(exist_ok=False)

#%%

# Read the FAOSTAT production data


def pandas_read_zipped_csv(zipfile_path, contents_path, *args, **kwargs):
    with zipfile.ZipFile(zipfile_path) as zf:
        with zf.open(contents_path) as cf:
            return pd.read_csv(cf, *args, **kwargs)


fao_production_data = (
    pandas_read_zipped_csv(
        INDATA_DIR / "Production_Crops_Livestock_E_All_Data_(Normalized).zip",
        "Production_Crops_Livestock_E_All_Data_(Normalized).csv",
        encoding="cp1252",
    )
    .set_index(
        [
            "Area Code",
            "Area",
            "Item Code",
            "Item",
            "Element Code",
            "Year",
        ]
    )
    .Value
)

fao_production_data

#%%

# Extract crop production data

fao_crop_data = pd.DataFrame(
    {
        "Area_harvested_ha": fao_production_data.xs(
            FAO_ELEMENT_AREA_HARVESTED, level="Element Code"
        ),
        "Production_Mg": fao_production_data.xs(
            FAO_ELEMENT_PRODUCTION, level="Element Code"
        ),
    }
)

#%%

grain_legumes_results = grainleg.estimate_fixation(fao_crop_data)
grain_legumes_results

#%%
peoples_table_2 = grainleg.calc_peoples_table_2(grain_legumes_results)
peoples_table_2.to_csv(OUTDATA_DIR / "results-like-peoples-table-2.csv")
peoples_table_2

#%%
peoples_table_4 = grainleg.calc_peoples_table_4(grain_legumes_results)
peoples_table_4.to_csv(OUTDATA_DIR / "results-like-peoples-table-4.csv")
peoples_table_4
