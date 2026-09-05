import argparse
import httpx
from .arxiv_client import fetch_arxiv_metadata_xml
from .arxiv_parser import parse_arxiv_metadata
from .arxiv_id import normalize_arxiv_id
from pypdf.errors import PdfReadError

from .models import ParsedPaper
from .pdf_downloader import download_pdf
from .pdf_parser import parse_pdf
from .section_extractor import extract_sections
from .reference_extractor import extract_references
from .citation_verifier import audit_arxiv_citations
from.doi_verifier import audit_doi_citations







def build_parser():
    parser = argparse.ArgumentParser(
        prog="arxit",
        description="Audit machine-learning papers on arXiv.",
    )

    parser.add_argument("paper", help="An arXiv URL or identifier.",)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:    
        arxiv_id = normalize_arxiv_id(args.paper)
        xml_text = fetch_arxiv_metadata_xml(arxiv_id)
        metadata = parse_arxiv_metadata(xml_text)

        pdf_bytes = download_pdf(metadata.pdf_url)
        pages = parse_pdf(pdf_bytes)
        sections = extract_sections(pages)

        


        references = extract_references(sections)

        paper = ParsedPaper(
            metadata=metadata,
            pages=pages,
            sections=sections,
            references=references
        )
        arxiv_findings = (audit_arxiv_citations(paper.references))
        doi_findings = audit_doi_citations(paper.references)
        citation_findings = (arxiv_findings + doi_findings)

    except ValueError as e:
        parser.error(str(e))

    except httpx.HTTPStatusError as e:
        if e.response.status_code ==429:
            parser.error(
                "arXiv rate limit reached. "
                "Wait before trying again."
            )
        parser.error(f"Coult not retrieve arXiv metadata: {e}")

    except httpx.HTTPError as e:
        parser.error(f"Could not retrieve arXiv metadata: {e}")

    except PdfReadError as e:
        parser.error(f"Could not parse PDF: {e}")


    character_count = sum(len(page.text) for page in paper.pages)



        
    print(f"arXiv ID: {metadata.arxiv_id}")
    print(f"Title: {metadata.title}")
    print(f"Authors: {', '.join(metadata.authors)}")
    print(f"Published: {metadata.published}")
    print(f"PDF: {metadata.pdf_url}")
    print(f"Pages parsed: {len(paper.pages)}")
    print(f"Characters extracted: {character_count}")
    print(f"Sections found: {len(paper.sections)}")

    for section in paper.sections:
        print(
            f"  {section.title} "
            f"(pages {section.start_page}-{section.end_page})"
        )

    print(f"References found: {len(paper.references)}")

    for reference in paper.references:
        if reference.label is not None:
            prefix = f"[{reference.label}]"
        else:
            prefix = "-"

        print(f"  {prefix} {reference.raw_text}")


    print(
        f"Citation findings: "
        f"{len(citation_findings)}")

    for finding in citation_findings:
        print(
            f"  [{finding.finding_type}] "
            f"{finding.message}"
        ) 

