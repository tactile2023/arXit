from .crossref_client import (fetch_crossref_metadata)

from .models import (DoiCitationResult, Reference, Finding)


CROSSREF_DATE_FIELDS = (
    "published",
    "published-online",
    "published-print",
    "issued"
)


def audit_doi_citations(references: list[Reference]) -> list[Finding]:
    results = verify_doi_references(references)

    return (find_unresolved_doi_citations(results) + find_doi_year_mismatches(results))


def find_doi_year_mismatches(results: list[DoiCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        reference = result.reference
        metadata = result.metadata

        if (
            metadata is None
            or reference.year is None
        ):
            continue

        authoritative_years = (
            extract_crossref_years(metadata)
        )

        if (
            authoritative_years
            and reference.year
            not in authoritative_years
        ):
            label = reference.label or "unlabeled"
            reported_years = " or ".join(
                str(year)
                for year in sorted(
                    authoritative_years
                )
            )

            findings.append(
                Finding(
                    finding_type=(
                        "doi_year_mismatch"
                    ),
                    message=(
                        f"Reference {label} cites DOI "
                        f"{reference.doi} as "
                        f"{reference.year}, but Crossref "
                        f"reports {reported_years}."
                    ),
                    reference=reference,
                )
            )

    return findings


def extract_crossref_years(metadata: dict) -> set[int]:
    years = set()

    for field in CROSSREF_DATE_FIELDS:
        date_information = metadata.get(field, {})

        date_parts = date_information.get("date-parts", [])

        if (date_parts and date_parts[0] and isinstance(date_parts[0][0], int)):
            years.add(date_parts[0][0])
    return years



def collect_unique_dois(references: list[Reference]) -> list[str]:
    unique_dois = []
    seen_dois = set()

    for reference in references: 
        doi = reference.doi

        if (doi is not None and doi not in seen_dois):
            unique_dois.append(doi)
            seen_dois.add(doi)

    return unique_dois


def verify_doi_references(references: list[Reference]) -> list[DoiCitationResult]:
    unique_dois = collect_unique_dois(references)

    metadata_by_doi = {
        doi: fetch_crossref_metadata(doi)
        for doi in unique_dois
    }

    return [
        DoiCitationResult(
            reference=reference,
            metadata=metadata_by_doi[
                reference.doi
            ],
        )
        for reference in references
        if reference.doi is not None
    ]



def find_unresolved_doi_citations(results: list[DoiCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        if result.metadata is None:
            doi = result.reference.doi

            findings.append(
                Finding(
                    finding_type=("unresolved_doi_citation"), 
                    message=(f"DOI {doi} could not be resolved."), 
                    reference = result.reference))

    return findings