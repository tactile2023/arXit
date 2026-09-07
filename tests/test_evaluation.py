import arxit.evaluation as evaluation
import httpx
from arxit.models import (
    ArxivMetadata,
    PaperSection,
    ParsedPage,
    Reference,
)


def test_select_corpus_round_robins_and_deduplicates():
    metadata_groups = [
        [
            ArxivMetadata(
                title="First ML Paper",
                summary="",
                authors=[],
                published="2020-01-01T00:00:00Z",
                updated="2020-01-01T00:00:00Z",
                categories=["cs.LG"],
                arxiv_id="2001.00001v2",
                pdf_url="https://arxiv.org/pdf/2001.00001v2",
            ),
            ArxivMetadata(
                title="Second ML Paper",
                summary="",
                authors=[],
                published="2020-01-01T00:00:00Z",
                updated="2020-01-01T00:00:00Z",
                categories=["cs.LG"],
                arxiv_id="2001.00002v1",
                pdf_url="https://arxiv.org/pdf/2001.00002v1",
            ),
        ],
        [
            ArxivMetadata(
                title="Duplicate Paper",
                summary="",
                authors=[],
                published="2020-01-01T00:00:00Z",
                updated="2020-01-01T00:00:00Z",
                categories=["cs.CL"],
                arxiv_id="2001.00001v3",
                pdf_url="https://arxiv.org/pdf/2001.00001v3",
            ),
            ArxivMetadata(
                title="Language Paper",
                summary="",
                authors=[],
                published="2020-01-01T00:00:00Z",
                updated="2020-01-01T00:00:00Z",
                categories=["cs.CL"],
                arxiv_id="2001.00003v1",
                pdf_url="https://arxiv.org/pdf/2001.00003v1",
            ),
        ],
        [
            ArxivMetadata(
                title="Vision Paper",
                summary="",
                authors=[],
                published="2020-01-01T00:00:00Z",
                updated="2020-01-01T00:00:00Z",
                categories=["cs.CV"],
                arxiv_id="2001.00004v1",
                pdf_url="https://arxiv.org/pdf/2001.00004v1",
            ),
        ],
    ]

    selected_ids = evaluation.select_corpus(
        metadata_groups,
        target_size=4,
    )

    assert selected_ids == [
        "2001.00001",
        "2001.00004",
        "2001.00002",
        "2001.00003",
    ]
    



def test_summarize_results_calculates_metrics():
    results = [
        evaluation.PaperEvaluationResult(
            arxiv_id="2401.00001",
            title="First Paper",
            status="success",
            page_count=10,
            character_count=1000,
            section_count=5,
            reference_count=20,
            has_reference_section=True,
            elapsed_seconds=1.0,
            failure_stage=None,
        ),
        evaluation.PaperEvaluationResult(
            arxiv_id="2401.00002",
            title="Second Paper",
            status="success",
            page_count=20,
            character_count=3000,
            section_count=10,
            reference_count=40,
            has_reference_section=True,
            elapsed_seconds=3.0,
            failure_stage=None,
        ),
        evaluation.PaperEvaluationResult(
            arxiv_id="2401.00003",
            title="Failed Paper",
            status="failed",
            page_count=0,
            character_count=0,
            section_count=0,
            reference_count=0,
            has_reference_section=False,
            elapsed_seconds=2.0,
            failure_stage="download",
            error_type="ReadTimeout",
            error_message="Timed out",
        ),
    ]

    summary = evaluation.summarize_results(
        results
    )

    assert summary == {
        "attempted": 3,
        "successful": 2,
        "failed": 1,
        "success_rate": 66.67,
        "total_pages": 30,
        "total_characters": 4000,
        "total_sections": 15,
        "total_references": 60,
        "average_pages": 15.0,
        "average_references": 30.0,
        "median_references": 30.0,
        "total_elapsed_seconds": 6.0,
        "failures_by_stage": {
            "download": 1,
        },
        "failures_by_type": {
            "ReadTimeout": 1,
        },
    }




