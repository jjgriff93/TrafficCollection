import pytest
import requests
import json
from azure.storage.blob import BlobClient, ContainerClient
from azure.keyvault.secrets import SecretClient


class MockResponse:
    @staticmethod
    def raise_for_status():
        return None
    content = b'mock data from Maps API'


class MockBlobClient:
    def __init__(self, blob_url):
        self.blob_url = blob_url

    def download_blob(self):
        return MockStorageStreamDownloader()

    def upload_blob(self, results):
        return {"mock_prop_key": "mock_prop_value"}


class MockStorageStreamDownloader:
    @staticmethod
    def readall():
        json_file = json.dumps({"mock_key": "mock_value"})
        return json_file


class MockContainerClient:
    def __init__(self, container_url):
        self.container_url = container_url

    def get_blob_client(self, url):
        return MockBlobClient(url)


@pytest.fixture
def mock_response(monkeypatch):
    """Requests.get() mocked to return {'mock_key':'mock_response'}."""
    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture
def mock_blob(monkeypatch):
    """BlobServiceClient(blob_url) mocked to create mock blob class"""
    def mock_get_blob_client(blob_url, *args, **kwargs):
        return MockBlobClient(blob_url)

    def mock_get_container_client(container_url, *args, **kwargs):
        return MockContainerClient(container_url)

    monkeypatch.setattr(BlobClient, "from_blob_url",
                        mock_get_blob_client)

    monkeypatch.setattr(ContainerClient, "from_container_url",
                        mock_get_container_client)


class MockSecret:
    def __init__(self, value):
        self.value = value

    def value(self):
        return self.value


@pytest.fixture
def mock_keyvault(monkeypatch):
    def mock_secret(container_url, *args, **kwargs):
        return MockSecret("kvsecret")

    monkeypatch.setattr(SecretClient, "get_secret",
                        mock_secret)
