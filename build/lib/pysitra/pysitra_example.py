from __future__ import print_function 

######################################################
#### 1. TRANSFORMING PYTHON LISTS OF POINTS  #########
######################################################

from pysitra import SloTransformation

# List of point that you want converted into d96 via several methods
D48_POINTS = [(500000,100000),(0,0),(650000,200000)]


# Initialize a Triangle Transformation object
ts_triangle = SloTransformation(from_crs="d48",method="triangle")

# Initialize a 24regions transformation object
ts_24region = SloTransformation(from_crs="d48",method="24regions")

# Initialize a affine transformation object with your own parameters
ts_triangle_manual = SloTransformation(from_crs="d48",method="triangle",params="1.00001;0.000040647;-374.668;-0.00002241;1.000006;494.8428".split(";"))

# Note, that seemingly redundant recreation of different transformations as a separate object comes very handy, when you want to
# transform many files/lists at once, so you don't have to perform the expensive transformation object initialization
# for every file/list separately.


# Once you have transformation object initialized, you can use it's .transform() method to transform old points into
# new points quite cheaply:
print("\nTriangle transformation (affine 6parametric):")
print(ts_triangle.transform(D48_POINTS))
print("\n24regions transformation (4parametric):")
print( ts_24region.transform(D48_POINTS))
print("\nTriangle transformation with custom parameters:")
print(ts_triangle_manual.transform(D48_POINTS))

############################################
#### 2. TRANSFORMING FILES WTIH PYTHON##
############################################

from pysitra import shp_transformation,csv_transformation
from pysitra.utils import recognize_csv_separator,check_for_csv_header
import geopandas as gpd
import pandas as pd


# SHAPEFILES:

#read shapefile into GeoDataFrame and transform it and save it as into new shapefile
df_in = gpd.read_file("shapefile_in_d48.shp")
df_out = shp_transformation(df_in,from_crs="d48",method="24regions")
df_out.to_file("shapefile_in_d96.shp")


# ASCII CSVS:
csv_file = "terrain_measurements_in_d48.csv"

sep = recognize_csv_separator(csv_file) #guess the separator type
header = check_for_csv_header(csv_file) #check if file has header

#read csv file into DataFrame, transform them by triangle method with custom parameters and save it to csv.
csv_in = pd.read_csv(csv_file, sep=sep, header=header)
csv_out = csv_transformation(df_in=csv_in, from_crs="d48", method="triangle", params="1.00001;0.000040647;-374.668;-0.00002241;1.000006;494.8428".split(";"))
csv_out.to_file("terrain_measurements_in_d96.csv")





#######################################################################
##### 3. USING LOW LEVEL FUNCTION TO TRANSFORM POINT-BY-POINT  ########
#######################################################################

from pysitra import trans_2R_4params,trans_2R_6params

D48_POINTS = [(500000,100000),(0,0),(650000,200000)]

for point in D48_POINTS:
    # 4parametric transformation with params: scale,rotation,trans_x,trans_y
    x, y = trans_2R_4params(point[0], point[1], params=[0.9999873226,0.0009846750,378.755,-493.382])
    print(x, y)
    # 6parametric transformation with params a,b,c,d,e,f
    x, y = trans_2R_6params(point[0], point[1], params=[1.00001,0.000040647,-374.668,-0.00002241,1.000006,494.8428])
    print(x, y)
