
#WORK IN PROGRESS!  NOT YET AVAILABLE!

#PySitra

Python package for a two-way 2D transformation between old and new slovenian coordinates system

## About

PySitra is The project and it's name is inspired by the popular Slovenian web portal for online point transformation between 
old and new coordinate systems, called [SitraNet.si](www.sitranet.si) and it's C-written command-line-friendly 
successor [Geo Coordinate Converter](http://geocoordinateconverter.tk/indeks.html).
It comes with a handy command-line utility tool that enables easy batch conversion of shapefiles

Only suitable for slovenian coordinate systems d48GK (espg 3912) and d96TM (epsg 3974). Supports shapefiles for IO only!

For more theoretical background

## Installation:

Library is available on PyPi repository, so it can easily be installed with pip:

```
pip install pysitra
```



Available methods:
- ***triangle:*** affine 6-parametric 2D triangle transformation, based on 899 [Slovenian reference points](http://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/drzavni-koordinatni-sistem/horizontalni-drzavni-koordinatni-sistem-d96tm/d96tm/transformacijski-parametri/) (best accuracy)
- ***24regions:*** simplified 4-parametric 2D transformation (where parameteres are precalculated for 24 Slovenian regions
([more info](http://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/drzavni-koordinatni-sistem/horizontalni-drzavni-koordinatni-sistem-d96tm/d96tm/transformacijski-parametri/))



##Usage:

### Python API





### Command Line Utility

```
$ sitra --help
Usage: sitra [OPTIONS] FILE_IN [FILE_OUT]

Options:
  --to_crs [d48|d96]             Coordinate system to transform your data into
                                 [required]
  --method [triangle|24regions]  Transformation method to be used
  --params TEXT                  Optional argument: semicolon separated manual
                                 parameters, required for each transformation
                                 method (24regions:4params,
                                 triangle:6params,...
  --help                         Show this message and exit.


```

**RULES AND DEFAULT CMD BEHAVIOUR**


* Valid input file types are ESRI Shapefiles (\*.shp) or plain ASCII csv files (\*.csv, *.txt)
* If no outfile name is given, the same filename with extension _{crs} will be used automaticaly! 
(e.g.: shapefile.shp --> shapefile_d96.shp)
* If input file is type *.shp, program check its EPSG code and 
will complain if input's crs is not reverse of the desired crs!
* If input file is ASCII type, program will try to autodetect field for easting and northing by checking
 the column values range and column names
* parameter `--to_crs` is required and can only be `d96` or `d48`.
* default value for `--method` is `triangle` (best accuracy)
* default value for `--params` is `None` (they get calculated automatically - best accuracy)
* Transformation speed is faaaar from optimal (on my Xeon, cca 7000 points/second) , so don't abuse it.


**EXAMPLES**:
1. Very basic example usage for transforming shapefile with default settings (--method=triangle) will save result into 'old_shapefile_d96.shp'
```
sitra --to_crs=d96 -method=triangular old_shapefile.shp
```

2. Another example, this time with --method=24regions and specified output.

```
sitra --to_crs=d96 --method=24regions old_shapefile.shp new_shapefile.shp
```

3. Example with csv file (note that no csv format specification is needed --> separator and columns are automatically guessed!)x,y field specification )

```
sitra --to_crs=d48 --method=24regions Cool_points.csv Back_to_MariaTheresa_times.csv
```


4. In all above examples the transformation parameters were automatically calculated based on a chosen method and point location.
But you can also specify your own parameters, but you have to make sure you pass correct number of parameters in right 
order for the corresponding transformation method. Here is an example for custom d48-->d96 tranformation with 
affine (~triangle) method (see the [rules](#RULES-AND-DEFAULT-CMD-BEHAVIOUR) section of the README. RULES):

```
sitra --to_crs=d96 --method=triangle --params=' old_points.csv new_points.csv
```


##DOCS:
- link to the theoretical background and sources
- github page!
- examples
- click demo!


###TODO:
Implementation for 3D points, ...


## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc