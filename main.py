#%%

import pandas as pd
from pathlib import Path
import zipfile
import matplotlib.pyplot as plt
import matplotlib.cm
import grainleg
import nonsymbiotic

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

fao_country_codes = pd.read_csv(
    INDATA_DIR / "faostat_definitions_country_group_2022-10-01.csv"
)["Country Code"].unique()
fao_country_codes

#%%

fao_item_codes = pd.read_csv(
    INDATA_DIR / "Items_Primary_Production.csv", encoding="cp1252"
)["Item Code"].unique()
fao_item_codes

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
    .reindex(fao_country_codes, level="Area Code")
    .reindex(fao_item_codes, level="Item Code")
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

grain_legumes_results = grainleg.estimate_fixation(
    fao_crop_data.loc[fao_crop_data["Production_Mg"] > 0]
)
grain_legumes_results


#%%
grain_legumes_fixation = (
    grain_legumes_results["Crop_N_fixed_MgN"]
    .rename("Main")
    .to_frame()
    .assign(
        Low=lambda d: d.Main * 0.9,
        High=lambda d: d.Main * 1.1,
    )[["Low", "Main", "High"]]
)
grain_legumes_fixation.to_csv(OUTDATA_DIR / "grain-legumes-symbiotic-fixation-MgN.csv")
grain_legumes_fixation

#%%
herridge_table_2 = grainleg.calc_herridge_table_2(grain_legumes_results)
herridge_table_2.to_csv(OUTDATA_DIR / "results-like-herridge-table-2.csv")
herridge_table_2

#%%
herridge_table_4 = grainleg.calc_herridge_table_4(grain_legumes_results)
herridge_table_4.to_csv(OUTDATA_DIR / "results-like-herridge-table-4.csv")
herridge_table_4

#%%
nonsymbiotic_fixation = nonsymbiotic.estimate_fixation_MgN(
    fao_crop_data["Area_harvested_ha"]
).dropna(how="all")
nonsymbiotic_fixation.to_csv(OUTDATA_DIR / "nonsymbiotic-fixation-MgN.csv")
nonsymbiotic_fixation

#%%

specific_summary_categories = {
    "Grain legumes": list(set(grain_legumes_fixation.dropna().index.unique("Item"))),
    "Rice": ["Rice"],
    "Sugar cane": ["Sugar cane"],
}

tr_crop_item_to_summary_category = pd.Series(
    index=fao_crop_data.index.unique("Item"), data="Other", name="Crop category"
)
for category, names in specific_summary_categories.items():
    tr_crop_item_to_summary_category[names] = category
tr_crop_item_to_summary_category

#%%
summary_country_crop = (
    pd.concat(
        [
            grain_legumes_fixation,
            nonsymbiotic_fixation,
        ]
    )
    .groupby(["Area Code", "Area", "Item Code", "Item", "Year"])
    .sum()
)
summary_country_crop.to_csv(OUTDATA_DIR / "total-fixation-country-crop-MgN.csv")
summary_country_crop

# %%

summary_country_cropcat = (
    summary_country_crop.join(tr_crop_item_to_summary_category)
    .groupby(["Area Code", "Area", "Crop category", "Year"])
    .sum()
)
summary_country_cropcat.to_csv(OUTDATA_DIR / "total-fixation-country-cropcat-MgN.csv")
summary_country_cropcat

# %%

summary_crop = summary_country_crop.groupby(["Item Code", "Item", "Year"]).sum()
summary_crop.to_csv(OUTDATA_DIR / "total-fixation-crop-MgN.csv")
summary_crop


# %%

summary_cropcat = summary_country_cropcat.groupby(["Crop category", "Year"]).sum()
summary_cropcat.to_csv(OUTDATA_DIR / "total-fixation-cropcat-MgN.csv")
summary_cropcat


# %%

summary_country = summary_country_cropcat.groupby(["Area Code", "Year"]).sum()
summary_country.to_csv(OUTDATA_DIR / "total-fixation-country-MgN.csv")
summary_country


# %%

fig, ax = plt.subplots()


plot_data_all = (
    summary_cropcat.unstack().T.assign(TOTAL=lambda d: d.sum(axis=1)).T.stack()
)
colors = dict(
    zip(
        plot_data_all.index.unique("Crop category"),
        matplotlib.cm.get_cmap("tab10").colors,
    )
)

for cropcat, data in plot_data_all.groupby("Crop category"):
    plot_data = data.droplevel("Crop category").mul(1e-6)
    ax.fill_between(
        plot_data.index,
        plot_data["Low"],
        plot_data["High"],
        color=colors[cropcat],
        alpha=0.2,
    )
    ax.plot(
        plot_data["Main"],
        label=cropcat,
        color=colors[cropcat],
    )

ax.grid(True)
ax.set_title(
    "Biological N fixation in global cropland (Tg N/y)\nexcluding forage legumes"
)
ax.set_ylim(0)
ax.set_xlim(1960)
ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1))

fig.savefig(OUTDATA_DIR / "results-summary-cropcat.pdf", bbox_inches="tight")

#%%

tr_area_code_m49 = pd.read_csv(
    INDATA_DIR / "faostat_definitions_country_region_2022-10-01.csv",
    index_col="Country Code",
)["M49 Code"]
tr_area_code_m49

#%%

fixation_by_m49_code = (
    summary_country.join(tr_area_code_m49, on="Area Code")
    .reset_index()
    .set_index(["M49 Code", "Year"])["Main"]
)
assert fixation_by_m49_code.index.is_unique
fixation_by_m49_code

#%%

DATA_REQUEST_STARTCOL = 1
requested_data = (
    pd.read_excel(INDATA_DIR / "Data_Request_2.xlsx", sheet_name="Data")
    .iloc[:, DATA_REQUEST_STARTCOL:]
    .set_index("m49")
    .fillna(fixation_by_m49_code.unstack())
)

requested_data.to_csv(OUTDATA_DIR / "FAO_requested_total_BNF_MgN.csv")
requested_data
