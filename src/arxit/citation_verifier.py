from .models import Reference
import re
from .arxiv_client import (fetch_arxiv_metadata_batch_xml)
from .arxiv_parser import (parse_arxiv_metadata_batch)

from .models import ArxivMetadata, Reference, ArxivCitationResult, Finding
from .title_matcher import is_title_mismatch




DEFAULT_ARXIV_BATCH_SIZE = 50


def find_arxiv_title_mismatches(results: list[ArxivCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        reference = result.reference
        metadata = result.metadata

        if metadata is None:
            continue

        if is_title_mismatch(
            metadata.title,
            reference.raw_text,
        ):
            label = reference.label or "unlabeled"

            findings.append(
                Finding(
                    finding_type=(
                        "arxiv_title_mismatch"
                    ),
                    message=(
                        f"Reference {label} may contain "
                        f"the wrong title for arXiv ID "
                        f"{reference.arxiv_id}. "
                        f"arXiv reports: "
                        f"{metadata.title}."
                    ),
                    reference=reference,
                )
            )

    return findings





def chunk_arxiv_ids(arxiv_ids: list[str], batch_size: int = DEFAULT_ARXIV_BATCH_SIZE) -> list[list[str]]:
    if batch_size <= 0:
        raise ValueError("Batch size must be positive")


    return [arxiv_ids[index:index + batch_size]
        for index in range(0, len(arxiv_ids), batch_size)

            ]



def audit_arxiv_citations(references: list[Reference]) -> list[Finding]:
    results = verify_arxiv_references(references)

    findings = find_unresolved_arxiv_citations(results) + find_year_mismatches(results) + find_arxiv_title_mismatches(results)

    return findings




def find_year_mismatches(results: list[ArxivCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        reference = result.reference
        metadata = result.metadata

        if (metadata is None or reference.year is None):
            continue

        authoritative_year = int(metadata.published[:4])

        if reference.year != authoritative_year:
            label = reference.label or "unlabeled"

            findings.append(
                Finding(
                    finding_type=(
                        "arxiv_year_mismatch"
                    ),
                    message=(
                        f"Reference {label} cites arXiv ID "
                        f"{reference.arxiv_id} as "
                        f"{reference.year}, but arXiv "
                        f"reports {authoritative_year}."
                    ),
                    reference=reference,
                )
            )

    return findings



def find_unresolved_arxiv_citations(
    results: list[ArxivCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        if result.metadata is None:
            arxiv_id = result.reference.arxiv_id

            findings.append(
                Finding(
                    finding_type=(
                        "unresolved_arxiv_citation"
                    ),
                    message=(
                        f"arXiv ID {arxiv_id} "
                        "could not be resolved."
                    ),
                    reference=result.reference,
                )
            )

    return findings




def remove_arxiv_version(arxiv_id: str) -> str:
    return re.sub(
        r"v\d+$",
        "",
        arxiv_id,
        flags=re.IGNORECASE,
    )


def match_reference_metadata(
    references: list[Reference],
    metadata_items: list[ArxivMetadata],
) -> list[ArxivCitationResult]:
    metadata_by_id = {
        remove_arxiv_version(metadata.arxiv_id):
        metadata
        for metadata in metadata_items
    }

    results = []

    for reference in references:
        if reference.arxiv_id is None:
            continue

        base_id = remove_arxiv_version(
            reference.arxiv_id
        )

        results.append(
            ArxivCitationResult(
                reference=reference,
                metadata=metadata_by_id.get(base_id),
            )
        )

    return results


def verify_arxiv_references(references: list[Reference]) -> list[ArxivCitationResult]:
    metadata_items = fetch_reference_metadata(references)

    return match_reference_metadata(references, metadata_items)



def collect_unique_arxiv_ids(references: list[Reference]) -> list[str]:
    unique_ids = []
    seen_ids = set()

    for reference in references:
        arxiv_id = reference.arxiv_id

        if(arxiv_id is not None and arxiv_id not in seen_ids):
            unique_ids.append(arxiv_id)
            seen_ids.add(arxiv_id)

    return unique_ids


def fetch_reference_metadata(references: list[Reference], batch_size: int = DEFAULT_ARXIV_BATCH_SIZE) -> list[ArxivMetadata]:
    arxiv_ids = collect_unique_arxiv_ids(references)

    if not arxiv_ids:
        return []

    metadata_items = []

    for batch in chunk_arxiv_ids(arxiv_ids,batch_size=batch_size):
        xml_text = (fetch_arxiv_metadata_batch_xml(batch))
        batch_metadata = (parse_arxiv_metadata_batch(xml_text))
        metadata_items.extend(batch_metadata)

    return metadata_items