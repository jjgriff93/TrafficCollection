# ----------------------------------------------------------
# Call the Azure Maps GET route destinations API
# Input : Array of coordinates (mix of origins & destinations)
# Output : Json of route directions
# ----------------------------------------------------------


from shapely.geometry import Point
from shapely import wkt
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
import numpy as np
import logging
import requests
import os
import math


# Get environment variables
# Local dev: found in local.settings.json, Azure: Function App Settings
key_vault_uri = os.environ["KEY_VAULT"]
maps_endpoint = os.environ["AZURE_MAPS_ENDPOINT"]
num_of_routes_to_calc = os.environ["NUM_OF_ROUTES_PER_CITY"]

# Constants for map tile download methods
earth_radius = 6378137
min_latitude = -85.05112878
max_latitude = 85.05112878
min_longitude = -180
max_longitude = 180
tile_size = 256


def get_maps_subscription_key():
    """Retrieves Azure Maps key secret from Key Vault"""
    credential = ManagedIdentityCredential()
    client = SecretClient(vault_url=key_vault_uri, credential=credential)
    try:
        maps_key = client.get_secret("mapskey").value
        return maps_key
    except Exception as ex:
        message = "Could not get Key Vault secret"
        logging.error(message, exc_info=ex)
        raise Exception(message, ex)


def create_polygon_from_string(string_to_convert):
    return wkt.loads(f"POLYGON(({string_to_convert}))")


def get_random_coords(city_polygon):
    """Generates configured no of random coordinates within city polygon"""
    # Get number to calculate from environment config
    num_points_to_calc = int(num_of_routes_to_calc) * 2

    min_lat, min_long, max_lat, max_long = city_polygon.bounds

    random_coordinates_list = []

    while len(random_coordinates_list) < num_points_to_calc:
        # Generate a random coordinate within polygon
        random_coordinate = Point([
            np.random.uniform(min_lat, max_lat),
            np.random.uniform(min_long, max_long)
        ])
        # If the generated coordinate is within the polygon, add it to the list
        if (random_coordinate.within(city_polygon)):
            random_coordinates_list.append(
                [random_coordinate.x, random_coordinate.y]
            )

    return random_coordinates_list


def construct_routes_query(origin, destination):
    """Create a maps routes API query from the coordinates"""
    url = (maps_endpoint
           + "route/directions/json?api-version=1.0&subscription-key="
           + get_maps_subscription_key())

    query = (f"{url}&query={str(origin[0])},"
             f"{str(origin[1])}:{str(destination[0])},{str(destination[1])}"
             "&traffic=true&computeTravelTimeFor=all")

    return query


def construct_tiles_query(zoom, tileX, tileY):
    """Create a maps query for Traffic Tiles API"""
    url = (maps_endpoint
           + "traffic/flow/tile/png?api-version=1.0&subscription-key="
           + get_maps_subscription_key())

    query = (f"{url}&style=relative&zoom={zoom}&x={tileX}&y={tileY}"
             "&thickness=1")

    return query


def query_maps(query):
    """Calls Azure Maps with defined query and returns payload"""
    try:
        response = requests.get(query)
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error calling Maps: {e}")


def get_tilegrid(polygon, zoom):
    """Converts geo polygon to pixel tile grid and get bounding tiles"""
    bottom, left, top, right = polygon.bounds
    top_left_tile = position_to_tile_XY((left, top), zoom, tile_size)
    bottom_right_tile = position_to_tile_XY((right, bottom), zoom, tile_size)
    top_tile = top_left_tile[1]
    bottom_tile = bottom_right_tile[1]
    left_tile = top_left_tile[0]
    right_tile = bottom_right_tile[0]

    return top_tile, bottom_tile, left_tile, right_tile


def position_to_tile_XY(position, zoom, tile_size):
    """Calculates XY tile coords that a coordinate falls in for zoom level."""
    latitude = clip(position[1], min_latitude, max_latitude)
    longitude = clip(position[0], min_longitude, max_longitude)

    # Adapted to Python from
    # https://docs.microsoft.com/en-gb/azure/azure-maps/zoom-levels-and-tile-grid
    x = (longitude + 180) / 360
    sin_latitude = math.sin(latitude * math.pi / 180)
    y = 0.5 - math.log((1 + sin_latitude) / (1 - sin_latitude)) / (4 * math.pi)

    map_size = get_map_size(zoom, tile_size)

    return (
        math.floor(clip(x * map_size + 0.5, 0, map_size - 1) / tile_size),
        math.floor(clip(y * map_size + 0.5, 0, map_size - 1) / tile_size)
    )


def clip(n, min_value, max_value):
    """Clips a number to the specified minimum and maximum values."""
    return min(max(n, min_value), max_value)


def get_map_size(zoom, tile_size):
    """Get map size in pixels from current zoom level and tile size"""
    return math.ceil(tile_size * math.pow(2, zoom))


def position_to_global_pixel(position, zoom, tile_size):
    """Converts lat/long coordinates (in degrees) into pixel XY coordinates"""
    latitude = clip(position[1], min_latitude, max_latitude)
    longitude = clip(position[0], min_longitude, max_longitude)

    # Calculate the pixel XY coordinates of the tiles from geo coordinates
    x = (longitude + 180) / 360
    sin_latitude = math.sin(latitude * math.pi / 180)
    y = 0.5 - math.log((1 + sin_latitude) / (1 - sin_latitude)) / (4 * math.pi)

    map_size = get_map_size(zoom, tile_size)

    return (
        clip(x * map_size + 0.5, 0, map_size - 1),
        clip(y * map_size + 0.5, 0, map_size - 1)
    )
