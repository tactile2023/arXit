import re
from .reference_parser import (extract_year, extract_arxiv_id, extract_doi, extract_url)
from .models import Reference




REFERENCE_START_PATTERN = re.compile(
    r"^\[(\d+)\]\s*(.*)$"
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
    


def extract_references(sections):
    reference_section = next(
        (
            section
            for section in sections
            if section.title.lower()
            in {"references", "bibliography"}
        ),
        None,
    )

    if reference_section is None:
        return []

    lines = [
        raw_line.strip()
        for raw_line in reference_section.text.splitlines()
        if raw_line.strip()
    ]

    has_numbered_references = any(
        REFERENCE_START_PATTERN.match(line)
        for line in lines
    )

    if has_numbered_references:
        return extract_numbered_references(lines)

    return extract_author_year_references(lines)


def extract_numbered_references(lines):
    references = []
    current_label = None
    current_lines = []

    for line in lines:
        match = REFERENCE_START_PATTERN.match(line)

        if match:
            if current_label is not None:
                references.append(
                    build_reference(
                        label=current_label,
                        raw_text=" ".join(current_lines),
                    )
                )

            current_label = match.group(1)
            current_lines = [match.group(2).strip()]

        elif current_label is not None:
            current_lines.append(line)

    if current_label is not None:
        references.append(
            build_reference(
                label=current_label,
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





