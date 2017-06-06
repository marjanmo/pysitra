from __future__ import print_function
from . import utils
import os
import math
from shapely.geometry import Point, LineString, Polygon, MultiLineString
from scipy import spatial
import geopandas as gpd
import numpy as np
from datetime import datetime

HOMEDIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))


class SloTransformation:

    methods = ["triangle", "24regions"]

    not_implemented_methods = ["1region", "3regions", "7regions"]

    def __init__(self,from_crs, method="triangle",params=None):

        if method not in self.methods:
            if method in self.not_implemented_methods:
                raise NotImplementedError("Method {} is not yet implemented! So far it can only be one of {}!".format(self.method,self.methods))
            else:
                raise IOError("Type can only be one of {}!".format(",".join(self.methods)))

        if from_crs not in ["d96", "d48"]:
            raise IOError("From_crs argument can only be d96 or d48!")

        self.method = method
        self.params = params
        self.from_crs = from_crs

        self.shpfile = os.path.join(HOMEDIR, "pysitra","static", "{}_parameters_from_{}.shp".format(self.method, self.from_crs))


        if self.params != None:  # Custom parameters! Error check parameteres
            if self.method in ["1region","3regions","7regions"]:
                if len(params) != 7:
                    raise IOError("You specified manual parameters: {}. Method {} requires 7 parameters in order 'cx;cy;cz;s;rx;ry;rz' (3x translation, 1x scale, 3x rotation)!"
                                  .format(self.params,self.method,len))

            if self.method == "24regions":
                if len(params) != 4:
                    raise IOError("You specified manual parameters: {}. Method 24regions requires 4 parameters in order "
                                  "'scale;rotation;transx;transy'!".format(self.params))

            if self.method == "triangle":
                if len(params) != 6:
                    raise IOError(
                        "You specified manual parameters: {}. Method triangle requires 6 parameters in order 'a;b;c;d;e;f' "
                        "(scalex,scaley,rotationx,rotationy,transx,transy)!".format(self.params))

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
                if self.params:
                    params = self.params
                else:
                    params = self.df_parameters.reset_index().ix[
                        index_of_closest, "a b c d e f".split(" ")].values.tolist()
                # https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array

                x_new, y_new = trans_2R_6params(point[0], point[1], params)
                new_points.append(Point(round(x_new, 2), round(y_new, 2)))

        # HELMERT 3R 7 PARAMETRIC
        elif self.method in ["1region", "3regions", "7regions"]:

            # doloci parametre
            if self.method == "1region":
                if self.params:
                    params = self.params
                else:
                    if self.from_crs == "d48":
                        # from d48 to d96
                        params = [409.545, 72.164, 486.872, 17.919665, -3.085957, -5.469110, 11.020289]
                    else:
                        # from d96 to d48
                        params = [-409.520, -72.192, -486.872, -17.919456, 3.086250, 5.468945, -11.020370]
            else:
                closest_polygons = utils.closest_element_to_given_points(points, self.df_parameters)

            for i, point in enumerate(points):
                if self.method == "1region":
                    x_new, y_new, _ = trans_3R_7params(point[0], point[1], 0, params=params)
                else:
                    params = self.df_parameters.ix[closest_polygons[i], "cx cy cz s rx ry rz".split(" ")]  # daj ven "id field"
                    #TODO:Impletement 3D points!
                    x_new, y_new, _ = trans_3R_7params(point[0], point[1], 0, params=params)

                new_points.append(Point(round(x_new,2), round(y_new,2)))

        #AFFINE 2R 4parametric
        elif self.method == "24regions":
            closest_polygons = utils.closest_element_to_given_points(points, self.df_parameters)

            for i, point in enumerate(points):
                if self.params:
                    params = self.params
                else:
                    params = self.df_parameters.ix[closest_polygons[i], ["merilo","zasuk","easting","northing"]]
                x_new, y_new = trans_2R_4params(point[0], point[1], params=params)

                new_points.append(Point(round(x_new, 2), round(y_new, 2)))

        if len(new_points) == 1:
            return new_points[0]

        return new_points

def trans_2R_6params(x,y,params=()):
    #parameters in order a,b,c,d,e,f

    [a, b, c, d, e, f] = params

    # calculate new points
    x_new = a * x + b * y + c
    y_new = d * x + e * y + f

    return x_new,y_new

