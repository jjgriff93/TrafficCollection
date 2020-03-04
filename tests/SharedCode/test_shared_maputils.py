from __app__.SharedCode.maputils import (
    create_polygon_from_string, get_random_coords, construct_routes_query,
    construct_tiles_query, query_maps, get_tilegrid, position_to_tile_XY,
    clip, get_map_size, position_to_global_pixel)
from shapely.geometry import Polygon, Point
import os


def test_create_polygon_from_string():
    polygon_string = "0.0 0.0,1.0 1.0,1.0 0.0,0.0 0.0"
    polygon = create_polygon_from_string(polygon_string)
    assert polygon.length == 3.4142135623730949


def test_get_random_coords():
    polygon = Polygon([(0, 0), (1, 1), (1, 0)])
    random_coords = get_random_coords(polygon)
    for coord_points in random_coords:
        coord = Point(coord_points)
        assert coord.within(polygon)


def test_contruct_routes_query(mock_keyvault):
    origin = ["0.2", "0.2"]
    destination = ["0.6", "0.6"]
    query = construct_routes_query(origin, destination)
    assert query == (
        os.environ["AZURE_MAPS_ENDPOINT"] +
        "route/directions/json?api-version=1.0&subscription-key=" +
        "kvsecret" + "&query=0.2,0.2:0.6,0.6" +
        "&traffic=true&computeTravelTimeFor=all")


def test_contruct_tiles_query(mock_keyvault):
    query = construct_tiles_query(13, 0, 1)
    assert query == (
        os.environ["AZURE_MAPS_ENDPOINT"] +
        "traffic/flow/tile/png?api-version=1.0&subscription-key=" +
        "kvsecret" + "&style=relative&zoom=13&x=0&y=1"
        "&thickness=1")


def test_query_maps(mock_response):
    result = query_maps("https://fakeatlas.microsoft.com/query")
    assert result == b'mock data from Maps API'


def test_get_tilegrid():
    polygon = Polygon([(0, 0), (1, 1), (1, 0)])
    top, bottom, left, right = get_tilegrid(polygon, 13)
    assert (top, bottom, left, right) == (4073, 4096, 4096, 4118)


def test_position_to_tile_XY():
    position = position_to_tile_XY((0, 1), 13, 256)
    assert position == (4096, 4073)


def test_clip():
    clipped = clip(1, 0, 2)
    assert clipped == 1


def test_get_map_size():
    map_size = get_map_size(13, 256)
    assert map_size == 2097152


def test_position_to_global_pixel():
    position = position_to_global_pixel((0, 1), 13, 256)
    assert position == (1048576.5, 1042750.7820010717)
