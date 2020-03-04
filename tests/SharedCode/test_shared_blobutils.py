from __app__.SharedCode.blobutils import (
    create_blob_client, get_polygonsJSON,
    upload_results)


def test_create_blob_client():
    test_url = ("https://testblobaccount.blob.core.windows.net"
                "/mycontainer/myblobpath/myblob")
    blob_client = create_blob_client(test_url)
    assert blob_client.url == test_url


def test_get_polygonsJSON(mock_blob):
    polygonsJSON = get_polygonsJSON()
    assert polygonsJSON["mock_key"] == "mock_value"


def test_upload_results(mock_blob):
    upload_props = upload_results("test", "test", "test")
    assert upload_props["mock_prop_key"] == "mock_prop_value"
