import re

MIN_TITLE_TOKENS= 4
TITLE_MISMATCH_THRESHOLD = .5

def is_title_mismatch(authoritative_title: str, reference_text: str) -> bool:
    title_tokens = normalize_title_text(authoritative_title).split()

    if len(title_tokens) < MIN_TITLE_TOKENS: return False

    coverage = title_token_coverage(authoritative_title, reference_text)

    return coverage < TITLE_MISMATCH_THRESHOLD





def normalize_title_text(text: str) -> str:
    normalized = text.lower()

    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        normalized,
    )

    return " ".join(normalized.split())


def title_token_coverage(authoritative_title: str, reference_text: str) -> float:
    title_tokens = normalize_title_text(authoritative_title).split()

    reference_tokens = set(normalize_title_text(reference_text).split())

    if not title_tokens:
        return 0.0

    matching_tokens = sum(token in reference_tokens for token in title_tokens)

    return matching_tokens / len(title_tokens)