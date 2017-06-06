from __future__ import print_function    # (at top of module)
import click
from . import utils,trans
import geopandas as gpd
import os
import pandas as pd
import warnings



@click.command()
@click.option("--to_crs", required=True, type=click.Choice(["d48", "d96"]), help="Coordinate system to transform your data into")
@click.option("--method", default="triangle",  type=click.Choice(["triangle", "24regions"]), help="Transformation method to be used")
@click.option("--params", required=False,default=None, help="Optional argument: semicolon separated manual parameters, required for each transformation method (24regions:4params, triangle:6params,...")
@click.argument("file_in", required=True)
@click.argument("file_out", required=False)
def cli(to_crs,method,params,file_in,file_out):

    if to_crs == 'd48':
        from_crs = "d96"
        to_epsg = 3912
        from_epsg = 379
    else:
        from_crs = "d48"
        to_epsg = 3794
        from_epsg = 3912

    params = [float(i) for i in params.split(";")] if params != None else None


    name, ext = os.path.splitext(os.path.abspath(file_in))

    #Save file!
    if not file_out:
        file_out = name + "_" + to_crs + ext

    # Command line utility tool for two way transformation between old slovenian CRS (D48GK) and new slovenian CRS (D96TM).
    click.echo("Transformating a file {} into {} and saving it to {}...".format(file_in,to_crs,file_out))


    if ext == ".shp":

        #Check file input epsg code (can only be 3912 or 3794 or none!)
        file_epsg = utils.cheesy_slovenian_epsg_checker(file_in)

        if file_epsg == from_epsg:
            pass
        elif file_epsg == None:
            raise IOError("Shapelile can only be in crs d48 (EPSG:3912) or d96 (EPSG:3794)! It didn't find word 'slovene' in prj file!")
        elif file_epsg == to_epsg:
            raise IOError("The input shapefile you've specified ({}) already seems to be in a projection "
                          "that you want to transform it into ({}, epsg: {})! That doesn't make any sense!".format(file_in,to_crs,file_epsg))


        df_in = gpd.read_file(file_in)

        print("\nInput data sample:")
        print(df_in)

        df_out = trans.shp_transformation(df_in=df_in, from_crs=from_crs,method=method,params=params)

        print("\nOutput data sample:")
        print(df_out)

        utils.save_to_shapefile_with_prj(geo_df=df_out, file_out=file_out, epsg=to_epsg)


    elif ext.lower() in [".txt",".csv"]:
        #NO ESPG CHECK...
        warnings.warn("Program can't perform a EPSG check of the input data for csv files for you. "
                      "Let's hope that you specified everything correctly!")

        sep = utils.recognize_csv_separator(file_in)
        header = utils.check_for_csv_header(file_in)
        df_in = pd.read_csv(file_in,sep=sep,header=header)

        print("\nInput data sample:")
        print(df_in)

        df_out = trans.csv_transformation(df_in=df_in, from_crs=from_crs,method=method,params=params)

        print("\nOutput data sample:")
        print(df_out)

        df_out.to_csv(file_out,sep=sep,header=header,index=None)



    else:
        raise IOError("Only shapefiles and csv files are supported input type!")
