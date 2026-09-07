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
from arxit.evaluation import select_corpus


CATEGORIES = (
    "cs.LG",
    "cs.CL",
    "cs.CV",
    "cs.AI",
    "stat.ML",
    "cs.IR",
)

SORT_ORDERS = (
    "ascending",
    "descending",
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
        "--target",
        type=int,
        default=600,
        help="Number of unique papers to select.",
    )
    parser.add_argument(
        "--per-query",
        type=int,
        default=75,
        help=(
            "Results requested for each category "
            "and sort order."
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

    if args.target <= 0:
        raise ValueError(
            "target must be positive"
        )

    if args.per_query <= 0:
        raise ValueError(
            "per-query must be positive"
        )

    if args.delay < 0:
        raise ValueError(
            "delay cannot be negative"
        )

    metadata_groups = []
    request_number = 0
    total_requests = (
        len(CATEGORIES) * len(SORT_ORDERS)
    )

    for category in CATEGORIES:
        for sort_order in SORT_ORDERS:
            request_number += 1

            print(
                f"[{request_number}/{total_requests}] "
                f"Fetching {sort_order} "
                f"{category} papers..."
            )

            metadata_items = fetch_with_retries(
                search_query=f"cat:{category}",
                max_results=args.per_query,
                sort_order=sort_order,
                delay_seconds=args.delay,
            )

            metadata_groups.append(
                metadata_items
            )

            print(
                f"  Received "
                f"{len(metadata_items)} papers."
            )

            if request_number < total_requests:
                time.sleep(args.delay)

    selected_ids = select_corpus(
        metadata_groups,
        target_size=args.target,
    )

    if len(selected_ids) < args.target:
        raise RuntimeError(
            f"Only {len(selected_ids)} unique "
            f"papers were returned; "
            f"{args.target} were requested."
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