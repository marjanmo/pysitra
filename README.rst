
WORK IN PROGRESS!  NOT YET AVAILABLE!


Python package for a two-way transformation between old and new slovenian coordinates system

PyPI address:

Comes with a handy command-line utility tool that enables easy batch conversion of shapefiles

Only suitable for slovenian coordinate systems d48GK (espg 3912) and d96TM (epsg 3974). Supports shapefiles for IO only!


Methods:
- triangle (best accuracy)
- 24regions
- 7regions
- 3regions
- 1region (Slovenia)
 custom

Example usage:



cmd:
sitra --help

sitra -to_crs=d48 -method=triangular old_shapefile.shp new_shapefile.shp
sitra -to_crs=d96 -method=24regions old_shapefile.shp new_shapefile.shp

Rules:
1. If no outfile name is given, the same filename with extension _{crs} will be used!
2. Will complain if input's crs is not reverse of the desired crs!
3. So far supports shapefiles with points,
4. Transformation speed is faaaar from optimal (on my Xeon, cca 7000 points/second) , so don't abuse it.

#DOCS:
- link to the theoretical background and sources
- github page!
- examples
- click demo!


#TODO:
Implementation for 3D points, manual transformation parameters...


SEE ALSO:
http://geocoordinateconverter.tk/index.html