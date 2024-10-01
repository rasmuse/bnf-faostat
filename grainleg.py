#%%
# Estimation of fixation in grain legumes from FAOSTAT crop production data.
# Following Peoples et al. (2021) and Herridge et al. (2022)

from pathlib import Path
import pandas as pd
import numpy as np

INDATA_DIR = Path(__file__).parent / "indata"

#%%

# Mapping of crop names from Herridge et al. (2022) to FAOSTAT item codes

tr_crops_fao_to_herridge = (
    pd.read_csv(INDATA_DIR / "crop-names-herridge.csv")
    .dropna()
    .set_index("Item Code")["Crop Herridge et al."]
)

tr_crops_fao_to_herridge

# %%

# Herridge et al. (2022) distinguish Europe and Brazil from the rest
# of the world (ROW). Here, mapping FAOSTAT country codes to these groups based on
# FAOSTAT nomenclature of what's included in "Europe".

fao_countries = pd.read_csv(
    INDATA_DIR / "faostat_definitions_country_region_2022-10-01.csv"
).set_index("Country Code")
fao_country_groups = pd.read_csv(
    INDATA_DIR / "faostat_definitions_country_group_2022-10-01.csv"
)

europe_country_codes = fao_country_groups.loc[
    lambda d: (d["Country Group"] == "Europe") | (d["Country"] == "Europe")
]["Country Code"].values

(brazil_code,) = (
    code for code, name in fao_countries["Country"].items() if name == "Brazil"
)

regions = pd.Series(index=fao_countries.index, data="ROW", name="Region Herridge et al.")
regions.update({c: "Europe" for c in europe_country_codes})
regions.update({brazil_code: "Brazil"})
regions.to_frame().join(fao_countries["Country"])

# %%

# Implement the model closely following Herridge et al. (2022)


def estimate_fixation(fao_crop_data):
    """
    Estimate symbiotic fixation in grain legumes.

    Args:
        fao_crop_data: A pandas DataFrame having columns
                "Area_harvested_ha" (hectares)
                "Production_Mg" (metric tonnes)
            and having columns or index levels
                "Item Code" (FAOSTAT crop code)
                "Area Code" (FAOSTAT area code)
    """
    result = (
        fao_crop_data.join(tr_crops_fao_to_herridge, on="Item Code", how="inner")
        .join(regions, on="Area Code", how="inner")
        .assign(
            **{
                "Yield_Mg_per_ha": get_yield,
                "HI": get_HI,
                "Shoot_DM_Mg": get_shoot_DM,
                "Shoot_N_concentration": get_N_conc_shoots,
                "Shoot_N_MgN": get_shoot_N,
                "B-G_N_factor": get_BG_N_factor,
                "Total_crop_N_MgN": get_total_crop_N,
                "Ndfa": get_Ndfa,
                "Crop_N_fixed_MgN": get_crop_N_fixed,
            }
        )
    )

    return result


def get_yield(d):
    return d["Production_Mg"] / d["Area_harvested_ha"]


def get_HI(d):
    k_dict = {
        **{crop: 0.0804 for crop in tr_crops_fao_to_herridge},
        "Soybean": 0.1178,
        "Groundnut": 0.1343,
        "Pigeonpea": 0.0517,
    }
    m_dict = {
        **{crop: 0.2839 for crop in tr_crops_fao_to_herridge},
        "Soybean": 0.2775,
        "Groundnut": 0.2614,
        "Pigeonpea": 0.1647,
    }

    k = d["Crop Herridge et al."].map(k_dict)
    m = d["Crop Herridge et al."].map(m_dict)

    return k * np.log(d["Yield_Mg_per_ha"]) + m


def get_shoot_DM(d):
    return d["Production_Mg"] / d["HI"]


def get_N_conc_shoots(d):
    k_dict = {
        **{crop: 0 for crop in tr_crops_fao_to_herridge},
        "Soybean": -0.118,
    }
    m_dict = {
        **{crop: 2.5 for crop in tr_crops_fao_to_herridge},
        "Soybean": 3.913,
        "Groundnut": 2.7,
        "Chickpea": 1.9,
        "Pigeonpea": 1.9,
        "Lupin": 2.7,
    }

    k = d["Crop Herridge et al."].map(k_dict)
    m = d["Crop Herridge et al."].map(m_dict)

    return (k * d["Shoot_DM_Mg"] / d["Area_harvested_ha"] + m) / 100


def get_shoot_N(d):
    return d["Shoot_DM_Mg"] * d["Shoot_N_concentration"]


def get_BG_N_factor(d):
    m_dict = {
        **{crop: 1.4 for crop in tr_crops_fao_to_herridge},
        "Chickpea": 2.0,
        "Pigeonpea": 2.0,
    }
    return d["Crop Herridge et al."].map(m_dict)


