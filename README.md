# Radar CSV File Converter

## Purpose
Convert Shapefiles or GeoJSON files into Radar CSV files ready for import. The final step in converting is always from GeoJSON to Radar CSV. 

#### Example Flow
'Shapefile' -> 'GeoJSON' -> Radar CSV

## How to use

### Starting with a Shapefile
Open the _shapefile_to_geojson.py_ file and:  
1) Specify the shapefile location for _geopandas_ to read. 
2) Specify the output file name/location.

### Converting a GeoJSON File
Open the _run.py_ file and:
1) Update the parameters with the needed values.
2) Run the file.

---

## Files

### run.py
This is the main file to run to convert GeoJSON files into Radar CSV. There are a few parameters that need to be specified for the GeoJSON file conversion to run smoothly:

-**filePath** : Path to the GeoJSON file to convert  
-**useFileNameAsTag** : Should the output file share the same name as input file. The file extension will always be _.csv_ regardless.  
-**includePropertiesAsMetadata** : Should all properties in the GeoJSON properties object be included as Metadata items for the Radar Geofence.  
-**descriptionKey** : What GeoJSON proeprty key has the value for the Radar Description. If this value is null that description will be ignored.  
-**tagKey** : What GeoJSON proeprty key has the value for the Radar Tag. This will default to the GeoJSON file name if property not specified or not found in the file.  
-**externalIdKey** : What GeoJSON property key has the value for the Radar ExternalID. This will default to the GeoJSON file name concatonated with an index counter.  
-**isochroneKey** : What GeoJSON proeprty key has the value for the Radar isochrone radius. This defaults to a static value specified in the _GeoJsonConverter_ class.  
-**radiusKey** : What GeoJSON property has the value for the radar geofence radius value. This defaults to a static value specified in the _GeoJsonConverter_ class.  

### shapefile_to_geojson.py
A simple file for converting Shapefiles to GeoJSON files using the _geopandas_ library. We also convert/specify the coordinate system being used to the standard latitude/longitude system that Radar uses.  
The current read path looks for a file in the _Inputs_ file directory and outputs to the _GeoJSONFiles_ directory.

### qeojson_to_radar.py
Converts a GeoJSON file to a Radar CSV file ready to import.  
There is no specified path prefix for the GeoJSON file. The output CSV will be placed in the _RadarFiles_ directory.

### quote_fixer.sh
Python doesn't allow for easy conversion between single and double quotes on strings. Thus we need to execute a shell file to swap all the single quotes that python uses for file writes to double quotes. This is required since the Radar CSV import doesn't allow for single quotes.

---

## Future Updates

- Support additional file types as needed.
- Use a GUI file picker
- Provide helpers for picking GeoJSON property keys.
- Automatially identify file type and run needed processes.