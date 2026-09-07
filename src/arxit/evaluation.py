from dataclasses import dataclass, field, asdict, fields
from time import perf_counter
import json

from pathlib import Path
from .models import ArxivMetadata
from .pdf_downloader import download_pdf
from .pdf_parser import parse_pdf
from .reference_extractor import extract_references
from .section_extractor import extract_sections
import re
import csv
from collections import Counter
from statistics import mean, median


@dataclass
class PaperEvaluationResult:
    arxiv_id: str
    title: str
    status: str
    page_count: int
    character_count: int
    section_count: int
    reference_count: int
    has_reference_section: bool
    elapsed_seconds: float
    failure_stage: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    structural_issues: list[str] = field(default_factory=list)




def select_corpus(
    metadata_groups: list[list[ArxivMetadata]], target_size: int) -> list[str]:
    if target_size < 0:
        raise ValueError(
            "target_size cannot be negative"
        )

    if target_size == 0 or not metadata_groups:
        return []

    selected_ids = []
    seen_ids = set()

    longest_group_size = max(
        len(group)
        for group in metadata_groups
    )

    for index in range(longest_group_size):
        for group in metadata_groups:
            if index >= len(group):
                continue

            arxiv_id = re.sub(
                r"v\d+$",
                "",
                group[index].arxiv_id,
                flags=re.IGNORECASE,
            )

            if arxiv_id in seen_ids:
                continue

            selected_ids.append(arxiv_id)
            seen_ids.add(arxiv_id)

            if len(selected_ids) == target_size:
                return selected_ids

    return selected_ids


def build_arxiv_year_query(category: str, year: int ) -> str:
    return (
        f"cat:{category} AND "
        f"submittedDate:"
        f"[{year}01010000 TO "
        f"{year}12312359]"
    )


def select_stratified_corpus(metadata_groups: list[list[ArxivMetadata]], papers_per_group: int ) -> list[str]:
    if papers_per_group < 0:
        raise ValueError(
            "papers_per_group cannot be negative"
        )

    if papers_per_group == 0:
        return []

    selected_groups = []
    seen_ids = set()

    for group_number, group in enumerate(
        metadata_groups,
        start=1,
    ):
        group_ids = []

        for metadata in group:
            arxiv_id = re.sub(
                r"v\d+$",
                "",
                metadata.arxiv_id,
                flags=re.IGNORECASE,
            )

            if arxiv_id in seen_ids:
                continue

            group_ids.append(arxiv_id)
            seen_ids.add(arxiv_id)

            if len(group_ids) == papers_per_group:
                break

        if len(group_ids) < papers_per_group:
            raise RuntimeError(
                f"Group {group_number} provided "
                f"only {len(group_ids)} unique "
                f"papers; {papers_per_group} "
                f"were required."
            )

        selected_groups.append(group_ids)

    selected_ids = []

    for index in range(papers_per_group):
        for group_ids in selected_groups:
            selected_ids.append(
                group_ids[index]
            )

    return selected_ids



