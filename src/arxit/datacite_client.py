from urllib.parse import quote

import httpx


DATACITE_API_URL = (
    "https://api.datacite.org/dois"
)

DATACITE_HEADERS = {
    "Accept": "application/vnd.api+json",
    "User-Agent": "arXit/0.5",
}


def fetch_datacite_metadata(doi: str) -> dict | None:
    encoded_doi = quote(
        doi,
        safe="/",
    )
    url = f"{DATACITE_API_URL}/{encoded_doi}"

    response = httpx.get(
        url,
        headers=DATACITE_HEADERS,
        timeout=30.0,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()[
        "data"
    ]["attributes"]