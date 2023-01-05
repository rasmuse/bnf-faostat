clean:
	rm -rf outdata_python outdata_r

outdata_r:
	Rscript main.R

output_python:
	python main.py

cropland_bnf.zip: clean outdata_r output_python README.md
	zip -r cropland_bnf.zip indata outdata_r outdata_python README.md
