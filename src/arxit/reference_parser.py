import re
from datetime import datetime, timezone


MODERN_ARXIV_ID_PATTERN = re.compile(
    r"(?:arxiv\s*:\s*|arxiv\.org/(?:abs|pdf)/)"
    r"(\d{4}\.\d{4,5}(?:v\d+)?)",
    re.IGNORECASE,
)

LEGACY_ARXIV_ID_PATTERN = re.compile(
    r"(?:arxiv\s*:\s*|arxiv\.org/(?:abs|pdf)/)"
    r"([a-z][a-z0-9.-]*/\d{7}(?:v\d+)?)",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r"(?<!\d)(\d{4})(?!\d)")
MIN_PUBLICATION_YEAR = 1800

DOI_PATTERN = re.compile(
    r"\b(10\.\d{4,9}/[-._;()/:a-z0-9]+)",
    re.IGNORECASE,
)

DOI_PREFIX_SPACE_PATTERN = re.compile(
    r"\b10\.\s+(?=\d{4,9}/)",
    re.IGNORECASE,
)

DOI_SUFFIX_SPACE_PATTERN = re.compile(
    r"(\b10\.\d{4,9}/"
    r"[-._;()/:a-z0-9]*[./])"
    r"\s+(?=\d)",
    re.IGNORECASE,
)



URL_PATTERN = re.compile(
    r'https?://[^\s<>"\']+',
    re.IGNORECASE,
)


def extract_url(raw_text: str) -> str | None:
    match = URL_PATTERN.search(raw_text)

    if match is None:
        return None

    return match.group(0).rstrip(".,;:")


def extract_doi(raw_text: str) -> str | None:
    normalized_text = DOI_PREFIX_SPACE_PATTERN.sub(
        "10.",
        raw_text,
    )

    normalized_text = DOI_SUFFIX_SPACE_PATTERN.sub(
        r"\1",
        normalized_text,
    )

    match = DOI_PATTERN.search(normalized_text)

    if match is None:
        return None

    doi = match.group(1).rstrip(".,;:")

    return doi.lower()


def extract_arxiv_id(raw_text: str) -> str | None:
    for pattern in (MODERN_ARXIV_ID_PATTERN, LEGACY_ARXIV_ID_PATTERN):
        match = pattern.search(raw_text)
        if match: 
            return match.group(1)

    return None



def extract_year(raw_text: str) -> int | None:
    current_year = datetime.now(timezone.utc).year

    for match in YEAR_PATTERN.finditer(raw_text):
        year = int(match.group(1))

        if MIN_PUBLICATION_YEAR <= year <= current_year:
            return year
        
    return None