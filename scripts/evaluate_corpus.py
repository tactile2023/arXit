import argparse
import re
import time
from pathlib import Path

import httpx

from arxit.arxiv_client import (
    fetch_arxiv_metadata_batch_xml,
)
from arxit.arxiv_id import normalize_arxiv_id
from arxit.arxiv_parser import (
    parse_arxiv_metadata_batch,
)
from arxit.evaluation import (
    PaperEvaluationResult,
    append_checkpoint_result,
    evaluate_paper,
    load_checkpoint_results,
    summarize_results,
    write_evaluation_reports,
)


RETRYABLE_ERROR_TYPES = {
    "ReadTimeout",
    "ConnectTimeout",
    "ConnectError",
    "RemoteProtocolError",
}


def base_arxiv_id(arxiv_id: str) -> str:
    return re.sub(
        r"v\d+$",
        "",
        arxiv_id,
        flags=re.IGNORECASE,
    )


def load_corpus(
    input_path: Path,
    limit: int | None,
) -> list[str]:
    raw_ids = input_path.read_text(
        encoding="utf-8"
    ).splitlines()

    paper_ids = []
    seen_ids = set()

    for raw_id in raw_ids:
        stripped_id = raw_id.strip()

        if not stripped_id:
            continue

        normalized_id = normalize_arxiv_id(
            stripped_id
        )
        normalized_id = base_arxiv_id(
            normalized_id
        )

        if normalized_id in seen_ids:
            continue

        paper_ids.append(normalized_id)
        seen_ids.add(normalized_id)

    if limit is not None:
        return paper_ids[:limit]

    return paper_ids


def chunk_items(
    items: list[str],
    chunk_size: int,
) -> list[list[str]]:
    return [
        items[index:index + chunk_size]
        for index in range(
            0,
            len(items),
            chunk_size,
        )
    ]


def fetch_metadata_with_retries(
    paper_ids: list[str],
    delay_seconds: float,
    max_attempts: int,
):
    for attempt in range(1, max_attempts + 1):
        try:
            xml_text = (
                fetch_arxiv_metadata_batch_xml(
                    paper_ids
                )
            )

            return parse_arxiv_metadata_batch(
                xml_text
            )

        except httpx.HTTPError as exc:
            if attempt == max_attempts:
                raise

            wait_seconds = (
                delay_seconds * attempt
            )

            print(
                f"Metadata request failed: {exc}. "
                f"Retrying in {wait_seconds} seconds."
            )

            time.sleep(wait_seconds)


def evaluate_with_retries(
    metadata,
    delay_seconds: float,
    max_attempts: int,
) -> PaperEvaluationResult:
    result = None

    for attempt in range(1, max_attempts + 1):
        result = evaluate_paper(metadata)

        should_retry = (
            result.status == "failed"
            and result.failure_stage == "download"
            and result.error_type
            in RETRYABLE_ERROR_TYPES
        )

        if not should_retry:
            return result

        if attempt < max_attempts:
            wait_seconds = (
                delay_seconds * attempt
            )

            print(
                f"  Download failed with "
                f"{result.error_type}. "
                f"Retrying in {wait_seconds} seconds."
            )

            time.sleep(wait_seconds)

    return result


def metadata_failure_result(
    arxiv_id: str,
    error_type: str,
    error_message: str,
) -> PaperEvaluationResult:
    return PaperEvaluationResult(
        arxiv_id=arxiv_id,
        title="",
        status="failed",
        page_count=0,
        character_count=0,
        section_count=0,
        reference_count=0,
        has_reference_section=False,
        elapsed_seconds=0.0,
        failure_stage="metadata",
        error_type=error_type,
        error_message=error_message,
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate arXit ingestion and reference "
            "extraction on a fixed paper corpus."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "benchmarks/paper_ids.txt"
        ),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path(
            "benchmarks/results"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
    )

    return parser


def main():
    args = build_parser().parse_args()

    if args.limit is not None and args.limit <= 0:
        raise ValueError(
            "limit must be positive"
        )

    if args.batch_size <= 0:
        raise ValueError(
            "batch-size must be positive"
        )

    if args.delay < 0:
        raise ValueError(
            "delay cannot be negative"
        )

    if args.max_attempts <= 0:
        raise ValueError(
            "max-attempts must be positive"
        )

    paper_ids = load_corpus(
        args.input,
        args.limit,
    )

    checkpoint_path = (
        args.output_directory
        / "checkpoint.jsonl"
    )

    existing_results = load_checkpoint_results(
        checkpoint_path
    )

    completed_ids = {
        base_arxiv_id(result.arxiv_id)
        for result in existing_results
    }

    pending_ids = [
        arxiv_id
        for arxiv_id in paper_ids
        if arxiv_id not in completed_ids
    ]

    print(f"Corpus papers: {len(paper_ids)}")
    print(f"Already completed: {len(completed_ids)}")
    print(f"Pending: {len(pending_ids)}")

    processed_count = len(completed_ids)

    for batch in chunk_items(
        pending_ids,
        args.batch_size,
    ):
        try:
            metadata_items = (
                fetch_metadata_with_retries(
                    batch,
                    delay_seconds=args.delay,
                    max_attempts=args.max_attempts,
                )
            )

        except httpx.HTTPError as exc:
            for arxiv_id in batch:
                result = metadata_failure_result(
                    arxiv_id=arxiv_id,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )

                append_checkpoint_result(
                    checkpoint_path,
                    result,
                )

                processed_count += 1

                print(
                    f"[{processed_count}/"
                    f"{len(paper_ids)}] "
                    f"{arxiv_id}: failed at metadata"
                )

            continue

        metadata_by_id = {
            base_arxiv_id(metadata.arxiv_id):
            metadata
            for metadata in metadata_items
        }

        for arxiv_id in batch:
            metadata = metadata_by_id.get(
                arxiv_id
            )

            if metadata is None:
                result = metadata_failure_result(
                    arxiv_id=arxiv_id,
                    error_type="MetadataNotFound",
                    error_message=(
                        "arXiv returned no metadata "
                        "for this identifier"
                    ),
                )

            else:
                result = evaluate_with_retries(
                    metadata,
                    delay_seconds=args.delay,
                    max_attempts=args.max_attempts,
                )

            append_checkpoint_result(
                checkpoint_path,
                result,
            )

            processed_count += 1

            print(
                f"[{processed_count}/"
                f"{len(paper_ids)}] "
                f"{arxiv_id}: {result.status} "
                f"({result.page_count} pages, "
                f"{result.reference_count} references)"
            )

            if processed_count < len(paper_ids):
                time.sleep(args.delay)

    all_checkpoint_results = (
        load_checkpoint_results(
            checkpoint_path
        )
    )

    selected_id_set = set(paper_ids)

    selected_results = [
        result
        for result in all_checkpoint_results
        if base_arxiv_id(result.arxiv_id)
        in selected_id_set
    ]

    write_evaluation_reports(
        output_directory=args.output_directory,
        results=selected_results,
    )

    summary = summarize_results(
        selected_results
    )

    print()
    print("Evaluation complete")
    print(f"Attempted: {summary['attempted']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(
        f"Success rate: "
        f"{summary['success_rate']}%"
    )
    print(
        f"Total pages: "
        f"{summary['total_pages']}"
    )
    print(
        f"Total references: "
        f"{summary['total_references']}"
    )
    print(
        f"Results saved to: "
        f"{args.output_directory}"
    )


if __name__ == "__main__":
    main() 