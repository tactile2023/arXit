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



def fetch_arxiv_search_xml(
    search_query: str,
    max_results: int = 75,
    start: int = 0,
    sort_order: str = "descending") -> str:

    
    if not search_query.strip():
        raise ValueError(
            "Search query cannot be empty"
        )

    if max_results <= 0:
        raise ValueError(
            "max_results must be positive"
        )

    if start < 0:
        raise ValueError(
            "start cannot be negative"
        )

    if sort_order not in {
        "ascending",
        "descending",
    }:
        raise ValueError(
            "sort_order must be ascending "
            "or descending"
        )

    response = httpx.get(
        ARXIV_API_URL,
        params={
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": sort_order,
        },
        timeout=60.0,
    )
    response.raise_for_status()

    return response.text