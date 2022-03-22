import geopandas as gpd
from shapely.geometry import Polygon
from shapely import affinity
import math
import csv
import sys
import json
import subprocess
import folium
import webbrowser

csv.field_size_limit(sys.maxsize)  # Ensures we can load the coordinates into memory to write to file.

RADAR_CSV_FILE_PATH = ""


class SimplifyRadarPolygons:
    # I think my math is right
    degreeToMeter = 111219.8  # Avg'd
    degreeToMeterSqrd = degreeToMeter * degreeToMeter
    meterToDegree = 1 / degreeToMeter

    defaultCircleRadius = 100

    lowReduction = (360 / 43200) / 10  # Should be about 100 Meters
    mediumReduction = (360 / 43200) / 5  # Should be about 500 Meters
    largeReduction = 360 / 43200  # ~1Km of tolerance (Degrees)

    minimumPolyAreaSize = 1500  # Giving some buffer

    maxPolyCoordinateCount = 10000  # Radar only allows 10K points (Giving a buffer)

    radarCSVHeaders = ["description", "tag", "externalId", "type", "radius", "coordinates", "enabled", "metadata"]

    def __init__(self, filePath):

        self.totalPolygons = 0
        self.scaledPolygons = 0
        self.convertedPolygons = 0
        self.reducedPolygons = [0, 0, 0]

        self.csvFile = open(filePath)

        totalRows = sum(1 for row in csv.reader(self.csvFile))
        print(f"Total CSV Rows : {totalRows}")
        self.csvFile.seek(0)

        self.csvOutputFile = open("simplified.csv", "w+")
        self.csvWriter = csv.DictWriter(self.csvOutputFile, quoting=csv.QUOTE_NONNUMERIC,
                                        fieldnames=self.radarCSVHeaders,
                                        doublequote=True)
        self.csvWriter.writeheader()  # Update to Radar Import process now REQUIRES header

    def run(self):
        self.simplify_rows()
        self.fix_single_quotes()

        print("Stats->")
        print(f"\tTotal Polygons: {self.totalPolygons}")
        print(f"\tScaled Polygons: {self.scaledPolygons}")
        print(f"\tConverted Polygons: {self.convertedPolygons}")
        print(f"\tLow Reduction Polygons: {self.reducedPolygons[0]}")
        print(f"\tMedium Reduction Polygons: {self.reducedPolygons[1]}")
        print(f"\tLarge Reduction Polygons: {self.reducedPolygons[2]}")

    def fix_single_quotes(self):
        print("Warning: Attempting to fix single quotes on metadata. Sometimes the regex fails spectacularly. Comment "
              "out if needed and use a text editor to do a global find and replace.")
        subprocess.call(['sh', './quote_fixer.sh', "simplified.csv"])

    def poly_coord_count_to_large(self, polygon):
        return len(list(polygon.exterior.coords)) > self.maxPolyCoordinateCount

    def simplify_rows(self):

        """
        Expected Header
        ["description", "tag", "externalId", "type", "radius", "coordinates", "enabled", "metadata"]
        """

        reader = csv.DictReader(self.csvFile, fieldnames=self.radarCSVHeaders)

        for row in reader:

            if row["type"] == "polygon":
                self.totalPolygons += 1

                coords = json.loads(row["coordinates"])

                if len(coords) > self.maxPolyCoordinateCount:
                    poly = Polygon(coords)

                    result = self.reducePolygon(poly)

                    if not result["success"]:
                        # Can't easily reduce poly to fit size constraints. Convert to circle.
                        self.convertedPolygons += 1
                        self.convertPolygonToCircle(poly)
                        continue

                    poly = result["polygon"]

                    polyAreaInMeters = poly.area * self.degreeToMeterSqrd
                    if polyAreaInMeters < self.minimumPolyAreaSize:
                        self.scaledPolygons += 1
                        poly = self.scalePoly(poly)

                    row["coordinates"] = list(poly.exterior.coords)
                    row["coordinates"] = [list(coord) for coord in row["coordinates"]]  # Somehow they are tuples now...

            metadata = json.loads(row["metadata"])
            row["metadata"] = metadata

            self.csvWriter.writerow(row)

        self.csvFile.close()

    def visualize_polygons(self, polygons):
        print("Creating Leaflet and Opening Chrome for Visualization.")

        data = {"geometry": polygons}
        dataframe = gpd.GeoDataFrame(data, crs={"init": "epsg:4326"})

        m = folium.Map(zoom_start=8,
                       tiles="cartodbpositron")  # Future Improvement: Find centroid of dataset for Leaflet

        folium.GeoJson(dataframe).add_to(m)
        folium.LatLngPopup().add_to(m)

        file_path = f"folium_map.html"
        m.save(file_path)

        url = file_path
        chromePath = 'open -a /Applications/Google\ Chrome.app %s'
        webbrowser.get(chromePath).open(url)

    def reduce_polygon(self, polygon):

        # This is so ugly; sorry...
        reducedPoly = polygon.simplify(self.lowReduction)
        self.reducedPolygons[0] += 1
        if self.poly_coord_count_to_large(reducedPoly):

            reducedPoly = polygon.simplify(self.mediumReduction)
            self.reducedPolygons[0] -= 1
            self.reducedPolygons[1] += 1
            if self.poly_coord_count_to_large(reducedPoly):
                reducedPoly = polygon.simplify(self.largeReduction)

                self.reducedPolygons[1] -= 1
                self.reducedPolygons[2] += 1

                if self.poly_coord_count_to_large(reducedPoly):
                    self.reducedPolygons[2] -= 1
                    return {"success": False}

        return {"success": True, "polygon": reducedPoly}

    def convert_polygon_to_circle(self, polygon, row):

        centroid = polygon.centroid
        bounds = polygon.bounds

        degreeDiameter = max([bounds[3] - bounds[1], bounds[2] - bounds[0]])
        radius = (degreeDiameter * self.degreeToMeter) / 2

        # circle_degree_offset = self.default_circle_radius * self.meter_to_degree
        # radius = centroid.buffer(self.circle_degree_offset * 2, 2)  # I think this is a better way to get the radius but not sure about the math.

        row["radius"] = max([radius, self.defaultCircleRadius])
        row["coordinates"] = centroid

        self.csvWriter.writerow(row)

    def scale_poly(self, polygon):

        polyAreaInMeters = polygon.area * self.degreeToMeterSqrd

        scaling = self.minimumPolyAreaSize / polyAreaInMeters
        scaling = math.sqrt(scaling)
        newPolygon = affinity.scale(polygon, xfact=scaling, yfact=scaling)

        # print(f"\tPolygon Scaled->")
        # print(f"\tPolygon Area Meters: {polyAreaInMeters}")
        # print(f"\tNew Polygon Area Meters: {newPolygon.area * self.degreeToMeterSqrd}")

        return newPolygon


s = SimplifyRadarPolygons(filePath=RADAR_CSV_FILE_PATH)
s.run()
