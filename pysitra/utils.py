import os
from datetime import datetime
import math
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


def trans_2R_6params(x,y,params=()):
    #parameters in order a,b,c,d,e,f

    [a, b, c, d, e, f] = params

    # calculate new points
    x_new = a * x + b * y + c
    y_new = d * y + e * y + f

    return x_new,y_new

def trans_3R_7params(x,y,z,params=()):
    # parameters in order cx,cy,cz,s,rx,ry,rz (https://en.wikipedia.org/wiki/Helmert_transformation)
    [cx,cy,cz,s,rx,ry,rz] = params

    sec_to_rad = 4.8481e-6
    rx = rx*sec_to_rad
    ry = ry*sec_to_rad
    rz = rz*sec_to_rad


    x_new = cx + (1+s*10e-6)*(x - rz*y + ry*z)
    print x_new
    y_new = cy + (1+s*10e-6)*(rz*x + y - rx*z)
    z_new = cz + (1+s*10e-6)*(-ry*x + rx*y + z)

    import numpy as np
    mx = np.array([x,y,z])
    mc = np.array([cx,cy,cz])
    mr = np.array([[1,-rz,ry],[rz,1,-rx],[-ry,rx,1]])

    a = mc + (1+s*0.000001)*np.dot(mr,mx)
    print a
    x_new, y_new, z_new = a
    return x_new,y_new,z_new


def trans_2R_4params(x,y,params):
    C, D, A, B = params

    if D -180 > 0: #Find angles almost 360 deg, because in file it should be negative angle instead of almost 360!
        D = D - 360

    D = D * 2 * math.pi / 360

    x_new = A + C * x - D * y
    y_new = B + D * x + C * y

    return x_new, y_new


class SlovenianTransformations:

    methods = ["triangle", "1region", "3regions", "7regions", "24regions"]

    def __init__(self,from_crs, method="triangle"):

        if method not in self.methods:
            raise IOError("Type can only be on of {}!".format(",".join(self.methods)))

        if from_crs not in ["d96", "d48"]:
            raise IOError("From_crs argument can only be d96 or d48!")

        self.method = method
        self.from_crs = from_crs

        self.shpfile = os.path.join(HOMEDIR, "pysitra","static", "{}_parameters_from_{}.shp".format(self.method, self.from_crs))

        #Prepare spatial data for faster execution of transform function! (Reading shapefiles and preparing special objects
        if self.method != "1region":
            # 1region doesnt have shapefile, parameters are hardcoded!
            self.df_parameters = gpd.read_file(self.shpfile)

        if self.method == "triangle":
            self.reference_points = np.array([(p.x, p.y) for p in self.df_parameters["geometry"].values.tolist()])

            # create a KDTre object from a reference points
            self.KDTree_object = spatial.KDTree(self.reference_points)


    def transform(self,points):

        # INPUT ERROR CHECK:
        if not isinstance(points, list):
            points = [points]

        if isinstance(points[0], Point):
            points = [(p.x, p.y) for p in points]

        new_points = []

        # AFFINE TRIANGLE 2R 6PARAMETRIC
        if self.method == "triangle":

            for point in points:
                index_of_closest = self.KDTree_object.query(point)[1]
                params = self.df_parameters.reset_index().ix[
                    index_of_closest, "a b c d e f".split(" ")].values.tolist()
                # https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array

                x_new, y_new = trans_2R_6params(point[0], point[1], params)

                new_points.append(Point(x_new, y_new))

        # HELMERT 3R 7 PARAMETRIC
        elif self.method in ["1region", "3regions", "7regions"]:

            # doloci parametre
            if self.method == "1region":
                if self.from_crs == "d48":
                    # from d48 to d96
                    params = [409.545, 72.164, 486.872, 17.919665, -3.085957, -5.469110, 11.020289]
                else:
                    # from d96 to d48
                    params = [-409.520, -72.192, -486.872, -17.919456, 3.086250, 5.468945, -11.020370]
            else:
                closest_polygons = closest_element_to_given_points(points, self.df_parameters)

            for i, point in enumerate(points):
                if self.method == "1region":
                    x_new, y_new, _ = trans_3R_7params(point[0], point[1], 0, params=params)
                else:
                    params = self.df_parameters.ix[closest_polygons[i], "cx cy cz s rx ry rz".split(" ")]  # daj ven "id field"
                    #TODO:Impletement 3D points!
                    x_new, y_new, _ = trans_3R_7params(point[0], point[1], 0, params=params)

                new_points.append(Point(x_new, y_new))

        #AFFINE 2R 4parametric
        elif self.method == "24regions":
            closest_polygons = closest_element_to_given_points(points, self.df_parameters)

            for i, point in enumerate(points):
                params = self.df_parameters.ix[closest_polygons[i], ["merilo","zasuk","easting","northing"]]
                x_new, y_new = trans_2R_4params(point[0], point[1], params=params)

                new_points.append(Point(x_new, y_new))


        print params
        if len(new_points) == 1:
            return new_points[0]


        return new_points


