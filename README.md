# Estimation of biological nitrogen fixation in cropland

- Symbiotic fixation in grain legumes following Peoples et al. (2021) and Herridge et al. (2022).
- Non-symbiotic fixation in other crops based on Smil (1999), Herridge et al. (2008), Ladha et al. (2016), and Ladha et al. (2022).
- No fixation estimate for vegetable legumes (string beans, etc).
- No fixation estimate for forage legumes due to lack of data on areas and harvests.

## References

- Herridge, D. F., Giller, K. E., Jensen, E. S., & Peoples, M. B. (2022). Quantifying country-to-global scale nitrogen fixation for grain legumes II. Coefficients, templates and estimates for soybean, groundnut and pulses. Plant and Soil. https://doi.org/10.1007/s11104-021-05166-7
- Herridge, D. F., Peoples, M. B., & Boddey, R. M. (2008). Global inputs of biological nitrogen fixation in agricultural systems. Plant and Soil, 311(1–2), 1–18. https://doi.org/10.1007/s11104-008-9668-3
- Ladha, J. K., Tirol-Padre, A., Reddy, C. K., Cassman, K. G., Verma, S., Powlson, D. S., van Kessel, C., de B. Richter, D., Chakraborty, D., & Pathak, H. (2016). Global nitrogen budgets in cereals: A 50-year assessment for maize, rice and wheat production systems. Scientific Reports, 6(1), 19355. https://doi.org/10.1038/srep19355
- Ladha, J. K., Peoples, M. B., Reddy, P. M., Biswas, J. C., Bennett, A., Jat, M. L., & Krupnik, T. J. (2022). Biological nitrogen fixation and prospects for ecological intensification in cereal-based cropping systems. Field Crops Research, 283, 108541. https://doi.org/10.1016/j.fcr.2022.108541
- Peoples, M. B., Giller, K. E., Jensen, E. S., & Herridge, D. F. (2021). Quantifying country-to-global scale nitrogen fixation for grain legumes: I. Reliance on nitrogen fixation of soybean, groundnut and pulses. Plant and Soil, 469(1), 1–14. https://doi.org/10.1007/s11104-021-05167-6
- Smil, V. (1999). Nitrogen in crop production: An account of global flows. Global Biogeochemical Cycles, 13(2), 647–662. https://doi.org/10.1029/1999GB900015

# Installing and running it

## Python setup

Developed using Python 3.9.6; should also work with newer versions.

Dependencies are listed in `requirements.txt`.

Strongly recommend to use a virtual environment as follows.

On a Linux system:

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Not tested on Windows, but should work like this:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running it

Run the main script:

```
python main.py
```

This will put results in directory `outdata`.

If `outdata` exists, will do nothing; to re-run, remove `outdata`.


## Updating the input data

All the necessary indata are available in `indata`. The FAOSTAT input data can be exchanged for newer data by downloading a newer FAOSTAT Crop & Livestock production data (dataset code `QCL`) in the `indata` directory under the name `indata/Production_Crops_Livestock_E_All_Data_(Normalized).zip`.

This file is available from the FAOSTAT bulk downloads facility; see `https://fenixservices.fao.org/faostat/static/bulkdownloads/datasets_E.json`.

At the time of writing, the dataset is found at url
```
https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data_(Normalized).zip
```
so it can be downloaded, e.g., as follows
```
cd indata && curl -OL https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data_\(Normalized\).zip
```

At the time of writing this (2022-10-01), the latest version has `DateUpdate 2022-02-16T00:00:00` and the zip file has md5sum as follows:

```
$ md5sum indata/Production_Crops_Livestock_E_All_Data_\(Normalized\).zip
9653e3270fc001bbc71ec68fe9b8e94d  indata/Production_Crops_Livestock_E_All_Data_(Normalized).zip
```
