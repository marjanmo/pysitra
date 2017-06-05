from __future__ import print_function
import os
import csv
import warnings
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point


HOMEDIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))


def cheesy_slovenian_epsg_checker(shp):

    #Very silly checker for epsg

    prj_file = os.path.splitext(os.path.abspath(shp))[0] + ".prj"

    with open(prj_file, "r") as f:
        prj_txt = f.read().lower()


    d48_keywords  = ["bessel", "1841", "MGI"]
    d96_keywords  = ["1996","GRS_1980"]

    if not "slove" in prj_txt:
        return None

    for keyword in d48_keywords:
        if keyword in prj_txt:
            return 3912

    for keyword in d96_keywords:
        if keyword in prj_txt:
            return 3794

    else:
        return None

def save_to_shapefile_with_prj(geo_df, file_out, epsg, encoding="utf-8"):
    prj_file = os.path.splitext(os.path.abspath(file_out))[0] + ".prj"

    prj_dict = {
        3912: 'PROJCS["MGI / Slovene National Grid",GEOGCS["MGI",DATUM["D_MGI",SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",500000],PARAMETER["false_northing",-5000000],UNIT["Meter",1]]',
        3794: 'PROJCS["Slovenia 1996 / Slovene National Grid",GEOGCS["Slovenia 1996",DATUM["D_Slovenia_Geodetic_Datum_1996",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",500000],PARAMETER["false_northing",-5000000],UNIT["Meter",1]]',
        4326: 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]',
        3857: 'PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["Popular Visualisation CRS",DATUM["D_Popular_Visualisation_Datum",SPHEROID["Popular_Visualisation_Sphere",6378137,0]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Mercator"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]',
        31258: 'PROJCS["MGI_Austria_GK_M31",GEOGCS["GCS_MGI",DATUM["D_MGI",SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",450000.0],PARAMETER["False_Northing",-5000000.0],PARAMETER["Central_Meridian",13.33333333333333],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'}

    if epsg not in prj_dict.keys():
        raise Exception("EPSG {} is not in the epsg:wkt_prj dictionary. Add it!".format(epsg))

    with open(prj_file, "w") as f:
        f.write(prj_dict[epsg])

    # save file
    geo_df.to_file(filename=file_out, crs_wkt=prj_dict[epsg], encoding=encoding)

def closest_element_to_given_points(points, shapefile):
    # ce je shapefile argument kot string, potem gre za fajl, ki ga preberi
    if isinstance(shapefile, str):
        shapefile = gpd.read_file(shapefile)

    results = []

    for point in points:

        # je gre za prazno tocko, vrni None
        if not isinstance(point, Point) and (not point[0] or not point[1]):
            results.append(np.NaN)
            continue

        p = Point(point) if not isinstance(point, Point) else point

        distance = 10000000000000
        nearest_object = None

        for i in shapefile.index.tolist():

            ref_object = shapefile.ix[i, "geometry"]

            # ce gre za prazen objekt, vrni None
            if ref_object.is_empty:
                results.append(np.NaN)
                continue

            trenutna_razdalja = p.distance(ref_object)

            if trenutna_razdalja < distance:
                distance = trenutna_razdalja
                nearest_object = i

        results.append(nearest_object)

    return results

def recognize_csv_separator(csv_file):

    # https://stackoverflow.com/questions/3952132/how-do-you-dynamically-identify-unknown-delimiters-in-a-data-file

    with open(csv_file) as f:
            line = f.readline()

    return csv.Sniffer().sniff(line).delimiter

def check_for_csv_header(csv_file):

    with open(csv_file) as f:
            line = f.readline()

    #return direct value for read_csv input argument header
    if any(c.isalpha() for c in set(line)):
        return 0
    else:
        return None

def convert_to_numeric(df):
    for i in df.columns:
        df[i] = pd.to_numeric(df[i], errors="ignore")

    return df

def recognize_xyz_fields(df):

    xyz_candidates = ["e","x","easting","east","vzhod","n","y","northing","north","sever","h","z"]
    x_range = [350000,650000]
    y_range = [10000,300000]
    z_range = [0,10000]

    x,y,z =  None,None,None

    df = convert_to_numeric(df)
    df = df._get_numeric_data() #https://stackoverflow.com/questions/19900202/how-to-determine-whether-a-column-variable-is-numeric-or-not-in-pandas-numpy

    # Check if there are no reasonable column names
    if len(set([str(i).lower() for i in df.columns]).intersection(set(xyz_candidates))) == 0:
        warnings.warn("The dataset specified doesn't seem to have any meaningful column names specifed (e.g: x,y,e,n,easting,...)\n"
                      "Program will try to autodetect x,y and z columns by accepting the first column with appropriate "
                      "value range, starting from the last column...")

        for col in reversed(df.columns):
                mean = df[col].mean()
                if x_range[0] < mean < x_range[-1]:
                    x = col
                elif y_range[0] < mean < y_range[-1]:
                    y = col
                elif z_range[0] < mean < z_range[-1]:
                    z = col
    else:
        for col in reversed(df.columns):
            if col.lower() in xyz_candidates:
                mean = df[col].mean()
                if x_range[0] < mean < x_range[-1]:
                    x = col
                if y_range[0] < mean < y_range[-1]:
                    y = col
                if z_range[0] < mean < y_range[-1]:
                    z = col

    if x == None:
        raise IOError("Couldn't figure out which field represents easting coordinate (tried matching names and guesing by size range.)")

    if y == None:
        raise IOError("Couldn't figure out which field represents northing coordinate (tried matching names and guesing by size range.)")

    if z == None:
        warnings.warn("The specified dataset doesn't seem to have a height attribute specified (h or z field)!")

    return x,y,z

