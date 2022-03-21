from geojson_to_radar import GeoJsonConverter

# Params

PATH_TO_GEOJSON = "./GeoJSONFiles/convertedFile.geojson" # GeoJSON file path for file to convert
useFileNameAsTag = True # Should the output file share the same name as input file (Will have CSV extension though)
includePropertiesAsMetadata = False #Use GeoJSON properties and Radar Geofence Metadata
descriptionKey = "" # What GeoJSON property key has the value for the Radar Description (Ignored if null)
tagKey = "" # What GeoJSON property key has the value for the Radar Tag (Defaults to filename)
externalIdKey = "" # What GeoJSON property key has the value for the Radar ExternalID (Defaults to file name + index counter )
isochroneKey = "" # What GeoJSON property key has teh value for the Radar Isochrone Radius (Defaults to static value)
radiusKey = "" # What GeoJSON property key has the value for the Radar Geofence Radius value (Defaults to static value)

##

gc = GeoJsonConverter(
    filePath=PATH_TO_GEOJSON,
    useFilenameAsTag=useFileNameAsTag,
    includePropertiesAsMetadata=includePropertiesAsMetadata,
    descriptionKey=descriptionKey,
    tagKey=tagKey,
    externalIdKey=externalIdKey,
    isochroneKey=isochroneKey,
    radiusKey=radiusKey)

gc.process()