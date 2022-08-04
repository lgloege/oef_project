import geopandas as gpd
import numpy as np
import os
import pandas as pd
from pathlib import Path
import pickle
import pooch
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import sqlite3


def get_pooch():
    POOCH = pooch.create(
        path=pooch.os_cache("oef"),
        base_url="https://github.com/lgloege/wildfires_cell_towers/data/",
        version_dev="main",
        registry={
            "RDS-2013-0009.5_SQLITE.zip": "8525c71c09705ec5381f468923bc8fe5ae98019119906b5693235cb138a8705d",
            "cb_2021_us_county_500k.zip": "0262e163a6b2effa8e73863912814d499f6bdd07a05726960e0f4135ca62df1e",
            "states.csv": "95daea9537390411ac566425eb26821b06bce95255d7a86e9075bc2ab97ea6d2",
            "S_USA.Lndcv_FIA_CntyEst_2017_PL.gdb.zip": "6b1833ad9f0577e81d87c410302568087633e4f471e913759d3b3040837ed4b5",
            "FCC_cellular_tower_locations.csv": "dbaba811e51db7bad60b2fc280db0f5f5d84897d4c48a825a81adfe68c3403e7",
            "fire_null_county_names.pickle": "fa44b9aba33a8de57f48ffa1b609bc79fb4cf54bac773669256f9f668e04533e"
        },
        urls={
            "RDS-2013-0009.5_SQLITE.zip": "https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.5/RDS-2013-0009.5_SQLITE.zip",
            "cb_2021_us_county_500k.zip": "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_county_500k.zip",
            "states.csv": "https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.csv",
            "S_USA.Lndcv_FIA_CntyEst_2017_PL.gdb.zip": "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.Lndcv_FIA_CntyEst_2017_PL.gdb.zip",
            "FCC_cellular_tower_locations.csv": "https://opendata.arcgis.com/api/v3/datasets/0835ba2ed38f494196c14af8407454fb_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1"
        },
    )
    return POOCH
    
    
def download_datasets_to_cache():
    # load the pooch registry
    POOCH = get_pooch()
    # fetch wildfire (FOD) dataset
    POOCH.fetch("RDS-2013-0009.5_SQLITE.zip", processor=pooch.Unzip())
    # fetch county boundaries
    POOCH.fetch("cb_2021_us_county_500k.zip")
    # fetch state abbreviations
    POOCH.fetch("states.csv")
    # fetch landcover dataset
    POOCH.fetch("S_USA.Lndcv_FIA_CntyEst_2017_PL.gdb.zip")
    # fetch location of cell towers
    POOCH.fetch("FCC_cellular_tower_locations.csv")
    # fetch pickled null county for FOD dataset
    POOCH.fetch("fire_null_county_names.pickle")
    
    
def get_county_polygons():
    url = f"{pooch.os_cache('oef')}/cb_2021_us_county_500k.zip"
    county_bounds = gpd.read_file(url)

    # dataframe fo counties and plyogn (polygon)
    county_polygons = county_bounds[["NAME", "geometry"]]
    return county_polygons


def get_county_name(p, county_polygons):
    out = county_polygons[county_polygons.contains(p)].NAME
    if len(out)==1:
        #print(county_polygons[county_polygons.contains(p)].NAME)
        return (p, str(county_polygons[county_polygons.contains(p)].NAME.values[0]))
    else:
        return (p, None)

    
def get_null_fires():
    url = f"{pooch.os_cache('oef')}/RDS-2013-0009.5_SQLITE.zip.unzip/Data/FPA_FOD_20210617.sqlite"
    con = sqlite3.connect(url)
    cur = con.cursor()

    query = """
    SELECT *
    FROM Fires 
    WHERE FIPS_NAME IS NULL
    """

    fires_null = pd.read_sql_query(query, con)

    # add point column to fires dataframe
    fires_null['point'] = fires_null.apply(lambda row: Point(row["LONGITUDE"], row["LATITUDE"]), axis=1)
    cur.close()
    return fires_null


