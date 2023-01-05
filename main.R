# Estimation of
# - symbiotic fixation in grain legumes
# - nonsymbiotic fixation in some crops

library(tidyverse)
library(readr)

fao_element_area_harvested <- 5312
fao_element_production <- 5510
indata_dir <- "indata"
outdata_dir <- "outdata_r"

if (dir.exists(outdata_dir)) {
    stop("Not doing anything because outdata directory exists.")
}
dir.create(outdata_dir)

# Read some codes

fao_country_codes <- read.csv(
    paste(
        indata_dir,
        "faostat_definitions_country_group_2022-10-01.csv",
        sep = "/"
    ),
) %>%
    distinct(Country.Code) %>%
    pull(Country.Code)

fao_item_codes <-
    read.csv(paste(indata_dir, "Items_Primary_Production.csv", sep = "/")) %>%
    distinct(Item.Code) %>%
    pull(Item.Code)


# Read the FAOSTAT production data

fao_production_data <- read.csv(
    unzip(
        paste(
            indata_dir,
            "Production_Crops_Livestock_E_All_Data_(Normalized).zip",
            sep = "/"
        ),
        "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
    )
) %>%
    select(c(Area.Code, Area, Item.Code, Item, Element.Code, Year, Value))

# Extract crop production data

fao_crop_data <- fao_production_data %>%
    filter(Element.Code %in% c(fao_element_area_harvested, fao_element_production)) %>%
    filter(Area.Code %in% fao_country_codes) %>%
    filter(Item.Code %in% fao_item_codes) %>%
    pivot_wider(names_from = Element.Code, values_from = Value) %>%
    rename(
        Area.harvested.ha = as.character(fao_element_area_harvested),
        Production.Mg = as.character(fao_element_production),
    )


# Estimate grain legumes fixation

source("grainleg.R")
grainleg_fixation_all_results <- estimate_grainleg_fixation(
    fao_crop_data %>% filter(Production.Mg > 0)
)

grainleg_symbiotic_by_crop <- grainleg_fixation_all_results %>%
    arrange(Area.Code, Item.Code, Year) %>%
    rename(Main = Crop_N_fixed_symbiotic_MgN) %>%
    mutate(
        Low = Main * 0.9,
        High = Main * 1.1
    ) %>%
    select(Area.Code, Area, Item.Code, Item, Year, Low, Main, High)

# Estimate nonsymbiotic fixation

nonsymbiotic_coefficients <- read.csv(
    paste(indata_dir,
        "nonsymbiotic-fixation-coefficients-kg-per-ha-harvest.csv",
        sep = "/"
    )
) %>%
    filter(!is.na(Main)) %>%
    select(Item.Code, Low, Main, High) %>%
    rename(Low_coeff = Low, Main_coeff = Main, High_coeff = High)

kg_to_Mg <- 1e-3

nonsymbiotic_by_crop <- fao_crop_data %>%
    filter(!is.na(Area.harvested.ha)) %>%
    arrange(Area.Code, Item.Code, Year) %>%
    inner_join(nonsymbiotic_coefficients) %>%
    mutate(
        Low = Area.harvested.ha * Low_coeff * kg_to_Mg,
        Main = Area.harvested.ha * Main_coeff * kg_to_Mg,
        High = Area.harvested.ha * High_coeff * kg_to_Mg,
    ) %>%
    select(Area.Code, Area, Item.Code, Item, Year, Low, Main, High)


# Calculate total fixation by country

tr_area_code_m49 <- read.csv(
    paste(
        indata_dir,
        "faostat_definitions_country_region_2022-10-01.csv",
        sep = "/"
    )
) %>%
    select(Country.Code, M49.Code)

fixation_total <- (nonsymbiotic_by_crop %>% mutate(Src = "nonsymbiotic")) %>%
    full_join(grainleg_symbiotic_by_crop %>% mutate(Src = "grainleg_symbiotic")) %>%
    replace(is.na(.), 0) %>%
    group_by(Area.Code, Year) %>%
    summarise(Low = sum(Low), Main = sum(Main), High = sum(High)) %>%
    left_join(tr_area_code_m49, by = c("Area.Code" = "Country.Code"))


# Write result files

write.csv(
    nonsymbiotic_by_crop,
    paste(outdata_dir, "nonsymbiotic-fixation-MgN.csv", sep = "/"),
    row.names = FALSE
)

write.csv(
    grainleg_symbiotic_by_crop,
    paste(outdata_dir, "grain-legumes-symbiotic-fixation-MgN.csv", sep = "/"),
    row.names = FALSE
)

write.csv(
    fixation_total,
    paste(outdata_dir, "total-fixation-country-MgN.csv", sep = "/"),
    row.names = FALSE
)