def write_corpus_checkpoint(
    checkpoint_path: Path,
    metadata_groups: dict[
        str,
        list[ArxivMetadata],
    ],
) -> None:
    checkpoint_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        group_key: [
            asdict(metadata)
            for metadata in metadata_items
        ]
        for group_key, metadata_items
        in metadata_groups.items()
    }

    temporary_path = checkpoint_path.with_name(
        checkpoint_path.name + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(
        checkpoint_path
    )


def load_corpus_checkpoint(checkpoint_path: Path) -> dict[str, list[ArxivMetadata]]:
    if not checkpoint_path.exists():
        return {}

    payload = json.loads(
        checkpoint_path.read_text(
            encoding="utf-8"
        )
    )

    return {
        group_key: [
            ArxivMetadata(**metadata_data)
            for metadata_data in metadata_items
        ]
        for group_key, metadata_items
        in payload.items()
    }






def evaluate_paper(metadata: ArxivMetadata) -> PaperEvaluationResult:
    started_at = perf_counter()

    pages = []
    sections = []
    references = []
    failure_stage = "download"

    try:
        pdf_bytes = download_pdf(
            metadata.pdf_url
        )

        failure_stage = "parse_pdf"
        pages = parse_pdf(pdf_bytes)

        failure_stage = "extract_sections"
        sections = extract_sections(pages)

        failure_stage = "extract_references"
        references = extract_references(
            sections
        )

    except Exception as exc:
        return PaperEvaluationResult(
            arxiv_id=metadata.arxiv_id,
            title=metadata.title,
            status="failed",
            page_count=len(pages),
            character_count=sum(
                len(page.text)
                for page in pages
            ),
            section_count=len(sections),
            reference_count=len(references),
            has_reference_section=False,
            elapsed_seconds=(
                perf_counter() - started_at
            ),
            failure_stage=failure_stage,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    character_count = sum(
        len(page.text)
        for page in pages
    )

    has_reference_section = any(
        section.title.lower()
        in {"references", "bibliography"}
        for section in sections
    )

    structural_issues = []

    if not pages:
        structural_issues.append("no_pages")

    if character_count == 0:
        structural_issues.append("empty_text")

    if not sections:
        structural_issues.append("no_sections")

    if not has_reference_section:
        structural_issues.append(
            "no_reference_section"
        )

    if not references:
        structural_issues.append("no_references")

    if structural_issues:
        return PaperEvaluationResult(
            arxiv_id=metadata.arxiv_id,
            title=metadata.title,
            status="failed",
            page_count=len(pages),
            character_count=character_count,
            section_count=len(sections),
            reference_count=len(references),
            has_reference_section=(
                has_reference_section
            ),
            elapsed_seconds=(
                perf_counter() - started_at
            ),
            failure_stage="validate_structure",
            error_type=(
                "StructuralValidationError"
            ),
            error_message=", ".join(
                structural_issues
            ),
            structural_issues=structural_issues,
        )

    return PaperEvaluationResult(
        arxiv_id=metadata.arxiv_id,
        title=metadata.title,
        status="success",
        page_count=len(pages),
        character_count=character_count,
        section_count=len(sections),
        reference_count=len(references),
        has_reference_section=True,
        elapsed_seconds=(
            perf_counter() - started_at
        ),
        failure_stage=None,
    )





def summarize_results(results: list[PaperEvaluationResult]) -> dict:
    successful_results = [
        result
        for result in results
        if result.status == "success"
    ]

    failed_results = [
        result
        for result in results
        if result.status == "failed"
    ]

    attempted = len(results)
    successful = len(successful_results)
    failed = len(failed_results)

    if attempted:
        success_rate = round(
            successful / attempted * 100,
            2,
        )
    else:
        success_rate = 0.0

    page_counts = [
        result.page_count
        for result in successful_results
    ]

    reference_counts = [
        result.reference_count
        for result in successful_results
    ]

    failures_by_stage = Counter(
        result.failure_stage
        for result in failed_results
        if result.failure_stage is not None
    )

    failures_by_type = Counter(
        result.error_type
        for result in failed_results
        if result.error_type is not None
    )

    return {
        "attempted": attempted,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "total_pages": sum(
            result.page_count
            for result in successful_results
        ),
        "total_characters": sum(
            result.character_count
            for result in successful_results
        ),
        "total_sections": sum(
            result.section_count
            for result in successful_results
        ),
        "total_references": sum(
            reference_counts
        ),
        "average_pages": (
            mean(page_counts)
            if page_counts
            else 0.0
        ),
        "average_references": (
            mean(reference_counts)
            if reference_counts
            else 0.0
        ),
        "median_references": (
            median(reference_counts)
            if reference_counts
            else 0.0
        ),
        "total_elapsed_seconds": round(
            sum(
                result.elapsed_seconds
                for result in results
            ),
            3,
        ),
        "failures_by_stage": dict(
            failures_by_stage
        ),
        "failures_by_type": dict(
            failures_by_type
        ),
    }




def append_checkpoint_result(checkpoint_path: Path, result: PaperEvaluationResult) -> None:
    checkpoint_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized_result = json.dumps(
        asdict(result),
        sort_keys=True,
    )

    with checkpoint_path.open(
        "a",
        encoding="utf-8",
    ) as checkpoint_file:
        checkpoint_file.write(
            serialized_result + "\n"
        )


def load_checkpoint_results(checkpoint_path: Path) -> list[PaperEvaluationResult]:
    if not checkpoint_path.exists():
        return []

    results = []

    with checkpoint_path.open(
        encoding="utf-8",
    ) as checkpoint_file:
        for line in checkpoint_file:
            stripped_line = line.strip()

            if not stripped_line:
                continue

            data = json.loads(stripped_line)

            results.append(
                PaperEvaluationResult(**data)
            )

    return results



def write_evaluation_reports(output_directory: Path, results: list[PaperEvaluationResult]) -> None:
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = summarize_results(results)

    summary_path = (
        output_directory / "summary.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    csv_path = (
        output_directory / "paper_results.csv"
    )

    field_names = [
        result_field.name
        for result_field in fields(
            PaperEvaluationResult
        )
    ]

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=field_names,
        )

        writer.writeheader()

        for result in results:
            row = asdict(result)

            row["structural_issues"] = ";".join(
                result.structural_issues
            )

            writer.writerow(row)