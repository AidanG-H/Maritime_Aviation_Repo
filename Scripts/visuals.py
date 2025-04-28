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

def clean(hts_num):
    df = pd.read_csv("Export_Data/exports_2024_"+str(hts_num)+".csv", header=1, usecols=[1,2,3,4,5,6,8])
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
    df.to_csv("Export_Data/exports_2024_"+str(hts_num)+".csv", index=False)
    return df



def exp_plot(df, hts_name, vessel_type, fuel_type):
    
    path_ne = "~Maps/ne_50m_admin_0_countries.shp"

    # Merge data with world dataset to get destination coordinates
    world = gpd.read_file(path_ne)
    world = world[["ISO_A3", "geometry"]]  # Keep only ISO3 and geometry
    df = df.merge(world, left_on="CTY_ISO3", right_on="ISO_A3", how="left")

    # Extract destination centroids
    df["geometry"] = df["geometry"].apply(lambda geom: geom.centroid if geom else None)  # Ensure valid centroids
    df["dest_lon"] = df["geometry"].apply(lambda geom: geom.x if geom else None)
    df["dest_lat"] = df["geometry"].apply(lambda geom: geom.y if geom else None)


    def calc_distance(row):
        port_coords = (row["PORT_LAT"], row["PORT_LON"])
        dest_coords = (row["dest_lat"], row["dest_lon"])
        return haversine(port_coords, dest_coords, unit=Unit.KILOMETERS)

    # Apply it to each row and save in new column
    df["haversine_distance_km"] = df.apply(calc_distance, axis=1)

    # Emissions factor calculation
    GREET_factor = 92   #gCO2/MJ (cell G53 in GREET marine_WTH sheet)

    if fuel_type == "lsfo":
        fuel_type = 0
    elif fuel_type == "liquid hydrogen":
        fuel_type = 1
    elif fuel_type == "ammonia":
        fuel_type = 2
    elif fuel_type == "methanol":
        fuel_type = 3
    elif fuel_type == "FT diesel":
        fuel_type = 4
    else:
        raise ValueError("Invalid fuel type. Choose from 'lsfo', 'liquid hydrogen', 'ammonia', 'methanol', or 'FT diesel'.")

    GJtnm = pd.read_csv('fuel_energy_info/fuel_GJ_per_tonne_nautical_mile_max_cap.csv')    #assuming max capacity for now
    if vessel_type == "Bulk Carrier":
        GJtnm = GJtnm.iloc[fuel_type,4]
    elif vessel_type == "Container Ship":
        GJtnm = GJtnm.iloc[fuel_type,9]
    elif vessel_type == "Tanker":
        GJtnm = GJtnm.iloc[fuel_type,16]
    else:
        raise ValueError("Invalid vessel type. Choose from 'Bulk Carrier', 'Container Ship', or 'Tanker'.")
    
    #multiply by 1000 to convert from GJ to MJ
    GJtnm = GJtnm * 1000  # MJ/tonne-nautical-mile

    # nm to km conversion
    conv = 1/1.852
    GJtnm = GJtnm * conv  # MJ/tonne-km

    em_factor = GREET_factor * GJtnm # gCO2/tonne-km

    #make a new column for the emissions intensity of each lane
    df['gCO2eq_total'] = em_factor*df['haversine_distance_km']*df["CNT_WGT_YR"]
    

    #only plot top 20 lanes
    df_top = df.sort_values(by="gCO2eq_total", ascending=False).head(20)

    #display to get a sense of the highest emissions lanes
    print(df_top[["PORT_NAME", "CTY_NAME", "gCO2eq_total"]])


    # Plot the map
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=-100))
    world.plot(ax=ax, transform=ccrs.PlateCarree(), color="lightgray")

    def add_arrow(ax, lon1, lat1, lon2, lat2, weight):
        # Convert lon/lat to display coordinates
        proj = ccrs.Geodetic()
        x1, y1 = ax.projection.transform_point(lon1, lat1, proj)
        x2, y2 = ax.projection.transform_point(lon2, lat2, proj)

        # Create arrow patch
        arrow = FancyArrowPatch(
            (x1, y1), (x2, y2),
            transform=ax.transData,
            arrowstyle='->',
            color='blue',
            linewidth= weight / 2e11,  
            alpha=0.8,
            mutation_scale=10
        )
        ax.add_patch(arrow)

    # Plot all trade flow arrows
    for _, row in df_top.iterrows():
        if pd.notna(row["PORT_LON"]) and pd.notna(row["PORT_LAT"]) and pd.notna(row["dest_lon"]) and pd.notna(row["dest_lat"]):
            add_arrow(ax, row["PORT_LON"], row["PORT_LAT"], row["dest_lon"], row["dest_lat"], row['gCO2eq_total'])


    # Title and display
    plt.title("Top 20 Marine Export Flows of " +hts_name+  " by g CO2 equivalent emissions")
    plt.savefig("draft_airplane_export_flow_"+hts_name+".png")
    

clean(29)