# def pts_transformation(points,from_crs,method="triangle",df_parameters=None,KDTree_object=None):
#
#
#     methods = ["triangle","1region","3regions","7regions","24regions"]
#     shpfile = os.path.join(HOMEDIR, "static", "{}_parameters_from_{}.shp".format(method, from_crs))
#
#     #INPUT ERROR CHECK:
#     if not isinstance(points, list):
#         points = [points]
#
#     if isinstance(points[0], Point):
#         points = [(p.x, p.y) for p in points]
#
#     if method not in methods:
#         raise IOError("Type can only be on of {}!".format(",".join(methods)))
#
#     if df_parameters == None and method != "1region":
#         #1region doesnt have shapefile, parameters are hardcoded!
#         df_parameters = gpd.read_file(shpfile)
#
#
#     new_points = []
#
#     # TRIAGNLE 2R 6PARAMETRIC
#     if method == "triangle":
#
#
#         # Dovoli izracunat sele kasenje - optimization purposes
#         if not KDTree_object == None:
#             reference_points = np.array([(p.x, p.y) for p in df_parameters["geometry"].values.tolist()])
#
#             # create a KDTre object from a reference points
#             KDTree_object = spatial.KDTree(reference_points)
#
#         for point in points:
#             index_of_closest = KDTree_object.query(point)[1]
#             [a, b, c, d, e, f] = df_parameters.reset_index().ix[
#                 index_of_closest, "a b c d e f".split(" ")].values.tolist()
#             # https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
#
#             x_new, y_new = trans_2R_6params(point[0], point[1], [a, b, c, d, e, f])
#
#             new_points.append(Point(x_new, y_new))
#
#     # HELMERT 3R 7 PARAMETRIC
#     elif method in ["1region","3regions","7regions","24regions"]:
#
#         #doloci parametre
#         if method == "1region":
#             if from_crs == "d48":
#                 # from d48 to d96
#                 params = [409.545, 72.164, 486.872, 17.919665, -3.085957, -5.469110, 11.020289]
#             else:
#                 # from d96 to d48
#                 params = [-409.520, -72.192, -486.872, -17.919456, 3.086250, 5.468945, -11.020370]
#         else:
#             closest_polygons = closest_element_to_given_points(points,df_parameters)
#
#         for i,point in enumerate(points):
#             if method == "1region":
#                 x_new, y_new, _ = trans_3R_7params(point[0], point[1], 0, params=params)
#             else:
#                 params = df_parameters.ix[closest_polygons[i],"cx cy cz s rx ry rz".split(" ")]  #daj ven "id field"
#                 x_new, y_new, _ = trans_3R_7params(point[0], point[1], 0, params=params)
#
#             new_points.append(Point(x_new,y_new))
#
#
#     if len(new_points) == 1:
#         return new_points[0]
#
#     return new_points


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



def shp_transformation(df_in,from_crs,method):
    start = datetime.now()

    """
    Function for transformation from d96 to d48 and vice versa with the triangular transformation
    :param df_in:
    :param from_crs:
    :return:
    """

    #Create a Transformation object with all the neccessary data in it.
    ts = SlovenianTransformations(method=method,from_crs=from_crs)

    st_tock = 0

    if df_in.ix[0, "geometry"].type == "Point":
        pts = df_in["geometry"].values.tolist()
        st_tock += len(pts)

        # poracunaj nove tocke
        pts_out = ts.transform(points=pts)
        df_in["geometry"] = pts_out

    else:
        # change the geometry by applying transformation formula t0 each vertex:
        for i in df_in.index:
            geom = df_in.loc[i, "geometry"]

            if geom.type == "LineString":
                pts = geom.coords[:]
                st_tock += len(pts)

                # poracunaj nove tocke
                pts_out = ts.transform(points=pts)
                df_in.loc[i, "geometry"] = LineString(pts_out)

            elif geom.type == "MultiLineString":
                lines = []
                for line in geom.geoms[:]:
                    pts = line.coords[:]
                    st_tock += len(pts)

                    # poracunaj nove tocke
                    pts_out = ts.transform(points=pts)
                    lines.append(LineString(pts_out))

                df_in.loc[i, "geometry"] = MultiLineString(lines)

            elif geom.type == "Polygon":

                pts = geom.exterior.coords[:]
                st_tock += len(pts)

                # poracunaj nove tocke
                pts_out = ts.transform(points=pts)
                df_in.loc[i, "geometry"] = Polygon(pts_out)
            else:
                raise NotImplementedError(
                    "Found a geometry method {}! Function is implemented only for Point, LineString, "
                    "MultiLineStrings and Polygons.".format(
                        geom.type))

    total_seconds = (datetime.now() - start).total_seconds()
    tock_na_minuto = float(st_tock) / total_seconds
    print "Successully transfromed {} points in {:.2f} seconds with a speed of {:.2f} points/s).".format(st_tock,
                                                                                                         total_seconds,
                                                                                                         tock_na_minuto)

    return df_in
