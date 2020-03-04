# --------------------------------------------------------------
# Send configured num of random routes itinerary to generate route directions
#
# Gets city polygons from blob storage account and iterates through
#
# Connection strings in Function App Settings, timing config in function.json
# --------------------------------------------------------------

import logging
import os
import gzip
import azure.functions as func
from datetime import datetime
from __app__.SharedCode import blobutils, maputils


def main(mytimer: func.TimerRequest) -> None:
    """Main method triggered by CRON time trigger"""
    logging.info("RandomRouteGenerator function initialised.")

    # Call blob storage to get city polygon definitions from stored JSON file
    polygons_json = blobutils.get_polygonsJSON()
    logging.info(f"Retrieved polygon JSON from blob storage")

    # existing blob container for saving outputs
    container_url = os.environ["TRAFFICROUTES_OUTPUT_URL"]

    # Iterate through JSON array and get random coordinates for each city
    for polygons_count, city_polygon in enumerate(polygons_json):
        try:
            # Get polygon for the city
            city_id = city_polygon['cityId']
            assert city_id, ("'cityId' field empty/not found in array"
                             f"[{polygons_count}] in polygons JSON")

            polygon_string = city_polygon['polygon']
            assert polygon_string, ("City 'polygon' field empty/not in array"
                                    f" [{polygons_count}] in polygons JSON")

            # Call method to convert polygon string to Shapely polygon object
            logging.info(f"Generating random coordinates for CityID {city_id}")
            polygon = maputils.create_polygon_from_string(polygon_string)
            assert polygon, "Valid polygon should be in city polygon string"

            # Get random routes within polygon
            random_coords = maputils.get_random_coords(polygon)

            # Send random routes to Azure Maps to get the calculation data
            blob_count = 1
            for origin, dest in zip(
                    random_coords[0::2], random_coords[1::2]):
                # Construct an API request with route to query
                query = maputils.construct_routes_query(origin, dest)
                # Query Azure Maps API
                file = maputils.query_maps(query)
                # Save result to blob with datetime values as folder path
                dt = datetime.utcnow().timetuple()
                file_name = (f"cityId={city_id}/year={dt[0]}/month={dt[1]}/"
                             f"day={dt[2]}/hour={dt[3]}/minute={dt[4]}/"
                             f"{blob_count}.json.gz")
                # Output the JSON result to blob
                if file:
                    gzipped = gzip.compress(file)
                    blobutils.upload_results(container_url, file_name, gzipped)
                    blob_count += 1
                else:
                    logging.error("Response from Maps empty. Skipping upload.")

        except Exception as ex:
            logging.exception(ex)
            raise
        else:
            logging.info(f"Random routes for CityID {city_id} successfully"
                         " queried & results uploaded to blob storage")
