import httpx
import pytest

from arxit.datacite_client import (
    fetch_datacite_metadata,
)


def test_fetch_datacite_metadata(monkeypatch):
    expected_metadata = {
        "doi": "10.48550/arxiv.1706.03762",
        "titles": [
            {
                "title": (
                    "Attention Is All You Need"
                )
            }
        ],
        "publicationYear": 2017,
    }

    def fake_get(url, headers, timeout):
        assert url == (
            "https://api.datacite.org/dois/"
            "10.48550/arxiv.1706.03762"
        )
        assert headers == {
            "Accept": "application/vnd.api+json",
            "User-Agent": "arXit/0.5",
        }
        assert timeout == 30.0

        request = httpx.Request("GET", url)

        return httpx.Response(
            200,
            json={
                "data": {
                    "attributes": expected_metadata
                }
            },
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_datacite_metadata(
        "10.48550/arxiv.1706.03762"
    )

    assert result == expected_metadata


def test_fetch_datacite_metadata_returns_none_for_404(
    monkeypatch,
):
    def fake_get(url, headers, timeout):
        request = httpx.Request("GET", url)

        return httpx.Response(
            404,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_datacite_metadata(
        "10.9999/missing"
    ) is None


def test_fetch_datacite_metadata_raises_server_error(
    monkeypatch,
):
    def fake_get(url, headers, timeout):
        request = httpx.Request("GET", url)

        return httpx.Response(
            503,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_datacite_metadata(
            "10.48550/arxiv.1706.03762"
        )