def get_total_crop_N(d):
    return d["Shoot_N_MgN"] * d["B-G_N_factor"]


def get_Ndfa(d):
    default_Ndfa_by_crop = {
        **{crop: 62 for crop in tr_crops_fao_to_herridge},
        "Soybean": 61,
        "Common bean": 38,
        "Pigeonpea": 74,
        "Faba bean": 74,
        "Lupin": 74,
    }
    region_specific_Ndfa = {
        ("Soybean", "Europe"): 44,
        ("Soybean", "Brazil"): 78,
    }

    result = d["Crop Herridge et al."].map(default_Ndfa_by_crop)
    for (crop, region), Ndfa_value in region_specific_Ndfa.items():
        rows = (d["Crop Herridge et al."] == crop) & (
            d["Region Herridge et al."] == region
        )
        result[rows] = Ndfa_value

    return result / 100


def get_crop_N_fixed(d):
    return d["Total_crop_N_MgN"] * d["Ndfa"]


#%%

# Function to reproduce a table similar to Herridge et al. (2022) Table 2
# to check that results agree.


SOYBEANS_CODE = {v: k for k, v in tr_crops_fao_to_herridge.items()}["Soybean"]


def calc_herridge_table_2(result):
    result = result.reset_index()
    assert result.set_index(["Area", "Year", "Item Code"]).index.is_unique
    d = (
        result.set_index(["Area", "Year", "Item Code"])
        .xs(SOYBEANS_CODE, level="Item Code")
        .xs(2018, level="Year")
        .reindex(["Brazil", "United States of America", "Argentina", "India", "China"])
    )
    return pd.DataFrame(
        {
            "Total area (Mha)": d["Area_harvested_ha"].div(1e6).round(1),
            "Grain prod (Tg)": d["Production_Mg"].div(1e6).round(1),
            "Grain yld (Mg/ha/y)": d["Yield_Mg_per_ha"],
            "Shoot DM (Tg)": d["Shoot_DM_Mg"].div(1e6).round(1),
            "Shoot N (Tg)": d["Shoot_N_MgN"].div(1e6),
            "Total crop N (Tg)": d["Total_crop_N_MgN"].div(1e6),
            "Crop N fixed (Tg)": d["Crop_N_fixed_MgN"].div(1e6).round(1),
        }
    ).round(2)


#%%

# Function to reproduce a table similar to Herridge et al. (2022) Table 4

tr_fao_group_to_herridge_group = pd.Series(
    {
        "South America": "South, Central America",
        "Central America": "South, Central America",
        "Northern America": "North America",
        "Asia": "Asia",
        "Europe": "Europe",
        "Africa": "Africa",
        "Oceania": "Oceania",
    }
).rename("Region")


def calc_herridge_table_4(result):
    result = result.reset_index()
    assert result.set_index(["Area", "Year", "Item Code"]).index.is_unique
    tr_item_code_to_legume_category = pd.Series(
        {
            code: (name if name in {"Soybean", "Groundnut"} else "Pulses")
            for code, name in tr_crops_fao_to_herridge.items()
        }
    ).rename("Legume category")

    d = (
        result.join(
            fao_country_groups.set_index("Country Code")["Country Group"],
            on="Area Code",
        )
        .join(tr_fao_group_to_herridge_group, on="Country Group")
        .join(
            tr_item_code_to_legume_category,
            on="Item Code",
        )
        .groupby(["Year", "Legume category", "Region"])
        .sum(numeric_only=True)
        .assign(Yield_Mg_per_ha=lambda d: d["Production_Mg"] / d["Area_harvested_ha"])
        .xs(2018, level="Year")
        .reindex(
            ["Soybean", "Groundnut", "Pulses"],
            level="Legume category",
        )
        .reindex(
            [
                "South, Central America",
                "North America",
                "Asia",
                "Europe",
                "Africa",
                "Oceania",
            ],
            level="Region",
        )
        .pipe(
            lambda d: (
                pd.DataFrame(
                    {
                        "Total area (Mha)": d["Area_harvested_ha"].div(1e6).round(1),
                        "Grain prod (Tg)": d["Production_Mg"].div(1e6).round(1),
                        "Grain yld (Mg/ha/y)": d["Yield_Mg_per_ha"],
                        "Shoot DM (Tg)": d["Shoot_DM_Mg"].div(1e6).round(1),
                        "Shoot N (Tg)": d["Shoot_N_MgN"].div(1e6),
                        "Total crop N (Tg)": d["Total_crop_N_MgN"].div(1e6),
                        "Crop N fixed (Tg)": d["Crop_N_fixed_MgN"].div(1e6).round(1),
                    }
                ).round(2)
            )
        )
    )

    return d


#%%

fao_country_groups["Country Group"].unique()
