# --------------------------------------------------------------
# Gets city polygons from blob storage account and iterates through
#
# Downloads map and traffic tiles for cities and saves to blob
#
# Connection strings in Function App Settings, timing config in function.json
# --------------------------------------------------------------

import logging
import os
import azure.functions as func
from datetime import datetime
from __app__.SharedCode import maputils, blobutils


def main(mytimer: func.TimerRequest) -> None:
    """Main method triggered by CRON time trigger"""
    logging.info("TrafficTileGenerator function initialised.")

    # Call blob storage to get city polygon definitions from stored JSON file
    polygons_json = blobutils.get_polygonsJSON()
    logging.info("Retrieved polygon JSON from blob storage.")

    # existing blob container for saving outputs
    container_url = os.environ["TRAFFICTILES_OUTPUT_URL"]

    # Specify zoom level for the tile grid
    zoom = 13

    # Iterate through the JSON array for each city
    for polygons_count, city_polygon in enumerate(polygons_json):
        try:
            # Get polygon for the city
            city_id = city_polygon['cityId']
            assert city_id, ("'cityId' field empty/not found in array"
                             f"[{polygons_count}] in polygons JSON")

            polygon_string = city_polygon['polygon']
            assert polygon_string, ("City 'polygon' field empty/not in array"
                                    f"[{polygons_count}] in polygons JSON")

            logging.info(f"Generating tile grid for CityID {city_id}")

            # Get a Shapely polygon object for the polygon string
            polygon = maputils.create_polygon_from_string(polygon_string)

            # Get tile grid positions for city bounding box area
            top, bottom, left, right = maputils.get_tilegrid(polygon, zoom)

            for tileX in range(left, right+1):
                for tileY in range(top, bottom+1):
                    # Construct tile query
                    query = maputils.construct_tiles_query(zoom, tileX, tileY)
                    logging.info(f"Calling Maps to generate traffic tile, "
                                 f"X:{tileX} Y:{tileY} Zoom:{zoom}")
                    # Query Azure Maps API
                    file = maputils.query_maps(query)
                    # Save result to blob with datetime values as folder path
                    dt = datetime.utcnow().timetuple()
                    file_name = (f"cityId={city_id}/year={dt[0]}/month={dt[1]}"
                                 f"/day={dt[2]}/hour={dt[3]}/minute={dt[4]}/"
                                 f"map.{tileX}.{tileY}.{zoom}.traffic.png")
                    # Upload the tile to blob storage
                    blobutils.upload_results(container_url, file_name, file)

        except Exception as ex:
            logging.exception(ex)
            raise
        else:
            logging.info(f"Tiles for CityID {city_id} successfully queried"
                         " & results uploaded to blob storage")