def test_evaluate_paper_records_structural_failure(monkeypatch):
    metadata = ArxivMetadata(
        title="Paper Without References",
        summary="Example summary.",
        authors=["Example Author"],
        published="2024-01-01T00:00:00Z",
        updated="2024-01-01T00:00:00Z",
        categories=["cs.LG"],
        arxiv_id="2401.55555v1",
        pdf_url="https://arxiv.org/pdf/2401.55555v1",
    )

    pages = [
        ParsedPage(
            page_number=1,
            text="Abstract\nPaper body.",
        ),
    ]

    sections = [
        PaperSection(
            title="Abstract",
            text="Paper body.",
            start_page=1,
            end_page=1,
        ),
    ]

    monkeypatch.setattr(
        evaluation,
        "download_pdf",
        lambda pdf_url: b"%PDF-fake",
    )
    monkeypatch.setattr(
        evaluation,
        "parse_pdf",
        lambda pdf_bytes: pages,
    )
    monkeypatch.setattr(
        evaluation,
        "extract_sections",
        lambda parsed_pages: sections,
    )
    monkeypatch.setattr(
        evaluation,
        "extract_references",
        lambda parsed_sections: [],
    )

    result = evaluation.evaluate_paper(metadata)

    assert result.status == "failed"
    assert result.failure_stage == (
        "validate_structure"
    )
    assert result.page_count == 1
    assert result.section_count == 1
    assert result.reference_count == 0
    assert result.has_reference_section is False
    assert result.error_type == (
        "StructuralValidationError"
    )
    assert result.structural_issues == [
        "no_reference_section",
        "no_references",
    ]


def test_evaluate_paper_records_download_failure(monkeypatch):
    metadata = ArxivMetadata(
        title="Unavailable Paper",
        summary="Example summary.",
        authors=["Example Author"],
        published="2024-01-01T00:00:00Z",
        updated="2024-01-01T00:00:00Z",
        categories=["cs.LG"],
        arxiv_id="2401.99999v1",
        pdf_url="https://arxiv.org/pdf/2401.99999v1",
    )

    def fake_download(pdf_url):
        request = httpx.Request("GET", pdf_url)
        raise httpx.ReadTimeout(
            "The read operation timed out",
            request=request,
        )

    monkeypatch.setattr(
        evaluation,
        "download_pdf",
        fake_download,
    )

    result = evaluation.evaluate_paper(metadata)

    assert result.arxiv_id == "2401.99999v1"
    assert result.title == "Unavailable Paper"
    assert result.status == "failed"
    assert result.failure_stage == "download"
    assert result.page_count == 0
    assert result.character_count == 0
    assert result.section_count == 0
    assert result.reference_count == 0
    assert result.has_reference_section is False
    assert result.error_type == "ReadTimeout"
    assert result.error_message == (
        "The read operation timed out"
    )
    assert result.elapsed_seconds >= 0






def test_evaluate_paper_records_success(monkeypatch):
    metadata = ArxivMetadata(
        title="Example Paper",
        summary="Example summary.",
        authors=["Example Author"],
        published="2024-01-01T00:00:00Z",
        updated="2024-01-01T00:00:00Z",
        categories=["cs.LG"],
        arxiv_id="2401.12345v1",
        pdf_url="https://arxiv.org/pdf/2401.12345v1",
    )

    pages = [
        ParsedPage(
            page_number=1,
            text="Abstract\nExample text.",
        ),
        ParsedPage(
            page_number=2,
            text=(
                "References\n"
                "[1] Example Author. Example Paper. 2024."
            ),
        ),
    ]

    sections = [
        PaperSection(
            title="Abstract",
            text="Example text.",
            start_page=1,
            end_page=1,
        ),
        PaperSection(
            title="References",
            text="[1] Example Author. Example Paper. 2024.",
            start_page=2,
            end_page=2,
        ),
    ]

    references = [
        Reference(
            label="1",
            raw_text=(
                "Example Author. Example Paper. 2024."
            ),
            year=2024,
        ),
    ]

    monkeypatch.setattr(
        evaluation,
        "download_pdf",
        lambda pdf_url: b"%PDF-fake",
    )
    monkeypatch.setattr(
        evaluation,
        "parse_pdf",
        lambda pdf_bytes: pages,
    )
    monkeypatch.setattr(
        evaluation,
        "extract_sections",
        lambda parsed_pages: sections,
    )
    monkeypatch.setattr(
        evaluation,
        "extract_references",
        lambda parsed_sections: references,
    )

    result = evaluation.evaluate_paper(metadata)

    assert result.arxiv_id == "2401.12345v1"
    assert result.title == "Example Paper"
    assert result.status == "success"
    assert result.page_count == 2
    assert result.character_count == 73
    assert result.section_count == 2
    assert result.reference_count == 1
    assert result.has_reference_section is True
    assert result.error_type is None
    assert result.error_message is None
    assert result.elapsed_seconds >= 0
    assert result.failure_stage is None