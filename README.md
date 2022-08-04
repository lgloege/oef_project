# OEF Take Home Project

Forest fires are common hazard, particularly in remote or unmanaged areas. Real time detection is possible 
with CO2 and temperature IoT sensors. This project aims to identify counties that would benefit such network. 
In this project, I use would look at the feasibility of this approach by analyzing forest cover and broadband internet access at the county level in the US.


## Datasets
- [FIA Landcover County Estimates 2017](https://data.fs.usda.gov/geodata/edw/datasets.php?dsetCategory=boundaries): This feature class represents forest area estimates by county for the year 2017. The data was generated from the Forest Inventory Analysis (FIA) using the [EVALIDator web tool](http://apps.fs.fed.us/Evalidator/evalidator.jsp). The areas were calculated within county limits using the US Census Bureau's county spatial data. 
- [Fire Program Analysis Fire-Occurrence Database (5th Edition)](https://www.fs.usda.gov/rds/archive/Catalog/RDS-2013-0009.5): The Fire Program Analysis fire-occurrence database (FPA FOD) includes 2.17 million geo-referenced wildfire records, representing a total of 165 million acres burned during the 27-year period. This is a spatial database of wildfires that occurred in the United States from 1992 to 2018. The wildfire records were acquired from the reporting systems of federal, state, and local fire organizations.
- [Cellular tower locations](https://hifld-geoplatform.opendata.arcgis.com/datasets/cellular-towers/explore?location=42.460834%2C-100.076156%2C4.69): This dataset represents cellular tower locations as recorded by the Federal Communications Commission (FCC). It is known that there are some errors in the licensing information - Latitude, Longitude and Ground Elevation data as well as frequency assignment data from which these MapInfo files were generated.
- [US Census Bureau's county spatial data](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html): The cartographic boundary files are simplified representations of selected geographic areas from the Census Bureau’s MAF/TIGER geographic database.
- [US State Abbreviations](https://github.com/jasonong/List-of-US-States): dataset with US state name and two letter abbreviation. 

## Download datasets

The following function downloads datasets to `{cache}/oef/`, where `{cache}` is your systems local cache directory.
```python
from utils import download_datasets_to_cache
download_datasets_to_cache()
```

## Next Steps
- Focus on specific forests and identify regions that have and don't have 4G/5G converage
- [FCC 4G LTE Coverage Map](https://fcc.maps.arcgis.com/apps/webappviewer/index.html?id=6c1b2e73d9d749cdb7bc88a0d1bdd25b) provides maps of 4G LTE mobile broadband coverage across the US for various carriers. 
- USDA provides estimates of [forest boundaries](https://data.fs.usda.gov/geodata/edw/datasets.php?dsetCategory=boundaries)
- satellite retrievals can also be used to estimate forested regions.
- Instead of LTE, may satellite internet is an option. Would need to find a dataset of satellite internet coverage and availabilty. 
  