def trans_3R_7params(x,y,z,params=()):
    # parameters in order cx,cy,cz,s,rx,ry,rz (https://en.wikipedia.org/wiki/Helmert_transformation)
    [cx,cy,cz,s,rx,ry,rz] = params

    sec_to_rad = 4.8481e-6
    rx = rx*sec_to_rad
    ry = ry*sec_to_rad
    rz = rz*sec_to_rad


    x_new = cx + (1+s*10e-6)*(x - rz*y + ry*z)

    y_new = cy + (1+s*10e-6)*(rz*x + y - rx*z)
    z_new = cz + (1+s*10e-6)*(-ry*x + rx*y + z)

    # import numpy as np
    # mx = np.array([x,y,z])
    # mc = np.array([cx,cy,cz])
    # mr = np.array([[1,-rz,ry],[rz,1,-rx],[-ry,rx,1]])
    # a = mc + (1+s*0.000001)*np.dot(mr,mx)
    # x_new, y_new, z_new = a

    return x_new,y_new,z_new

def trans_2R_4params(x,y,params):
    C, D, A, B = params

    if D -180 > 0: #Find angles almost 360 deg, because in file it should be negative angle instead of almost 360!
        D = D - 360

    D = D * 2 * math.pi / 360

    x_new = A + C * x - D * y
    y_new = B + D * x + C * y

    return x_new, y_new

def csv_transformation(df_in,from_crs,method,params=None):
    start = datetime.now()

    # Create a Transformation object with all the neccessary data in it.
    ts = SloTransformation(method=method, from_crs=from_crs, params=params)

    x_f,y_f,z_f = utils.recognize_xyz_fields(df_in)

    pts = df_in[[x_f,y_f]].values.tolist()

    pts = [(i.x,i.y) for i in ts.transform(pts)]
    df_in[x_f]  = [i[0] for i in pts]
    df_in[y_f] = [i[1] for i in pts]

    num_pts = len(pts)
    total_seconds = (datetime.now() - start).total_seconds()
    tock_na_minuto = float(num_pts) / total_seconds
    print("Successully transfromed {} points in {:.2f} seconds with a speed of {:.2f} points/s.".format(num_pts,
                                                                                                         total_seconds,
                                                                                                         tock_na_minuto))
    return df_in

def shp_transformation(df_in,from_crs,method,params=None):
    start = datetime.now()

    """
    Function for transformation from d96 to d48 and vice versa with the triangular transformation
    :param df_in:
    :param from_crs:
    :return:
    """

    #Create a Transformation object with all the neccessary data in it.
    ts = SloTransformation(method=method,from_crs=from_crs,params=params)

    num_pts = 0

    if df_in.ix[0, "geometry"].type == "Point":
        pts = df_in["geometry"].values.tolist()
        num_pts += len(pts)

        # poracunaj nove tocke
        pts_out = ts.transform(points=pts)
        df_in["geometry"] = pts_out

    else:
        # change the geometry by applying transformation formula t0 each vertex:
        for i in df_in.index:
            geom = df_in.loc[i, "geometry"]

            if geom.type == "LineString":
                pts = geom.coords[:]
                num_pts += len(pts)

                # poracunaj nove tocke
                pts_out = ts.transform(points=pts)
                df_in.loc[i, "geometry"] = LineString(pts_out)

            elif geom.type == "MultiLineString":
                lines = []
                for line in geom.geoms[:]:
                    pts = line.coords[:]
                    num_pts += len(pts)

                    # poracunaj nove tocke
                    pts_out = ts.transform(points=pts)
                    lines.append(LineString(pts_out))

                df_in.loc[i, "geometry"] = MultiLineString(lines)

            elif geom.type == "Polygon":

                pts = geom.exterior.coords[:]
                num_pts += len(pts)

                # poracunaj nove tocke
                pts_out = ts.transform(points=pts)
                df_in.loc[i, "geometry"] = Polygon(pts_out)
            else:
                raise NotImplementedError(
                    "Found a geometry method {}! Function is implemented only for Point, LineString, "
                    "MultiLineStrings and Polygons.".format(
                        geom.type))

    total_seconds = (datetime.now() - start).total_seconds()
    tock_na_minuto = float(num_pts) / total_seconds
    print("Successully transfromed {} points in {:.2f} seconds with a speed of {:.2f} points/s.".format(num_pts,
                                                                                                         total_seconds,
                                                                                                         tock_na_minuto))

    return df_in