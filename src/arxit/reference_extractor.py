import re
from .reference_parser import (extract_year, extract_arxiv_id, extract_doi, extract_url)
from .models import Reference

YEAR_IN_REFERENCE_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}[a-z]?\."
)

DOI_IN_REFERENCE_PATTERN = re.compile(
    r"(?:doi:\s*)?10\.\s*\d{4,9}/",
    re.IGNORECASE,
)

PARENTHESIZED_AUTHOR_YEAR_START_PATTERN = re.compile(
    r"^.+\s+\(\s*(?:19|20)\d{2}[a-z]?\s*\)\."
)


REFERENCE_START_PATTERN = re.compile(
    r"^\[(\d+)\]\s*(.*)$"
)

PLAIN_NUMBERED_REFERENCE_START_PATTERN = re.compile(
    r"^(\d{1,3})\.\s+(.+)$"
)

YEAR_TERMINATED_REFERENCE_PATTERN = re.compile(
    r",\s+(?:19|20)\d{2}[a-z]?\.$"
)

PAGE_NUMBER_PATTERN = re.compile(
    r"^\d{1,3}$"
)

AUTHOR_YEAR_START_PATTERN = re.compile(
    r"^.+\.\s+(?:19|20)\d{2}[a-z]?\.(?:\s+.*)?$"
)

YEAR_AT_LINE_START_PATTERN = re.compile(
    r"^(?:19|20)\d{2}[a-z]?\.(?:\s+.*)?$"
)

















def build_reference(label, raw_text):
    return Reference(
        label=label,
        raw_text=raw_text,
        year=extract_year(raw_text),
        arxiv_id = extract_arxiv_id(raw_text),
        doi = extract_doi(raw_text),
        url = extract_url(raw_text)
    )



def match_numbered_reference_start(line):
    for pattern in (
        REFERENCE_START_PATTERN,
        PLAIN_NUMBERED_REFERENCE_START_PATTERN,
    ):
        match = pattern.match(line)

        if match:
            return (
                match.group(1),
                match.group(2).strip(),
            )

    return None






def extract_references(sections):
    reference_sections = [
        section
        for section in sections
        if section.title.lower()
        in {"references", "bibliography"}
    ]

    if not reference_sections:
        return []

    lines = [
        raw_line.strip()
        for section in reference_sections
        for raw_line in section.text.splitlines()
        if raw_line.strip()
    ]

    lines = [
    line
    for line in lines
    if PAGE_NUMBER_PATTERN.fullmatch(line) is None
    ]

    has_numbered_references = any(
        match_numbered_reference_start(line)
        is not None
        for line in lines
    )

    if has_numbered_references:
        return extract_numbered_references(lines)


    has_parenthesized_author_year = any(
    PARENTHESIZED_AUTHOR_YEAR_START_PATTERN.match(
        line
    )
    is not None
    for line in lines
    )

    if has_parenthesized_author_year:
        return (
            extract_parenthesized_author_year_references(
                lines
            )
        )

    has_year_at_end_of_line = any(
    YEAR_TERMINATED_REFERENCE_PATTERN.search(
        line
    )
    is not None
    for line in lines
)

    has_wrapped_terminal_year = any(
        index > 0
        and lines[index - 1].endswith(",")
        and YEAR_AT_LINE_START_PATTERN.fullmatch(
            line
        )
        is not None
        for index, line in enumerate(lines)
    )

    has_year_terminated_references = (
        has_year_at_end_of_line
        or has_wrapped_terminal_year
    )

    if has_year_terminated_references:
        return extract_year_terminated_references(
            lines
        )

    return extract_author_year_references(lines)


def find_next_numbered_reference_label(
    lines,
    start_index,
):
    for line in lines[start_index:]:
        match = match_numbered_reference_start(
            line
        )

        if match is not None:
            return match[0]

    return None