def get_fires():
    # wildfire data
    url = f"{pooch.os_cache('oef')}/RDS-2013-0009.5_SQLITE.zip.unzip/Data/FPA_FOD_20210617.sqlite"
    con = sqlite3.connect(url)
    cur = con.cursor()

    query = """
    SELECT *
    FROM Fires 
    WHERE FIPS_NAME IS NOT NULL
    """

    fires = pd.read_sql_query(query, con)

    # add point column to fires dataframe
    fires['point'] = fires.apply(lambda row: Point(row["LONGITUDE"], row["LATITUDE"]), axis=1)
    cur.close()
    return fires


def get_state_abbreviations():
    fl_states = f"{pooch.os_cache('oef')}/states.csv"
    states = pd.read_csv(fl_states)
    return states["Abbreviation"]



def get_forest_fire_data():
    # open pickled file
    data_dir = os.getcwd() + '/data'
    with open(f"{data_dir}/fire_null_county_names.pickle", "rb") as fp:   # Unpickling
        results = pickle.load(fp)

    # county names of the null fires 
    fires_null_county_names = [result[1] for result in results]

    # the fires still unable to classify county for
    fire_null_none = [result for result in results if result[1] is None]

    # put the county names in the fires_null dataframe
    fires_null = get_null_fires()
    fires_null["FIPS_NAME"] = pd.Series(fires_null_county_names).values 

    # filter, only keep the records that are not null
    filt = ~fires_null['FIPS_NAME'].isnull()
    fires_null = fires_null.loc[filt]

    # gets the fires with a FIPS_NAME 
    fires = get_fires()

    # make the full fires dataframe, merging fires and fires_null
    fires_full = pd.concat([fires, fires_null])

    # select just the useful columns
    columns = ["FIRE_SIZE", "FIRE_SIZE_CLASS", "LATITUDE","LONGITUDE", "STATE", "FIPS_NAME", "point"]
    fires_full = fires_full[columns]

    # remove "county" from the FIPS_NAME
    fires_full["FIPS_NAME"] = fires_full["FIPS_NAME"].str.replace(' County', '')

    # Make all the FIPS_NAME upper case
    fires_full["FIPS_NAME"] = fires_full["FIPS_NAME"].str.upper()

    #----------------------------------------
    # add county boundaries to the file
    #----------------------------------------

    # get the county names
    fl_county_bounds = f"{pooch.os_cache('oef')}/cb_2021_us_county_500k.zip"
    county_bounds = gpd.read_file(fl_county_bounds)

    # dataframe for counties and plyogn (polygon)
    county_name_state_geometry = county_bounds[["NAME", "STUSPS", "geometry"]]

    # change columns names so consistent across dataframe
    county_name_state_geometry = county_name_state_geometry.rename(columns={"STUSPS":"STATE", "NAME":"FIPS_NAME"})

    # make county name uppercase
    county_name_state_geometry["FIPS_NAME"] = county_name_state_geometry["FIPS_NAME"].str.upper()

    # merge county_anem_state_geomty and fires_full
    df_merged = pd.merge(fires_full, county_name_state_geometry,  
                         how='left', 
                         left_on=['STATE','FIPS_NAME'], 
                         right_on = ['STATE','FIPS_NAME'])
    
    # Only include US states (add this to process script)
    df_states = get_state_abbreviations()
    state_filt = df_merged["STATE"].isin(df_states)
    df_merged = df_merged.loc[state_filt]

    # perform statistics on dataset
    df_fires = (df_merged.groupby(['STATE','FIPS_NAME'])
                  #.agg({"FIRE_SIZE":"sum", "FIRE_SIZE":"max"})
                  .agg({"FIRE_SIZE": [np.mean, np.sum, np.max, np.min]})
                  .reset_index()
                  #.rename(columns={"X":"num_towers"})
                 )

    # rename columns
    df_fires.columns = [col[1] if bool(col[1]) else col[0] for col in df_fires.columns]

    df_fires = df_fires.rename(columns = {"FIPS_NAME":"COUNTY", 
                                      "mean":"MEAN_FIRE_AREA",
                                      "sum":"TOTAL_FIRE_AREA",
                                      "amax":"MAX_FIRE_AREA",
                                      "amin":"MIN_FIRE_AREA",})
    return df_fires


