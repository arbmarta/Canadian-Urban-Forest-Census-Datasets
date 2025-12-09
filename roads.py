import geopandas as gpd

roads = gpd.read_file('Datasets/Inputs/roads/roads.shp')
csd = gpd.read_file('Datasets/Outputs/urban csds/urban csds.gpkg', layer='urban csds')

print(roads.columns)