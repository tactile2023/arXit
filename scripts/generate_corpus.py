import argparse
import time
from pathlib import Path

import httpx

from arxit.arxiv_client import (
    fetch_arxiv_search_xml,
)
from arxit.arxiv_parser import (
    parse_arxiv_metadata_batch,
)

from arxit.evaluation import (
    build_arxiv_year_query,
    select_stratified_corpus,
    write_corpus_checkpoint,
    load_corpus_checkpoint
)

CATEGORIES = (
    "cs.LG",
    "cs.CL",
    "cs.CV",
    "cs.AI",
    "stat.ML",
    "cs.IR",
)


YEARS = (
    2021,
    2022,
    2023,
    2024,
    2025,
)


def fetch_with_retries(
    search_query: str,
    max_results: int,
    sort_order: str,
    delay_seconds: float,
    max_attempts: int = 3,
):
    for attempt in range(1, max_attempts + 1):
        try:
            xml_text = fetch_arxiv_search_xml(
                search_query=search_query,
                max_results=max_results,
                sort_order=sort_order,
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
                f"Request failed: {exc}. "
                f"Retrying in {wait_seconds} seconds."
            )

            time.sleep(wait_seconds)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a fixed corpus of real "
            "arXiv paper identifiers."
        )
    )

    parser.add_argument(
    "--checkpoint",
    type=Path,
    default=Path(
        "benchmarks/"
        "corpus-generation-checkpoint.json"
    ),
    help=(
        "Checkpoint used to resume completed "
        "category-year queries."
    ),
    )

    parser.add_argument(
    "--papers-per-group",
    type=int,
    default=20,
    help=(
        "Papers selected from each "
        "category-year group."
        ),
    )
    parser.add_argument(
        "--candidates-per-group",
        type=int,
        default=75,
        help=(
            "Candidate papers requested for each "
            "category-year group before "
            "deduplication."
        ),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Seconds between arXiv API requests.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "benchmarks/paper_ids.txt"
        ),
        help="Destination corpus manifest.",
    )

    return parser


def main():
    args = build_parser().parse_args()

    if args.papers_per_group <= 0:
        raise ValueError(
            "papers-per-group must be positive"
        )

    if (
        args.candidates_per_group
        < args.papers_per_group
    ):
        raise ValueError(
            "candidates-per-group must be at "
            "least papers-per-group"
        )

    if args.delay < 0:
        raise ValueError(
            "delay cannot be negative"
        )


    checkpoint_groups = (
        load_corpus_checkpoint(args.checkpoint)
    )


    metadata_groups = []
    request_number = 0
    total_requests = (
        len(CATEGORIES) * len(YEARS)
    )
    expected_total = (
        len(CATEGORIES)
        * len(YEARS)
        * args.papers_per_group
    )

    for category in CATEGORIES:
        for year in YEARS:
            request_number += 1

            group_key = (
                f"{category}:{year}:"
                f"{args.candidates_per_group}"
            )

            if group_key in checkpoint_groups:
                metadata_items = (
                    checkpoint_groups[group_key]
                )

                print(
                    f"[{request_number}/"
                    f"{total_requests}] "
                    f"Loaded {category} {year} "
                    f"from checkpoint "
                    f"({len(metadata_items)} "
                    f"candidates)."
                )

            else:
                search_query = (
                    build_arxiv_year_query(
                        category,
                        year,
                    )
                )

                print(
                    f"[{request_number}/"
                    f"{total_requests}] "
                    f"Fetching {category} papers "
                    f"from {year}..."
                )

                metadata_items = fetch_with_retries(
                    search_query=search_query,
                    max_results=(
                        args.candidates_per_group
                    ),
                    sort_order="descending",
                    delay_seconds=args.delay,
                )

                checkpoint_groups[group_key] = (
                    metadata_items
                )

                write_corpus_checkpoint(
                    args.checkpoint,
                    checkpoint_groups,
                )

                print(
                    f"  Received and checkpointed "
                    f"{len(metadata_items)} "
                    f"candidates."
                )

                if request_number < total_requests:
                    time.sleep(args.delay)

            metadata_groups.append(
                metadata_items
            )

    selected_ids = select_stratified_corpus(
        metadata_groups,
        papers_per_group=(
            args.papers_per_group
        ),
    )

    if len(selected_ids) != expected_total:
        raise RuntimeError(
            f"Selected {len(selected_ids)} "
            f"papers; expected {expected_total}."
        )



    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        "\n".join(selected_ids) + "\n",
        encoding="utf-8",
    )

    print(
        f"Saved {len(selected_ids)} unique "
        f"real arXiv IDs to {args.output}."
    )


if __name__ == "__main__":
    main()