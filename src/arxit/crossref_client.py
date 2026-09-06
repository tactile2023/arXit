from urllib.parse import quote
import httpx

CROSSREF_API_URL = ("https://api.crossref.org/works")

CROSSREF_HEADERS = {"User-Agent": "arXit/0.5"}


def fetch_doi_agency(doi: str) -> str | None:
    encoded_doi = quote(doi,safe="/")
    url = (
        f"{CROSSREF_API_URL}/"
        f"{encoded_doi}/agency"
    )

    response = httpx.get(
        url,
        headers=CROSSREF_HEADERS,
        timeout=30.0,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    agency = response.json()[
        "message"
    ]["agency"]["id"]

    return agency.lower()





def fetch_crossref_metadata(doi: str) -> dict | None:
    encoded_doi = quote(doi, safe="/")

    url = f"{CROSSREF_API_URL}/{encoded_doi}"

    response = httpx.get(url, headers=CROSSREF_HEADERS, timeout = 30.0)

    if response.status_code == 404:
        return None
    response.raise_for_status()

    return response.json()["message"]