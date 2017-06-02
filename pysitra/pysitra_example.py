

from pysitra import SloTransformation


D48_POINTS = [(500000,100000),(0,0),(650000,200000)]


# Initialize a Transformation object
ts_triangle = SloTransformation(from_crs="d48",method="triangle")

ts_24region = SloTransformation(from_crs="d48",method="24regions")



D96_POINTS_triangle = ts_triangle.transform(D48_POINTS)
D96_POINTS_24regions = ts_24region.transform(D48_POINTS)