def extract_numbered_references(lines):
    references = []
    current_label = None
    current_lines = []

    for index, line in enumerate(lines):
        match = match_numbered_reference_start(
            line
        )

        if match is not None:
            candidate_label, first_line = match

            looks_like_false_label_jump = False

            if (
                current_label is not None
                and current_label.isdigit()
                and candidate_label.isdigit()
            ):
                expected_label = str(
                    int(current_label) + 1
                )

                if candidate_label != expected_label:
                    next_label = (
                        find_next_numbered_reference_label(
                            lines,
                            index + 1,
                        )
                    )

                    looks_like_false_label_jump = (
                        next_label == expected_label
                    )

            if looks_like_false_label_jump:
                current_lines.append(line)
                continue

            if current_label is not None:
                references.append(
                    build_reference(
                        label=current_label,
                        raw_text=" ".join(
                            current_lines
                        ),
                    )
                )

            current_label = candidate_label
            current_lines = [first_line]

        elif current_label is not None:
            current_lines.append(line)

    if current_label is not None:
        references.append(
            build_reference(
                label=current_label,
                raw_text=" ".join(
                    current_lines
                ),
            )
        )

    return references


def extract_year_terminated_references(lines):
    references = []
    current_lines = []
    waiting_for_doi_continuation = False

    for line in lines:
        previous_line = (
            current_lines[-1]
            if current_lines
            else None
        )

        current_lines.append(line)

        if waiting_for_doi_continuation:
            ends_reference = True
            waiting_for_doi_continuation = False

        else:
            contains_year = any(
                YEAR_IN_REFERENCE_PATTERN.search(
                    current_line
                )
                is not None
                for current_line in current_lines
            )

            contains_doi = (
                DOI_IN_REFERENCE_PATTERN.search(
                    line
                )
                is not None
            )

            ends_with_year = (
                YEAR_TERMINATED_REFERENCE_PATTERN.search(
                    line
                )
                is not None
            )

            standalone_year_after_comma = (
                previous_line is not None
                and previous_line.endswith(",")
                and YEAR_AT_LINE_START_PATTERN.fullmatch(
                    line
                )
                is not None
            )

            doi_continues_on_next_line = (
                contains_doi
                and line.endswith("/")
            )

            if doi_continues_on_next_line:
                waiting_for_doi_continuation = True
                ends_reference = False

            else:
                ends_reference = (
                    ends_with_year
                    or standalone_year_after_comma
                    or (
                        contains_year
                        and contains_doi
                    )
                )

        if ends_reference:
            references.append(
                build_reference(
                label=None,
                raw_text=" ".join(current_lines),
)
            )
            current_lines = []

    if current_lines:
        references.append(
            build_reference(
                label=None,
                raw_text=" ".join(current_lines),
)
        )

    return references


def extract_parenthesized_author_year_references(lines):
    references = []
    current_lines = []

    for line in lines:
        starts_reference = (
            PARENTHESIZED_AUTHOR_YEAR_START_PATTERN.match(
                line
            )
            is not None
        )

        if starts_reference:
            if current_lines:
                references.append(
                    build_reference(
                        label=None,
                        raw_text=" ".join(
                            current_lines
                        ),
                    )
                )

            current_lines = [line]

        elif current_lines:
            current_lines.append(line)

    if current_lines:
        references.append(
            build_reference(
                label=None,
                raw_text=" ".join(current_lines),
            )
        )

    return references


def extract_author_year_references(lines):
    references = []
    current_lines = []

    for line in lines:
        year_starts_line = (
            YEAR_AT_LINE_START_PATTERN.match(line)
            is not None
        )

        is_new_reference = (
            AUTHOR_YEAR_START_PATTERN.match(line)
            is not None
        )

        if year_starts_line and current_lines:
            author_line = current_lines.pop()

            if current_lines:
                references.append(
                    build_reference(
                        label=None,
                        raw_text=" ".join(current_lines),
                    )
                )

            current_lines = [author_line, line]

        elif is_new_reference:
            wrapped_author_lines = []

            while (
                current_lines
                and not current_lines[-1].endswith(
                    (".", "?", "!")
                )
            ):
                wrapped_author_lines.insert(
                    0,
                    current_lines.pop(),
                )

            if current_lines:
                references.append(
                    build_reference(
                        label=None,
                        raw_text=" ".join(current_lines),
                    )
                )

            current_lines = wrapped_author_lines + [line]

        elif current_lines:
            current_lines.append(line)

        else:
            current_lines = [line]

    if current_lines:
        references.append(
            build_reference(
                label=None,
                raw_text=" ".join(current_lines),
            )
        )

    return references





