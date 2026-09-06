import xml.etree.ElementTree as ET

from .arxiv_id import normalize_arxiv_id
from .models import ArxivMetadata


ATOM_NAMESPACE = {
    "atom": "http://www.w3.org/2005/Atom"
}


def parse_entry(entry) -> ArxivMetadata:
    link_elements = entry.findall(
        "atom:link",
        namespaces=ATOM_NAMESPACE,
    )
    pdf_url = None

    for link in link_elements:
        if link.get("title") == "pdf":
            pdf_url = link.get("href")
            break

    if pdf_url is None:
        raise ValueError(
            "arXiv entry is missing a PDF URL"
        )

    entry_id = entry.findtext(
        "atom:id",
        namespaces=ATOM_NAMESPACE,
    )
    arxiv_id = normalize_arxiv_id(entry_id)

    published = entry.findtext(
        "atom:published",
        namespaces=ATOM_NAMESPACE,
    )
    published = " ".join(published.split())

    updated = entry.findtext(
        "atom:updated",
        namespaces=ATOM_NAMESPACE,
    )
    updated = " ".join(updated.split())

    category_elements = entry.findall(
        "atom:category",
        namespaces=ATOM_NAMESPACE,
    )
    categories = [
        category.get("term")
        for category in category_elements
    ]

    author_elements = entry.findall(
        "atom:author",
        namespaces=ATOM_NAMESPACE,
    )
    authors = [
        element.findtext(
            "atom:name",
            namespaces=ATOM_NAMESPACE,
        )
        for element in author_elements
    ]

    title = entry.findtext(
        "atom:title",
        namespaces=ATOM_NAMESPACE,
    )
    title = " ".join(title.split())

    summary = entry.findtext(
        "atom:summary",
        namespaces=ATOM_NAMESPACE,
    )
    summary = " ".join(summary.split())

    return ArxivMetadata(
        title=title,
        summary=summary,
        authors=authors,
        published=published,
        updated=updated,
        categories=categories,
        arxiv_id=arxiv_id,
        pdf_url=pdf_url,
    )


def parse_arxiv_metadata_batch(
    xml_text: str,
) -> list[ArxivMetadata]:
    root = ET.fromstring(xml_text)
    entries = root.findall(
        "atom:entry",
        namespaces=ATOM_NAMESPACE,
    )

    return [
        parse_entry(entry)
        for entry in entries
    ]


def parse_arxiv_metadata(
    xml_text: str,
) -> ArxivMetadata:
    results = parse_arxiv_metadata_batch(xml_text)

    if not results:
        raise ValueError("No arXiv paper found")

    return results[0]