import httpx
import pytest

from arxit.crossref_client import (
    fetch_crossref_metadata,
    fetch_doi_agency
)


def test_fetch_doi_agency_for_crossref(monkeypatch):
    def fake_get(url, headers, timeout):
        assert url == (
            "https://api.crossref.org/works/"
            "10.1038/example/agency"
        )

        request = httpx.Request("GET", url)

        return httpx.Response(
            200,
            json={
                "message": {
                    "DOI": "10.1038/example",
                    "agency": {
                        "id": "crossref",
                        "label": "Crossref",
                    },
                }
            },
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_doi_agency("10.1038/example") == "crossref"


def test_fetch_doi_agency_for_datacite(
    monkeypatch,
):
    def fake_get(url, headers, timeout):
        request = httpx.Request("GET", url)

        return httpx.Response(
            200,
            json={
                "message": {
                    "DOI": "10.48550/arxiv.1706.03762",
                    "agency": {
                        "id": "datacite",
                        "label": "DataCite",
                    },
                }
            },
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_doi_agency(
        "10.48550/arxiv.1706.03762"
    ) == "datacite"


def test_fetch_doi_agency_returns_none_for_404(monkeypatch):
    def fake_get(url, headers, timeout):
        request = httpx.Request("GET", url)

        return httpx.Response(
            404,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_doi_agency("10.9999/missing") is None



def test_fetch_crossref_metadata(monkeypatch):
    expected_metadata = {
        "DOI": "10.1038/s41586-021-03819-2",
        "title": ["Example Paper"],
        "published": {
            "date-parts": [[2021]]
        },
    }

    def fake_get(url, headers, timeout):
        assert url == (
            "https://api.crossref.org/works/"
            "10.1038/s41586-021-03819-2"
        )
        assert headers == {
            "User-Agent": "arXit/0.5"
        }
        assert timeout == 30.0

        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={"message": expected_metadata},
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_crossref_metadata(
        "10.1038/s41586-021-03819-2"
    )

    assert result == expected_metadata


def test_fetch_crossref_metadata_returns_none_for_404(
    monkeypatch,
):
    def fake_get(url, headers, timeout):
        request = httpx.Request("GET", url)

        return httpx.Response(
            404,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    assert fetch_crossref_metadata(
        "10.9999/nonexistent"
    ) is None


def test_fetch_crossref_metadata_raises_server_error(monkeypatch):
    def fake_get(url, headers, timeout):
        request = httpx.Request("GET", url)

        return httpx.Response(
            503,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_crossref_metadata(
            "10.1038/s41586-021-03819-2"
        )