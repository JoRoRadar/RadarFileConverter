import geopandas

OUTPUT_DIRECTORY = "./GeoJSONFiles"

# Supply a Shapefile to Geopandas to convert to GeoJSON
shpfile = geopandas.read_file("")
shpfile = shpfile.to_crs(epsg=4326) # Sometimes shapefiles are not in the correct coordinate system.

# Specify output GeoJSON File name as needed.
shpfile.to_file(OUTPUT_DIRECTORY + '/convertedFile.geojson', driver='GeoJSON')