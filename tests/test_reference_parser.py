from arxit.reference_parser import (
    extract_arxiv_id, extract_year, extract_doi, extract_url)


def test_extracts_doi_split_after_prefix():
    raw_text = (
        "Example paper. "
        "https://doi.org/10. 1007/example"
    )

    assert extract_doi(raw_text) == (
        "10.1007/example"
    )


def test_extracts_doi_split_inside_suffix():
    raw_text = (
        "Visual Analytics in Deep Learning. "
        "https://doi.org/10.1109/TVCG. "
        "2018.2843369"
    )

    assert extract_doi(raw_text) == (
        "10.1109/tvcg.2018.2843369"
    )



def test_extract_url():
    raw_text = (
        "Example project. Code available at "
        "https://github.com/example/project"
    )

    assert extract_url(raw_text) == "https://github.com/example/project"


def test_extract_url_removes_trailing_punctuation():
    raw_text = (
        "Dataset available at "
        "https://example.org/dataset."
    )

    assert extract_url(raw_text) == "https://example.org/dataset"


def test_extract_url_with_path_and_query():
    raw_text = (
        "See https://example.org/search?q=machine-learning&year=2024"
    )

    assert extract_url(raw_text) == (
        "https://example.org/search?q=machine-learning&year=2024"
    )


def test_extract_url_returns_none_when_missing():
    raw_text = "Example Author. Example Paper. 2024."

    assert extract_url(raw_text) is None



def test_extract_doi_with_label():
    raw_text = (
        "Vasista et al. Exoplanet Research. "
        "doi:10.13021/MARS/15158."
    )

    assert extract_doi(raw_text) == "10.13021/mars/15158"


def test_extract_doi_from_url():
    raw_text = (
        "Example paper. "
        "https://doi.org/10.1038/s41586-021-03819-2"
    )

    assert extract_doi(raw_text) == "10.1038/s41586-021-03819-2"


def test_extract_doi_without_label():
    raw_text = "Example paper. 10.1145/3290605.3300233."

    assert extract_doi(raw_text) == "10.1145/3290605.3300233"


def test_extract_doi_removes_trailing_punctuation():
    raw_text = "Available at doi:10.1000/example.123,"

    assert extract_doi(raw_text) == "10.1000/example.123"


def test_extract_doi_returns_none_when_missing():
    raw_text = "Example Author. Example Paper. 2024."

    assert extract_doi(raw_text) is None



def test_extract_year_from_reference():
    raw_text = (
        "K. He, X. Zhang, S. Ren, and J. Sun. "
        "Deep residual learning for image recognition. 2016."
    )
    assert extract_year(raw_text) == 2016


def test_extract_year_from_parantheses():
    raw_text = (
        "Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. "
        "(2019). BERT."
    )
    assert extract_year(raw_text) == 2019


def test_extract_year_returns_none_when_missing():
    raw_text = "OpenAI. An example paper without publication date."

    assert extract_year(raw_text) is None

def test_extract_year_rejects_unreasonable_year():
    raw_text = "Example Author. Example Paper. 3025."

    assert extract_year(raw_text) is None



from arxit.reference_parser import extract_arxiv_id, extract_year


def test_extract_modern_arxiv_id():
    raw_text = "Goodfellow et al. Maxout Networks. arXiv:1302.4389, 2013."

    assert extract_arxiv_id(raw_text) == "1302.4389"


def test_extract_versioned_arxiv_id():
    raw_text = "Example paper. arXiv:2404.01349v2."

    assert extract_arxiv_id(raw_text) == "2404.01349v2"


def test_extract_arxiv_id_from_url():
    raw_text = "Available at https://arxiv.org/abs/1706.03762."

    assert extract_arxiv_id(raw_text) == "1706.03762"


def test_extract_legacy_arxiv_id():
    raw_text = "Example paper. arXiv:hep-th/9901001."

    assert extract_arxiv_id(raw_text) == "hep-th/9901001"


def test_extract_arxiv_id_returns_none_when_missing():
    raw_text = "Example Author. Example Paper. 2024."

    assert extract_arxiv_id(raw_text) is None