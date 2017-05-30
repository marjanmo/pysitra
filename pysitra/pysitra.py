import click
from . import utils
import geopandas as gpd
import os



@click.command()
@click.option("-to_crs", required=True, type=click.Choice(["d48", "d96"]), help="Coordinate system to transform your data into")
@click.option("-method", default="triangle",  type=click.Choice(["triangle", "24regions", "7regions","manual"]), help="Transformation method to be used")
@click.argument("shp_in", required=True)
@click.argument("shp_out", required=False)
def cli(to_crs,method,shp_in,shp_out):

    if to_crs == 'd48':
        from_crs = "d96"
        to_epsg = 3912
        from_epsg = 379
    else:
        from_crs = "d48"
        to_epsg = 3794
        from_epsg = 3912

    #Save file!
    if not shp_out:
        name,ext = os.path.splitext(os.path.abspath(shp_in))
        shp_out = name + "_" + to_crs + ext


    #Check file input epsg code (can only be 3912 or 3794 or none!)
    file_epsg = utils.cheesy_slovenian_epsg_checker(shp_in)

    if file_epsg == from_epsg:
        pass
    elif file_epsg == None:
        raise IOError("Shapelile can only be in crs d48 (EPSG:3912) or d96 (EPSG:3794)! It didn't find word 'slovene' in prj file!")
    elif file_epsg == to_epsg:
        raise IOError("The input shapefile you've specified ({}) already seems to be in a projection "
                      "that you want to transform it into ({}, epsg: {})! That doesn't make any sense!".format(shp_in,to_crs,file_epsg))


    # Command line utility tool for two way transformation between old slovenian CRS (D48GK) and new slovenian CRS (D96TM).
    click.echo("Transformating a file {} to crs:{} and saving it to {}...".format(shp_in,to_crs,shp_out))

    df_in = gpd.read_file(shp_in)


    if method == "triangle":
        df_out = utils.shp_triangular_transformation(df_in=df_in, from_crs=from_crs)

    elif method == "24regions":
        df_out = None
        #TODO:NAREDI
        raise NotImplementedError("24regions not yet implemented!")

    elif method == "7regions":
        df_out = None
        #TODO:NAREDI
        raise NotImplementedError("24regions not yet implemented!")

    else:
        df_out = None
        #TODO:NAREDI
        raise NotImplementedError("24regions not yet implemented!")





    utils.save_to_shapefile_with_prj(geo_df=df_out, file_out=shp_out, epsg=to_epsg)
