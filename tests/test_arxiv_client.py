import httpx
import pytest
from arxit.arxiv_client import fetch_arxiv_metadata_xml, fetch_arxiv_metadata_batch_xml



def test_fetch_arxiv_metadata_batch_xml(monkeypatch):
    expected_xml = "<feed>multiple entries</feed>"

    def fake_get(url, params, timeout):
        assert url == "https://export.arxiv.org/api/query"
        assert params == {
            "id_list": "1302.4389,1706.03762,1810.04805",
            "max_results": 3
        }
        assert timeout == 30.0

        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            text=expected_xml,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_arxiv_metadata_batch_xml(
        [
            "1302.4389",
            "1706.03762",
            "1810.04805",
        ]
    )

    assert result == expected_xml


    def test_fetch_arxiv_metadata_batch_rejects_empty_list():
    
        with pytest.raises(
            ValueError,
            match="At least one arXiv ID is required",
        ):
            fetch_arxiv_metadata_batch_xml([])





def test_fetch_arxiv_metadata_xml(monkeypatch):
    expected_xml = "<feed>example response</feed>"

    def fake_get(url, params, timeout):
        assert url == "https://export.arxiv.org/api/query"
        assert params == {"id_list": "1706.03762", "max_results": 1}
        assert timeout == 30.0

        request = httpx.Request("GET", url)
        return httpx.Response(200, text=expected_xml, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_arxiv_metadata_xml("1706.03762")

    assert result == expected_xml


def test_fetch_raises_for_server_error(monkeypatch):
    def fake_get(url, params, timeout):
        request = httpx.Request("GET", url)
        return httpx.Response(
            503,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_arxiv_metadata_xml("1706.03762")
