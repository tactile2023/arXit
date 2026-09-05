import arxit.doi_verifier as verifier

from arxit.doi_verifier import (verify_doi_references, audit_doi_citations, find_doi_year_mismatches, extract_crossref_years,find_unresolved_doi_citations)
from arxit.models import Reference, DoiCitationResult


def test_audit_doi_citations_combines_findings(monkeypatch):
    unresolved_reference = Reference(
        label="1",
        raw_text="Unknown paper.",
        doi="10.9999/missing",
    )
    wrong_year_reference = Reference(
        label="2",
        raw_text="Example paper. 2012.",
        year=2012,
        doi="10.1000/example",
    )

    results = [
        DoiCitationResult(
            reference=unresolved_reference,
            metadata=None,
        ),
        DoiCitationResult(
            reference=wrong_year_reference,
            metadata={
                "published": {
                    "date-parts": [[2020]]
                }
            },
        ),
    ]

    monkeypatch.setattr(
        verifier,
        "verify_doi_references",
        lambda references: results,
    )

    findings = audit_doi_citations(
        [
            unresolved_reference,
            wrong_year_reference,
        ]
    )

    assert [
        finding.finding_type
        for finding in findings] == [
        "unresolved_doi_citation",
        "doi_year_mismatch",
    ]






def test_find_doi_year_mismatch():
    reference = Reference(
        label="4",
        raw_text="Example Paper. 2012.",
        year=2012,
        doi="10.1000/example",
    )

    results = [
        DoiCitationResult(
            reference=reference,
            metadata={
                "published-online": {
                    "date-parts": [[2020, 12, 15]]
                },
                "published-print": {
                    "date-parts": [[2021, 1]]
                },
            },
        )
    ]

    findings = find_doi_year_mismatches(results)

    assert len(findings) == 1
    assert findings[0].finding_type == (
        "doi_year_mismatch"
    )
    assert findings[0].message == (
        "Reference 4 cites DOI 10.1000/example "
        "as 2012, but Crossref reports 2020 or 2021."
    )


def test_doi_online_year_creates_no_finding():
    reference = Reference(
        label="4",
        raw_text="Example Paper. 2020.",
        year=2020,
        doi="10.1000/example",
    )

    results = [
        DoiCitationResult(
            reference=reference,
            metadata={
                "published-online": {
                    "date-parts": [[2020]]
                },
                "published-print": {
                    "date-parts": [[2021]]
                },
            },
        )
    ]

    assert find_doi_year_mismatches(results) == []




def test_extract_crossref_years():
    metadata = {
        "published-online": {
            "date-parts": [[2020, 12, 15]]
        },
        "published-print": {
            "date-parts": [[2021, 1]]
        },
    }

    assert extract_crossref_years(metadata) == {
        2020,
        2021,
    }


def test_extract_crossref_years_ignores_missing_dates():
    metadata = {
        "title": ["Example Paper"],
    }

    assert extract_crossref_years(metadata) == set()






def test_find_unresolved_doi_citations():
    reference = Reference(
        label="8",
        raw_text="Unknown paper. doi:10.9999/missing.",
        doi="10.9999/missing",
    )

    results = [
        DoiCitationResult(
            reference=reference,
            metadata=None
        )
    ]

    findings = find_unresolved_doi_citations(results)

    assert len(findings) == 1
    assert findings[0].finding_type == ("unresolved_doi_citation")
    assert findings[0].message == ("DOI 10.9999/missing could not be resolved.")
    assert findings[0].reference == reference


def test_resolved_doi_creates_no_unresolved_finding():
    reference = Reference(
        label="8",
        raw_text="Example paper.",
        doi="10.1000/example",
    )

    results = [
        DoiCitationResult(
            reference=reference,
            metadata={
                "DOI": "10.1000/example",
                "title": ["Example Paper"],
            },
        )
    ]

    assert find_unresolved_doi_citations(results) == []



def test_verify_doi_references_deduplicates_requests(monkeypatch):
    first_reference = Reference(
        label="1",
        raw_text="First occurrence.",
        doi="10.1000/example",
    )
    repeated_reference = Reference(
        label="2",
        raw_text="Repeated occurrence.",
        doi="10.1000/example",
    )
    missing_reference = Reference(
        label="3",
        raw_text="Missing DOI.",
        doi="10.9999/missing",
    )

    requested_dois = []

    def fake_fetch(doi):
        requested_dois.append(doi)

        if doi == "10.1000/example":
            return {
                "DOI": doi,
                "title": ["Example Paper"],
            }

        return None

    monkeypatch.setattr(
        verifier,
        "fetch_crossref_metadata",
        fake_fetch,
    )

    results = verify_doi_references(
        [
            first_reference,
            repeated_reference,
            missing_reference,
        ]
    )

    assert requested_dois == [
        "10.1000/example",
        "10.9999/missing",
    ]

    assert len(results) == 3
    assert results[0].metadata is not None
    assert results[1].metadata is not None
    assert results[2].metadata is None


def test_verify_doi_references_skips_references_without_doi(
    monkeypatch,
):
    reference = Reference(
        label="1",
        raw_text="No DOI here.",
    )

    def fail_if_called(doi):
        raise AssertionError(
            "Crossref should not be called"
        )

    monkeypatch.setattr(
        verifier,
        "fetch_crossref_metadata",
        fail_if_called,
    )

    assert verify_doi_references([reference]) == []