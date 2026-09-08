import arxit.evaluation as evaluation
import httpx
from arxit.models import (
    ArxivMetadata,
    PaperSection,
    ParsedPage,
    Reference,
)
import csv
import json



def test_corpus_generation_checkpoint_round_trip(tmp_path):
    metadata = ArxivMetadata(
        title="Checkpoint Paper",
        summary="Example summary.",
        authors=["Example Author"],
        published="2021-01-01T00:00:00Z",
        updated="2021-01-01T00:00:00Z",
        categories=["cs.LG"],
        arxiv_id="2101.00001v1",
        pdf_url=(
            "https://arxiv.org/pdf/"
            "2101.00001v1"
        ),
    )

    checkpoint_path = (
        tmp_path / "corpus-checkpoint.json"
    )

    groups = {
        "cs.LG:2021:30": [metadata],
    }

    evaluation.write_corpus_checkpoint(
        checkpoint_path,
        groups,
    )

    loaded_groups = (
        evaluation.load_corpus_checkpoint(
            checkpoint_path
        )
    )

    assert loaded_groups == groups


def test_load_corpus_checkpoint_returns_empty_when_missing(
    tmp_path,
):
    checkpoint_path = (
        tmp_path / "missing-checkpoint.json"
    )

    assert (
        evaluation.load_corpus_checkpoint(
            checkpoint_path
        )
        == {}
    )



def test_build_arxiv_year_query():
    query = evaluation.build_arxiv_year_query(
        "cs.LG",
        2021,
    )

    assert query == (
        "cat:cs.LG AND "
        "submittedDate:"
        "[202101010000 TO 202112312359]"
    )


def test_select_stratified_corpus_fills_each_group():
    def make_metadata(arxiv_id, category):
        return ArxivMetadata(
            title=f"Paper {arxiv_id}",
            summary="",
            authors=[],
            published="2021-01-01T00:00:00Z",
            updated="2021-01-01T00:00:00Z",
            categories=[category],
            arxiv_id=arxiv_id,
            pdf_url=(
                f"https://arxiv.org/pdf/{arxiv_id}"
            ),
        )

    metadata_groups = [
        [
            make_metadata(
                "2101.00001v1",
                "cs.LG",
            ),
            make_metadata(
                "2101.00002v2",
                "cs.LG",
            ),
            make_metadata(
                "2101.00003v1",
                "cs.LG",
            ),
        ],
        [
            make_metadata(
                "2101.00001v3",
                "cs.CL",
            ),
            make_metadata(
                "2101.00004v1",
                "cs.CL",
            ),
            make_metadata(
                "2101.00005v1",
                "cs.CL",
            ),
        ],
    ]

    selected_ids = (
        evaluation.select_stratified_corpus(
            metadata_groups,
            papers_per_group=2,
        )
    )

    assert selected_ids == [
        "2101.00001",
        "2101.00004",
        "2101.00002",
        "2101.00005",
    ]



def test_write_evaluation_reports(tmp_path):
    result = evaluation.PaperEvaluationResult(
        arxiv_id="2401.00001",
        title="Example Paper",
        status="success",
        page_count=10,
        character_count=1000,
        section_count=5,
        reference_count=20,
        has_reference_section=True,
        elapsed_seconds=1.5,
        failure_stage=None,
    )

    evaluation.write_evaluation_reports(
        output_directory=tmp_path,
        results=[result],
    )

    summary_path = tmp_path / "summary.json"
    csv_path = tmp_path / "paper_results.csv"

    assert summary_path.exists()
    assert csv_path.exists()

    summary = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    assert summary["attempted"] == 1
    assert summary["successful"] == 1
    assert summary["failed"] == 0
    assert summary["success_rate"] == 100.0
    assert summary["total_pages"] == 10
    assert summary["total_references"] == 20

    with csv_path.open(
        encoding="utf-8",
        newline="",
    ) as csv_file:
        rows = list(
            csv.DictReader(csv_file)
        )

    assert len(rows) == 1
    assert rows[0]["arxiv_id"] == "2401.00001"
    assert rows[0]["status"] == "success"
    assert rows[0]["page_count"] == "10"
    assert rows[0]["reference_count"] == "20"






def test_checkpoint_round_trip(tmp_path):
    checkpoint_path = (
        tmp_path / "checkpoint.jsonl"
    )

    first_result = (
        evaluation.PaperEvaluationResult(
            arxiv_id="2401.00001",
            title="Successful Paper",
            status="success",
            page_count=10,
            character_count=1000,
            section_count=5,
            reference_count=20,
            has_reference_section=True,
            elapsed_seconds=1.5,
            failure_stage=None,
        )
    )

    second_result = (
        evaluation.PaperEvaluationResult(
            arxiv_id="2401.00002",
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
        )
    )

    evaluation.append_checkpoint_result(
        checkpoint_path,
        first_result,
    )
    evaluation.append_checkpoint_result(
        checkpoint_path,
        second_result,
    )

    loaded_results = (
        evaluation.load_checkpoint_results(
            checkpoint_path
        )
    )

    assert loaded_results == [
        first_result,
        second_result,
    ]






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