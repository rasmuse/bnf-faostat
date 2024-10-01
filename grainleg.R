library(tidyverse)

# Estimation of fixation in grain legumes from FAOSTAT crop production data.
# Following Peoples et al. (2021) and Herridge et al. (2022)

indata_dir <- "indata"

# Enforce min and max harvest index (not part of the original model)

MIN_HI <- 0.1
MAX_HI <- 0.5

# Mapping of crop names from Herridge et al. (2022) to FAOSTAT item codes

tr_crops_fao_to_herridge <- read.csv(paste(
    indata_dir,
    "crop-names-herridge.csv",
    sep = "/"
)) %>%
    filter(Crop.Herridge.et.al. != "") %>%
    select(Item.Code, Crop.Herridge.et.al.)

# Herridge et al. (2022) distinguish Europe and Brazil from the rest
# of the world (ROW). Here, mapping FAOSTAT country codes to these groups based
# on FAOSTAT nomenclature of what's included in "Europe".

fao_countries <- read.csv(paste(
    indata_dir,
    "faostat_definitions_country_region_2022-10-01.csv",
    sep = "/"
))

fao_country_groups <- read.csv(paste(
    indata_dir,
    "faostat_definitions_country_group_2022-10-01.csv",
    sep = "/"
))

europe_country_codes <- fao_country_groups %>%
    filter(Country.Group == "Europe" | Country == "Europe") %>%
    pull(Country.Code)


brazil_code <- fao_countries %>%
    filter(Country == "Brazil") %>%
    pull(Country.Code)

regions_except_row <- tibble(Country.Code = europe_country_codes, Region = "Europe") %>%
    full_join(tibble(Country.Code = brazil_code, Region = "Brazil"))

regions <- tibble(Country.Code = fao_countries$Country.Code, Region = "ROW") %>%
    filter(!Country.Code %in% regions_except_row$Country.Code) %>%
    full_join(regions_except_row)


# Implement the model closely following Herridge et al. (2022)

# estimate_fixation <- function(fao_crop_data) {
# }


build_crop_regression_params <- function(special_crops, special_k, special_m, default_k, default_m) {
    km_special <- tibble(
        Crop.Herridge.et.al. = special_crops,
        k = special_k,
        m = special_m,
    )
    all_crops <- unique(tr_crops_fao_to_herridge$Crop.Herridge.et.al.)
    tibble(
        Crop.Herridge.et.al. = all_crops,
        k = default_k,
        m = default_m
    ) %>%
        filter(!Crop.Herridge.et.al. %in% km_special$Crop.Herridge.et.al.) %>%
        full_join(km_special)
}

apply_crop_regression <- function(d, x_name, regression_params) {
    param_values <- d %>%
        select(Crop.Herridge.et.al.) %>%
        left_join(regression_params)
    d[[x_name]] * param_values$k + param_values$m
}

HI_params <- build_crop_regression_params(
    c("Soybean", "Groundnut", "Pigeonpea"),
    c(0.1178, 0.1343, 0.0517),
    c(0.2775, 0.2614, 0.1647),
    0.0804,
    0.2839
)

N_conc_params <- build_crop_regression_params(
    c("Soybean", "Groundnut", "Chickpea", "Pigeonpea", "Lupin"),
    c(-0.118, 0.0, 0.0, 0.0, 0.0) / 100,
    c(3.913, 2.7, 1.9, 1.9, 2.7) / 100,
    0.0 / 100,
    2.5 / 100
)

BG_N_params <- build_crop_regression_params(
    c("Chickpea", "Pigeonpea"),
    c(2, 2),
    c(0, 0),
    1.4,
    0.0
)

except <- function(candidates, exclusions) {
    candidates[!candidates %in% exclusions]
}

Ndfa <- {
    Ndfa_specials <- c(
        "Soybean" = 61,
        "Common bean" = 38,
        "Pigeonpea" = 74,
        "Faba bean" = 74,
        "Lupin" = 74
    )
    Ndfa_default_value <- 62
    Ndfa_defaults <- tibble(
        Region = "ROW",
        Crop.Herridge.et.al. = names(Ndfa_specials),
        Ndfa = Ndfa_specials,
    ) %>% full_join(
        tibble(
            Region = "ROW",
            Crop.Herridge.et.al. = except(unique(tr_crops_fao_to_herridge$Crop.Herridge.et.al.), names(Ndfa_specials)),
            Ndfa = Ndfa_default_value
        )
    )
    special_soybean_Ndfa <- list(
        list(Region = "Europe", Ndfa = 44),
        list(Region = "Brazil", Ndfa = 78)
    )
    Ndfa <- Ndfa_defaults
    for (item in special_soybean_Ndfa) {
        new <- Ndfa_defaults %>%
            mutate(
                Region = item[["Region"]],
                Ndfa = replace(Ndfa, Crop.Herridge.et.al. == "Soybean", item[["Ndfa"]])
            )
        Ndfa <- Ndfa %>% full_join(new)
    }
    Ndfa <- Ndfa %>% mutate(Ndfa=Ndfa / 100)
    Ndfa
}

estimate_grainleg_fixation <- function(fao_crop_data) {
    fao_crop_data %>%
        inner_join(tr_crops_fao_to_herridge) %>%
        inner_join(regions, c("Area.Code" = "Country.Code")) %>%
        mutate(Yield.Mg.per.ha = Production.Mg / Area.harvested.ha) %>%
        mutate(Log_yield_Mg_per_ha = log(Yield.Mg.per.ha)) %>%
        mutate(HI = apply_crop_regression(., "Log_yield_Mg_per_ha", HI_params)) %>%
        mutate(HI = pmax(HI, MIN_HI)) %>%
        mutate(HI = pmin(HI, MAX_HI)) %>%
        mutate(Shoot_DM_Mg = Production.Mg / HI) %>%
        mutate(Shoot_DM_yield_Mg_per_ha = Shoot_DM_Mg / Area.harvested.ha) %>%
        mutate(Shoot_N_concentration = apply_crop_regression(., "Shoot_DM_yield_Mg_per_ha", N_conc_params)) %>%
        mutate(Shoot_N_MgN = Shoot_N_concentration * Shoot_DM_Mg) %>%
        mutate(Total_crop_N_MgN = apply_crop_regression(., "Shoot_N_MgN", BG_N_params)) %>%
        left_join(Ndfa) %>%
        mutate(Crop_N_fixed_symbiotic_MgN = Total_crop_N_MgN * Ndfa)
}
