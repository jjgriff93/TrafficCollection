# ----------------------------------------------------------
# Utils for functions to download/upload files to blob storage
# ----------------------------------------------------------


from azure.storage.blob import BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
import logging
import json
import os


# Get environment variables
# Local dev: found in local.settings.json, Azure: Function App Settings
cities_config_url = os.environ["CITIES_CONFIG_URL"]
blob_credential = DefaultAzureCredential()


def create_container_client(url):
    """Create container client from URL to read/write blobs to Azure"""
    container_client = ContainerClient.from_container_url(
        url, credential=blob_credential
    )
    return container_client


def create_blob_client(url):
    """Create blob client from URL to read/write blobs to Azure"""
    blob_client = BlobClient.from_blob_url(url, credential=blob_credential)
    return blob_client


def get_polygonsJSON():
    """Gets JSON definition file of city polygons from Azure Blob Storage"""
    polygon_blob_client = create_blob_client(cities_config_url)

    try:
        # Download polygon JSON blob from Azure Storage
        polygons_filestream = polygon_blob_client.download_blob()
        polygons_file = polygons_filestream.readall()
        polygons_json = json.loads(polygons_file)

        assert polygons_json, "Polygons JSON should not be empty"

        return polygons_json

    except Exception as ex:
        message = "Exception while download the polygon JSON from blob."
        logging.exception(message, exc_info=ex)
        raise Exception(message, ex)


def upload_results(container_url, file_name, results):
    """Uploads JSON results to the specified city's blob container"""
    # Create blob client to output map response into
    container_client = create_container_client(container_url)
    # Instantiate a new BlobClient
    upload_blob_client = container_client.get_blob_client(file_name)

    # Upload the file
    try:
        upload_props = upload_blob_client.upload_blob(results)
        return upload_props
    except Exception as ex:
        logging.exception(f"Blob upload failed, filename: {file_name}.",
                          exc_info=ex)
    else:
        logging.info(f'Blob successfully uploaded: {file_name}')
