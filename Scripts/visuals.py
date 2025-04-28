## calculating emissions factors for maritime shipping

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import pycountry
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from haversine import haversine, Unit

def get_iso3(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except LookupError:
        return None  # Return None if country name is not found

def clean(df, hts_num):
    phrases = ["Total", "EUROPEAN UNION", "PACIFIC RIM COUNTRIES", "CAFTA-DR", "NAFTA", "TWENTY LATIN AMERICAN REPUBLICS", "OECD", "NATO", "LAFTA", "EURO AREA", "APEC", "ASEAN", "CACM",
           "NORTH AMERICA", "CENTRAL AMERICA", "SOUTH AMERICA", "EUROPE", "ASIA", "AFRICA", "OCEANIA", "MIDDLE EAST", "CARIBBEAN", "LOW VALUE", "MAIL SHIPMENTS"]
    df = df[~df.apply(lambda row: row.astype(str).str.contains("|".join(phrases), case=False, na=False).any(), axis=1)]
    df = df.replace({
        'CHICAGO MIDWAY INT?L AIRPORT, IL': 'CHICAGO MIDWAY INTERNATIONAL AIRPORT, IL',
        'RUSSIA': 'RUSSIAN FEDERATION',
        'MACEDONIA': 'NORTH MACEDONIA',
        'MACAU': 'MACAO',
        'BURMA': 'MYANMAR',
        'REUNION': 'RÉUNION',
        'ST LUCIA': 'SAINT LUCIA',
        'ST KITTS AND NEVIS': 'SAINT KITTS AND NEVIS',
        'ST VINCENT AND THE GRENADINES': 'SAINT VINCENT AND THE GRENADINES',
        'SINT MAARTEN': 'SINT MAARTEN (DUTCH PART)',
        'CURACAO': 'CURAÇAO',
        'CONGO (KINSHASA)': 'CONGO, DEMOCRATIC REPUBLIC OF THE',
        'CONGO (BRAZZAVILLE)': 'CONGO',
        'BRUNEI': 'BRUNEI DARUSSALAM',
        "COTE D'IVOIRE": "CÔTE D'IVOIRE",
        'KOREA, SOUTH': 'KOREA, REPUBLIC OF',
        'TURKEY': 'Türkiye',
        'FALKLAND ISLANDS (ISLAS MALVINAS)': 'FALKLAND ISLANDS (MALVINAS)',
        'BRITISH INDIAN OCEAN TERRITORIES': 'BRITISH INDIAN OCEAN TERRITORY',
        'HEARD AND MCDONALD ISLANDS': 'HEARD ISLAND AND MCDONALD ISLANDS',
        'MICRONESIA': 'MICRONESIA, FEDERATED STATES OF',
        'WEST BANK ADMINISTERED BY ISRAEL': 'ISRAEL'
    })
    df["CTY_ISO3"] = df["CTY_NAME"].apply(get_iso3)
    port_coords = pd.read_csv("/Users/aidangoldenberg-hart/Documents/MIT/Research/Maritime and Aviation/CensusAPI/Port_Coords.csv")
    df = df.merge(port_coords, on="PORT_NAME", how="left")

    #need to fix this so it works for ex and imports
    ######also lowkey maybe need to do containerized and plain vessel... still no real documentation on that
    df.to_csv("Import_Data/exports_2024_"+str(hts_num)+".csv", index=False)
    return df

test = 0
path_ne = "Maps/ne_50m_admin_0_countries.shp"