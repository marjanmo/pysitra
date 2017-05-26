import os
from datetime import datetime
#
# from fiona.crs import to_string
# from urllib import urlencode
# from urllib2 import urlopen
# import json


import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiLineString
from scipy import spatial
import numpy as np

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


def pts_triangle_transformation(points, df_parameters, KDTree_object=None):
    """
    Function,

    https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
    :param points:
    :param df_reference_points:
    :return:
    """

    # Dovoli izracunat sele kasenje - optimization purposes
    if not KDTree_object:
        reference_points = np.array([(p.x, p.y) for p in df_parameters["geometry"].values.tolist()])

        # create a KDTre object from a reference points
        KDTree_object = spatial.KDTree(reference_points)

    TRANS_PARAMETERS = "a b c d e f"

    new_points = []

    if not isinstance(points, list):
        points = [points]

    if isinstance(points[0], Point):
        points = [(p.x, p.y) for p in points]

    for point in points:
        now = datetime.now()
        index_of_closest = KDTree_object.query(point)[1]
        # print (datetime.now() - now).total_seconds()
        [a, b, c, d, e, f] = df_parameters.reset_index().ix[
            index_of_closest, TRANS_PARAMETERS.split(" ")].values.tolist()
        # https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array

        # calculate new points
        x_new = a * point[0] + b * point[1] + c
        y_new = d * point[0] + e * point[1] + f

        new_points.append(Point(x_new, y_new))

    if len(new_points) == 1:
        return new_points[0]

    return new_points

def shp_triangular_transformation(df_in, from_crs="d96"):
    start = datetime.now()

    """
    Function for transformation from d96 to d48 and vice versa with the triangular transformation
    :param df_in:
    :param from_crs:
    :return:
    """
    from_crs = from_crs.lower()

    if from_crs not in ["d96", "d48"]:
        raise IOError("From_crs argument can only be d96 or d48!")

    # read the correct (d96 or d48) file with transformation parameters for given direction
    param_shp = os.path.join(HOMEDIR, "pysitra","static", "triangle_parameters_from_{}_points.shp".format(from_crs))
    df_parameters = gpd.read_file(param_shp)

    reference_points = np.array([(p.x, p.y) for p in df_parameters["geometry"].values.tolist()])

    # create a KDTre object from a reference points
    KDTree_object = spatial.KDTree(reference_points)

    st_tock = 0

    if df_in.ix[0, "geometry"].type == "Point":
        pts = df_in["geometry"].values.tolist()
        st_tock += len(pts)

        # poracunaj nove tocke
        pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
                                                     df_parameters=df_parameters)
        df_in["geometry"] = pts_out

    else:
        # change the geometry by applying transformation formula t0 each vertex:
        for i in df_in.index:
            geom = df_in.loc[i, "geometry"]

            if geom.type == "LineString":
                pts = geom.coords[:]
                st_tock += len(pts)

                # poracunaj nove tocke
                pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
                                                             df_parameters=df_parameters)
                df_in.loc[i, "geometry"] = LineString(pts_out)

            elif geom.type == "MultiLineString":
                lines = []
                for line in geom.geoms[:]:
                    pts = line.coords[:]
                    st_tock += len(pts)

                    # poracunaj nove tocke
                    pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
                                                                 df_parameters=df_parameters)
                    lines.append(LineString(pts_out))

                df_in.loc[i, "geometry"] = MultiLineString(lines)

            elif geom.type == "Polygon":

                pts = geom.exterior.coords[:]
                st_tock += len(pts)

                # poracunaj nove tocke
                pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
                                                             df_parameters=df_parameters)
                df_in.loc[i, "geometry"] = Polygon(pts_out)
            else:
                raise NotImplementedError(
                    "Found a geometry type {}! Function is implemented only for Point, LineString, "
                    "MultiLineStrings and Polygons.".format(
                        geom.type))

    total_seconds = (datetime.now() - start).total_seconds()
    tock_na_minuto = float(st_tock) * 60 / total_seconds
    print "Successully transfromed {} points in {:.2f} seconds with a speed of {:.2f} points/min).".format(st_tock, total_seconds,
                                                                                 tock_na_minuto)

    return df_in

