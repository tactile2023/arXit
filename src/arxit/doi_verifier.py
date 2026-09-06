from .crossref_client import (fetch_crossref_metadata, fetch_doi_agency)
from .title_matcher import is_title_mismatch
from .datacite_client import fetch_datacite_metadata
from .models import (DoiCitationResult, Reference, Finding)
import httpx

CROSSREF_DATE_FIELDS = (
    "published",
    "published-online",
    "published-print",
    "issued"
)


def extract_doi_years(metadata: dict, agency: str | None) -> set[int]:
    if agency == "datacite":
        publication_year = metadata.get(
            "publicationYear"
        )

        if isinstance(publication_year, int):
            return {publication_year}

        if (
            isinstance(publication_year, str)
            and publication_year.isdigit()
        ):
            return {int(publication_year)}

        return set()

    return extract_crossref_years(metadata)




def fetch_metadata_for_doi(doi: str,agency: str | None) -> dict | None:
    if agency == "crossref":
        return fetch_crossref_metadata(doi)

    if agency == "datacite":
        return fetch_datacite_metadata(doi)

    return None


def extract_doi_title(metadata: dict, agency: str | None) -> str | None:
    if agency == "datacite":
        titles = metadata.get("titles", [])

        if titles and isinstance(titles[0], dict):
            title = titles[0].get("title")

            if isinstance(title, str) and title.strip():
                return title.strip()

        return None

    titles = metadata.get("title", [])

    if titles and isinstance(titles[0], str):
        title = titles[0].strip()

        if title:
            return title

    return None





def find_doi_title_mismatches(results: list[DoiCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        reference = result.reference
        metadata = result.metadata

        if metadata is None:
            continue

        authoritative_title = extract_doi_title(
            metadata,
            result.agency,
        )

        if authoritative_title is None:
            continue

        agency_name = (
            "DataCite"
            if result.agency == "datacite"
            else "Crossref"
        )

        if is_title_mismatch(
            authoritative_title,
            reference.raw_text,
        ):
            label = reference.label or "unlabeled"

            findings.append(
                Finding(
                    finding_type="doi_title_mismatch",
                    message=(
                        f"Reference {label} may contain "
                        f"the wrong title for DOI "
                        f"{reference.doi}. "
                        f"{agency_name} reports: "
                        f"{authoritative_title}."
                    ),
                    reference=reference,
                )
            )

    return findings



def find_doi_verification_errors(results: list[DoiCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        if result.error is None:
            continue

        reference = result.reference
        label = reference.label or "unlabeled"

        if result.agency == "crossref":
            service_name = "Crossref"
        elif result.agency == "datacite":
            service_name = "DataCite"
        else:
            service_name = "DOI registry"

        findings.append(
            Finding(
                finding_type="doi_verification_error",
                message=(
                    f"Reference {label} could not be "
                    f"verified because {service_name} "
                    f"returned an error: "
                    f"{result.error}."
                ),
                reference=reference,
            )
        )

    return findings







def audit_doi_citations(references: list[Reference]) -> list[Finding]:
    results = verify_doi_references(references)

    return (find_unresolved_doi_citations(results) + find_doi_year_mismatches(results) + find_doi_title_mismatches(results) + find_doi_verification_errors(results))


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

        authoritative_years = extract_doi_years(
            metadata, result.agency
        )

        if (
            authoritative_years
            and reference.year
            not in authoritative_years):
            label = reference.label or "unlabeled"
            reported_years = " or ".join(
                str(year)
                for year in sorted(
                    authoritative_years
                )
            )

            agency_name = (
                "DataCite"
                if result.agency == "datacite"
                else "Crossref"
            )
        

            findings.append(
                Finding(
                    finding_type=(
                        "doi_year_mismatch"
                    ),
                    message=(
                        f"Reference {label} cites DOI "
                        f"{reference.doi} as "
                        f"{reference.year}, but "
                        f"{agency_name} reports "
                        f"{reported_years}."
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

    agencies_by_doi = {}
    metadata_by_doi = {}
    errors_by_doi = {}

    for doi in unique_dois:
        agency = None
        metadata = None
        error = None

        try:
            agency = fetch_doi_agency(doi)
            metadata = fetch_metadata_for_doi(
                doi,
                agency,
            )
        except httpx.HTTPError as exc:
            error = str(exc)

        agencies_by_doi[doi] = agency
        metadata_by_doi[doi] = metadata
        errors_by_doi[doi] = error

    return [
        DoiCitationResult(
            reference=reference,
            metadata=metadata_by_doi[
                reference.doi
            ],
            agency=agencies_by_doi[
                reference.doi
            ],
            error=errors_by_doi[
                reference.doi
            ],
        )
        for reference in references
        if reference.doi is not None
    ]


def find_unresolved_doi_citations(results: list[DoiCitationResult]) -> list[Finding]:
    findings = []

    for result in results:
        if result.agency is None and result.metadata is None and result.error is None:
            doi = result.reference.doi

            findings.append(
                Finding(
                    finding_type=("unresolved_doi_citation"), 
                    message=(f"DOI {doi} could not be resolved."), 
                    reference = result.reference))

    return findings