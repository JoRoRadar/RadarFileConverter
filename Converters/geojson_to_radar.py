import json
import csv
import re
import subprocess

# GeoJSON Types:
#   Point, LineString, Polygon, MultiPoint, MultiLineString,
#   MultiPolygon, and GeometryCollection.
#
# We cannot support: LineString, Multilinestring, GeometryCollection
# * Linestring doesn't have a good analogy for geofences.
# * MultiLinestring doesn't have a good analogy for geofences.
# * GeometryCollection greatly increases complexity.
#
# Polygons can have holes in them. This is not supported.
#
# Multipolygons will be converted into multiple geofences utilizing an increasing index.
#
# Multipoints will be converted into multiple geofences utilizing an increasing index.
# When geometries cross the antimeridian, the GeoJSON is converted.
#
# Due to Antimeridian Cutting that GeoJSON enforces, this will almost always cause issues
# with the way Radar handles geofences. Solving for this would greatly increase complexity
#
# Metadata can only have str int and bool
#

class GeoJsonConverter:

    defaultPointRadiusSize = 10
    defaultIsochroneValue = 15

    supportedTypes = ["Point", "Polygon", "MultiPoint", "MultiPolygon"]
    jsonData = {}
    filePath = ""
    fileName = ""

    outputDirectory = "./Converters/RadarFiles/"
    filePathRegex = "\/([^\/]+)\.geojson"

    isValidFile = False

    csvFile = None
    csvWriter = None

    radarCSVHeaders = ["description", "tag", "externalId", "type", "radius", "coordinates", "enabled", "metadata"]

    descriptionKey = None
    tagKey = None
    externalIdKey = None
    isochroneKey= None
    radiusKey = None

    includePropertiesAsMetadata = True
    useFileNameAsTag = True

    currentGeoJSON = None

    indexCounter = {}

    circlesCounter = 0
    isochroneCounters = 0
    polygonCounters = 0

    def __init__(self, filePath=filePath, useFilenameAsTag=True, includePropertiesAsMetadata=True, descriptionKey=None, tagKey=None, externalIdKey=None, isochroneKey=None, radiusKey=None):

        self.useFileNameAsTag = useFilenameAsTag
        self.includePropertiesAsMetadata = includePropertiesAsMetadata

        self.descriptionKey = descriptionKey
        self.tagKey = tagKey
        self.externalIdKey = externalIdKey
        self.isochroneKey = isochroneKey
        self.radiusKey = radiusKey

        self.filePath = filePath
        self.fileName = re.search(self.filePathRegex, self.filePath)

        if self.fileName:
            self.fileName = self.fileName[1]

            self.isValidFile = True
            self.csvFile = open(self.outputDirectory + self.fileName + ".csv", "w+")
            self.csvWriter = csv.DictWriter(self.csvFile, quoting=csv.QUOTE_NONNUMERIC, fieldnames=self.radarCSVHeaders, doublequote=True)
            self.csvWriter.writeheader() #Update to Radar Import process now REQUIRES header

            self.jsonData = json.load(open(filePath))

            if self.useFileNameAsTag:
                self.tagKey = self.fileName

    def process(self):
        self.process_geojson(self.jsonData)
        self.csvFile.close()

        print(f"Stats:\n\tCircles: {self.circlesCounter}\n\tIsochrones: {self.isochroneCounters}\n\tPolygons: {self.polygonCounters}")

        self.fix_single_quotes()

    def fix_single_quotes(self):
        subprocess.call(['sh', './Converters/Utilities/quote_fixer.sh', self.outputDirectory + self.fileName + ".csv"])

    def process_geojson(self, currentGeoJSON, properties=None):
        geoType = currentGeoJSON["type"]

        if geoType == "Feature":
            self.process_geojson(currentGeoJSON["geometry"], properties=currentGeoJSON["properties"])
        elif geoType == "FeatureCollection":
            for feature in currentGeoJSON["features"]:
                self.process_geojson(feature)
        elif geoType in self.supportedTypes:
            self.process_type(currentGeoJSON, properties)

    def process_type(self, geoJSON, properties):
        if geoJSON["type"] == "Point":
            self.write_point(geoJSON["coordinates"], properties)

        elif geoJSON["type"] == "Polygon":
            self.write_polygon(geoJSON["coordinates"][0], properties) #First Element Only to ignore holes

        elif geoJSON["type"] == "MultiPoint":
            for point in geoJSON["coordinates"]:
                self.write_point(point, properties)

        elif geoJSON["type"] == "MultiPolygon":
            for polygon in geoJSON["coordinates"]:
                self.write_polygon(polygon[0], properties)

    def write_point(self, coordinates, properties):

        row = self.setup_row(properties)

        if row is None:
            return

        if self.isochroneKey is not None:

            self.isochroneCounters += 1

            row["type"] = "isochrone"

            row["radius"] = self.defaultIsochroneValue

            if properties[self.isochroneKey] and isinstance(properties[self.isochroneKey], int):
                row["radius"] = properties[self.isochroneKey]

        else:

            self.circlesCounter += 1

            row["type"] = "circle"
            row["radius"] = self.defaultPointRadiusSize

            if self.radiusKey and properties[self.radiusKey] and isinstance(properties[self.radiusKey], int):
                row["radius"] = properties[self.radiusKey]

        row["coordinates"] = coordinates

        self.csvWriter.writerow(row)

    def write_polygon(self, coordinateArray, properties):

        row = self.setup_row(properties)

        if row is None:
            return

        self.polygonCounters += 1

        row["type"] = "polygon"
        row["radius"] = 0 #Ignored

        row["coordinates"] = coordinateArray

        self.csvWriter.writerow(row)

    def setup_row(self, properties):

        # properties = self.clean_properties(properties)

        row = {}

        if self.descriptionKey and properties[self.descriptionKey] and isinstance(properties[self.descriptionKey], str):
            row["description"] = properties[self.descriptionKey]

        row["tag"] = self.fileName
        if not self.useFileNameAsTag and self.tagKey and properties[self.tagKey] and isinstance(properties[self.tagKey], str):
            row["tag"] = properties[self.tagKey]

        if self.externalIdKey and properties[self.externalIdKey] and isinstance(properties[self.externalIdKey], str):

            externalId = properties[self.externalIdKey]
            if externalId in self.indexCounter:
                row["externalId"] = externalId + f"_{self.indexCounter[externalId]}"
                self.indexCounter[externalId] += 1
            else:
                row["externalId"] = externalId + "_0"
                self.indexCounter[externalId] = 1
        else:
            if self.fileName in self.indexCounter:
                row["externalId"] = self.fileName + f"_{self.indexCounter[self.fileName]}"
                self.indexCounter[self.fileName] += 1
            else:
                row["externalId"] = self.fileName + "_0"
                self.indexCounter[self.fileName] = 1

        row["enabled"] = True

        if self.includePropertiesAsMetadata:
            row["metadata"] = properties

        return row

    def clean_properties(self, properties):
        new_props = {}
        for key in properties.keys():
            if isinstance(properties[key], int) or isinstance(properties[key], bool) or isinstance(properties[key], str) or isinstance(properties[key], None):
                new_props[key] = properties[key]

        new_props