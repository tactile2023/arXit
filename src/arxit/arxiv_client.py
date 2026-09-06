import httpx

ARXIV_API_URL = "https://export.arxiv.org/api/query"


def fetch_arxiv_metadata_batch_xml(arxiv_ids: list[str]) -> str:
    if not arxiv_ids:
        raise ValueError("At least one arXiv ID is required")

    response = httpx.get(
        ARXIV_API_URL,
        params={
            "id_list": ",".join(arxiv_ids), 
            "max_results": len(arxiv_ids)
            },
        timeout=30.0,
    )
    response.raise_for_status()

    return response.text

def fetch_arxiv_metadata_xml(arxiv_id: str) -> str:
    return fetch_arxiv_metadata_batch_xml([arxiv_id])