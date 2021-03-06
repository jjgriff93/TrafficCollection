from __app__ import TrafficTileGenerator
from unittest.mock import Mock
from datetime import datetime
import re


def test_random_routes_main(mock_blob, mock_response, mock_keyvault, mocker):
    req = Mock()

    mocker.patch(
        '__app__.SharedCode.blobutils.get_polygonsJSON',
        return_value=[
            {'cityId': '25', 'polygon': '0 0, 0 .1, 1 .1, 1 0, 0 0'}])

    mocker.patch(
        '__app__.TrafficTileGenerator.datetime',
        Mock(utcnow=lambda: datetime(2017, 11, 29, 14, 32, 23)))

    def verify_upload(container_url, file_name, results):
        assert (container_url ==
                'https://teststorage.invalid/tiles')
        assert re.match(
            r'cityId=25/year=2017/month=11/day=29/hour=14/minute=32'
            r'/map\.(\d+)\.(\d+)\.13\.traffic\.png', file_name)
        assert results == b'mock data from Maps API'

    m = mocker.patch(
        '__app__.SharedCode.blobutils.upload_results',
        side_effect=verify_upload)

    TrafficTileGenerator.main(req)

    assert m.call_count == 72