#
# def shp_triangular_transformation(df_in, from_crs="d96"):
#     start = datetime.now()
#
#     """
#     Function for transformation from d96 to d48 and vice versa with the triangular transformation
#     :param df_in:
#     :param from_crs:
#     :return:
#     """
#     from_crs = from_crs.lower()
#
#     if from_crs not in ["d96", "d48"]:
#         raise IOError("From_crs argument can only be d96 or d48!")
#
#     # read the correct (d96 or d48) file with transformation parameters for given direction
#     param_shp = os.path.join(HOMEDIR, "pysitra","static", "triangle_parameters_from_{}_points.shp".format(from_crs))
#     df_parameters = gpd.read_file(param_shp)
#
#     reference_points = np.array([(p.x, p.y) for p in df_parameters["geometry"].values.tolist()])
#
#     # create a KDTre object from a reference points
#     KDTree_object = spatial.KDTree(reference_points)
#
#     st_tock = 0
#
#     if df_in.ix[0, "geometry"].method == "Point":
#         pts = df_in["geometry"].values.tolist()
#         st_tock += len(pts)
#
#         # poracunaj nove tocke
#         pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
#                                                      df_parameters=df_parameters)
#         df_in["geometry"] = pts_out
#
#     else:
#         # change the geometry by applying transformation formula t0 each vertex:
#         for i in df_in.index:
#             geom = df_in.loc[i, "geometry"]
#
#             if geom.method == "LineString":
#                 pts = geom.coords[:]
#                 st_tock += len(pts)
#
#                 # poracunaj nove tocke
#                 pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
#                                                              df_parameters=df_parameters)
#                 df_in.loc[i, "geometry"] = LineString(pts_out)
#
#             elif geom.method == "MultiLineString":
#                 lines = []
#                 for line in geom.geoms[:]:
#                     pts = line.coords[:]
#                     st_tock += len(pts)
#
#                     # poracunaj nove tocke
#                     pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
#                                                                  df_parameters=df_parameters)
#                     lines.append(LineString(pts_out))
#
#                 df_in.loc[i, "geometry"] = MultiLineString(lines)
#
#             elif geom.method == "Polygon":
#
#                 pts = geom.exterior.coords[:]
#                 st_tock += len(pts)
#
#                 # poracunaj nove tocke
#                 pts_out = pts_triangle_transformation(points=pts, KDTree_object=KDTree_object,
#                                                              df_parameters=df_parameters)
#                 df_in.loc[i, "geometry"] = Polygon(pts_out)
#             else:
#                 raise NotImplementedError(
#                     "Found a geometry method {}! Function is implemented only for Point, LineString, "
#                     "MultiLineStrings and Polygons.".format(
#                         geom.method))
#
#     total_seconds = (datetime.now() - start).total_seconds()
#     tock_na_minuto = float(st_tock)/ total_seconds
#     print "Successully transfromed {} points in {:.2f} seconds with a speed of {:.2f} points/s).".format(st_tock, total_seconds,
#                                                                                  tock_na_minuto)
#
#     return df_in
#
#
#


# def pts_triangle_transformation(points, df_parameters, KDTree_object=None):
#     """
#     Function,
#
#     https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
#     :param points:
#     :param df_reference_points:
#     :return:
#     """
#
#     # Dovoli izracunat sele kasenje - optimization purposes
#     if not KDTree_object:
#         reference_points = np.array([(p.x, p.y) for p in df_parameters["geometry"].values.tolist()])
#
#         # create a KDTre object from a reference points
#         KDTree_object = spatial.KDTree(reference_points)
#
#     TRANS_PARAMETERS = "a b c d e f"
#
#     new_points = []
#
#     if not isinstance(points, list):
#         points = [points]
#
#     if isinstance(points[0], Point):
#         points = [(p.x, p.y) for p in points]
#
#     for point in points:
#         index_of_closest = KDTree_object.query(point)[1]
#         [a, b, c, d, e, f] = df_parameters.reset_index().ix[
#             index_of_closest, TRANS_PARAMETERS.split(" ")].values.tolist()
#         # https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
#
#         x_new,y_new = trans_2R_6params(point[0],point[1],[a, b, c, d, e, f])
#
#         new_points.append(Point(x_new, y_new))
#
#     if len(new_points) == 1:
#         return new_points[0]
#
#     return new_points