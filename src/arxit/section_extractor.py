import re

from .models import PaperSection


NUMBERED_HEADING_PATTERN = re.compile(
    r"^\d{1,2}(?:\.\d{1,2})*\.?\s+(.+)$"
)

APPENDIX_TITLE_PATTERN = re.compile(
    r"^(?:Appendix\s+([A-Z])|([A-Z])\s+Appendix)"
    r"(?:\s*[:-]?\s+(.+))?$",
    re.IGNORECASE,
)

APPENDIX_FOR_PATTERN = re.compile(
    r"^Appendix\s+for\s+(.+)$",
    re.IGNORECASE,
)

APPENDIX_SUBHEADING_PATTERN = re.compile(
    r"^[A-Z]\.\d{1,2}(?:\.\d{1,2})*\.?\s+(.+)$"
)

LETTERED_APPENDIX_TITLE_PATTERN = re.compile(
    r"^([A-Z])\.?\s+(.+)$"
)

KNOWN_HEADINGS = {
    "abstract",
    "references",
    "bibliography",
    "acknowledgments",
    "acknowledgements",
    "appendix",
    "supplementary material",
    "supplemental material",
}


def find_heading_title(line, current_title=None):
    if line.lower() in KNOWN_HEADINGS:
        return line.title()

    appendix_for_match = APPENDIX_FOR_PATTERN.match(line)

    if (
        appendix_for_match
        and current_title is not None
        and current_title.lower()
        in {"references", "bibliography"}
    ):
        description = appendix_for_match.group(1).strip()
        return f"Appendix: {description}"

    appendix_title_match = APPENDIX_TITLE_PATTERN.match(line)

    if appendix_title_match:
        letter = (
            appendix_title_match.group(1)
            or appendix_title_match.group(2)
        )
        description = appendix_title_match.group(3)

        title = f"Appendix {letter.upper()}"

        if description:
            title = f"{title}: {description.strip()}"

        return title


    lettered_appendix_match = (
    LETTERED_APPENDIX_TITLE_PATTERN.match(line)
)

    if lettered_appendix_match and current_title is not None:
        letter = lettered_appendix_match.group(1)
        candidate = (
            lettered_appendix_match.group(2).strip()
        )

        current_title_lower = current_title.lower()
        expected_letter = None

        if (
            current_title_lower
            in {"references", "bibliography", "appendix"}
            or current_title_lower.startswith("appendix:")
        ):
            expected_letter = "A"

        else:
            previous_appendix_match = re.match(
                r"^appendix\s+([A-Z])(?:\s*:|$)",
                current_title,
                re.IGNORECASE,
            )

            if previous_appendix_match:
                previous_letter = (
                    previous_appendix_match
                    .group(1)
                    .upper()
                )

                if previous_letter != "Z":
                    expected_letter = chr(
                        ord(previous_letter) + 1
                    )

        looks_like_title = (
            candidate
            and candidate[0].isupper()
            and not candidate.endswith((".", "?", "!"))
            and "," not in candidate
            and re.search(
                r"\b(?:19|20)\d{2}\b",
                candidate,
            )
            is None
            and len(candidate.split()) <= 12
        )

        if letter == expected_letter and looks_like_title:
            return f"Appendix {letter}: {candidate}"

    appendix_subheading_match = APPENDIX_SUBHEADING_PATTERN.match(line)

    if appendix_subheading_match:
        candidate = appendix_subheading_match.group(1).strip()

        if candidate.endswith((".", "?", "!")):
            return None

        return candidate




    match = NUMBERED_HEADING_PATTERN.match(line)

    if match: 
        candidate = match.group(1).strip()

        if not candidate[0].isalpha():
            return None

        if candidate[0].islower():
            return None

        numbered_list_item = (
            re.match(r"^\d{1,2}\.\s+", line) is not None
        )

        if numbered_list_item and (
            len(candidate.split()) > 8 or ". " in candidate
        ):
            return None

        if candidate.endswith((".", "?", "!")):
            return None

        return candidate

    return None





def extract_sections(pages):
    sections = []

    current_title = None
    current_lines = []
    start_page = None
    end_page = None

    for page in pages:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            heading_title = find_heading_title(line, current_title)

            if heading_title is not None:
                if current_title is not None:
                    sections.append(
                        PaperSection(
                            title= current_title,
                            text="\n".join(current_lines),
                            start_page=start_page,
                            end_page=end_page
                        )
                    )

                current_title = heading_title
                current_lines = []
                start_page = page.page_number
                end_page = page.page_number

            elif current_title is not None:
                current_lines.append(line)
                end_page = page.page_number

    if current_title is not None:
        sections.append(
            PaperSection(
                title=current_title,
                text="\n".join(current_lines),
                start_page=start_page,
                end_page=end_page
            )
        )

    return sections