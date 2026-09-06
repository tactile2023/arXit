from arxit.title_matcher import (
    normalize_title_text,
    title_token_coverage, is_title_mismatch
)


def test_matching_title_is_not_mismatch():
    assert is_title_mismatch(
        "Attention Is All You Need",
        (
            "Vaswani et al. Attention Is All You Need. "
            "2017.")) is False


def test_unrelated_title_is_mismatch():
    assert is_title_mismatch(
        "Attention Is All You Need",
        ("Vaswani et al. Convolutional Networks "
            "for Image Classification. 2017.")) is True


def test_short_title_is_not_flagged():
    assert is_title_mismatch("BERT", "Devlin et al. BART. 2019.") is False




def test_normalize_title_text():
    assert normalize_title_text("Attention Is All You Need: A Study!") == "attention is all you need a study"


def test_title_token_coverage_for_matching_title():
    coverage = title_token_coverage(
        "Attention Is All You Need",
        (
            "A. Vaswani et al. Attention Is All You Need. "
            "2017. arXiv:1706.03762."
        ),
    )

    assert coverage == 1.0 #coverage meaning % match


def test_title_token_coverage_for_wrong_title():
    coverage = title_token_coverage(
        "Attention Is All You Need",
        (
            "A. Vaswani et al. Convolutional Networks "
            "for Image Classification. 2017."
        ),
    )

    assert coverage < 0.5