def get_forest_area_data():
    # read file
    url = f"{pooch.os_cache('oef')}/S_USA.Lndcv_FIA_CntyEst_2017_PL.gdb.zip"
    df_forest_area = gpd.read_file(url)

    # pre-process data
    columns = ['STATE_CNTY_FIPS', 'STATE_FIPS', 'CNTY_FIPS', 'STATE_NAME', 'CNTY_NAME',
           'SAMPLEDLANDWATER_ACRES', 'SAMPLEDLANDWATER_ERR',
           'FORESLAND_ACRES', 'ABOVEGRDBIOMASSTREES_SHRTTON', "TOTALCARBON_SHRTTON", 
           'SHAPE_Length', 'SHAPE_Area','geometry']
    df_forest_area = df_forest_area[columns]

    # select columns
    columns = ['STATE_CNTY_FIPS', 'STATE_NAME', 'CNTY_NAME',
               'SAMPLEDLANDWATER_ACRES', 'FORESLAND_ACRES',
               'ABOVEGRDBIOMASSTREES_SHRTTON', 'TOTALCARBON_SHRTTON', 
               'SHAPE_Length','SHAPE_Area', 'geometry']
    df_forest_area = df_forest_area[columns]

    # rename columns
    df_forest_area = df_forest_area.rename(columns={"STATE_NAME":"STATE", 
                                                    "CNTY_NAME":"COUNTY", 
                                                    "FORESLAND_ACRES":"FOREST_ACRES"})

    # drop Puerto Rico from dataset
    filt = df_forest_area.STATE != "Puerto Rico"
    df_forest_area = df_forest_area.loc[filt]

    # read states dataset
    fl_states = f"{pooch.os_cache('oef')}/states.csv"
    states = pd.read_csv(fl_states)

    # get state abbreviation
    state_abbreviation = [str(states.where(states["State"] == state).dropna()["Abbreviation"].values[0]) 
                          for state in df_forest_area["STATE"]]

    # replace full state name with abbreviation
    df_forest_area.STATE = state_abbreviation

    # make county name uppercase 
    df_forest_area.COUNTY = df_forest_area.COUNTY.str.upper()

    return df_forest_area


def get_cell_tower_data():
    # read tower data
    url = f"{pooch.os_cache('oef')}/FCC_cellular_tower_locations.csv"
    towers = pd.read_csv(url)

    # Only include US states
    df_states = get_state_abbreviations()
    state_filt = towers["LocState"].isin(df_states)
    towers = towers.loc[state_filt]

    # select columns
    columns = ['X', 'Y', 'LocCounty', 'LocState']
    towers = towers[columns]

    # filter the null and complete counties
    filt = towers.LocCounty.str.isspace()
    towers_null = towers.loc[filt]
    towers_comp = towers.loc[~filt]

    # replace missing county names 
    county_polygons = get_county_polygons()
    tower_null_counties = [get_county_name(Point(X,Y), county_polygons)[1].upper() 
                           for X,Y in zip(towers_null["X"], towers_null["Y"])]

    towers_null["LocCounty"] = tower_null_counties

    # complete towers dataset
    towers_full = pd.concat([towers_comp, towers_null])

    # count number of towers in each county
    towers_out = (towers_full.groupby(["LocCounty","LocState"])
                  .count()
                  .reset_index()[["LocCounty","LocState", "X"]]
                  .rename(columns={"X":"num_towers"})
                 )

    # rename columns
    df_towers = towers_out.rename(columns={"LocCounty":"COUNTY", "LocState":"STATE","num_towers":"N_TOWERS"})

    return df_towers


def create_complete_dataset():
    import functools
    dfs = [get_forest_fire_data(), get_cell_tower_data(), get_forest_area_data()]
    df_final = functools.reduce(lambda left, right: pd.merge(left, right, on=['STATE','COUNTY']), dfs)
    
    # reset the index
    df_final = df_final.reset_index()

    # only keep counties where forest area in acres is positive
    filt = (df_final["FOREST_ACRES"] > 0)
    df_final = df_final.loc[filt]

    return df_final
