from arxit.models import PaperSection
from arxit.reference_extractor import extract_references, extract_numbered_references, extract_author_year_references


def test_reference_includes_extracted_url():
    lines = [
        "[1] Example Author. Example Dataset. "
        "https://example.org/dataset."
    ]

    references = extract_numbered_references(lines)
    assert references[0].url == "https://example.org/dataset"




def test_reference_includes_extracted_doi():
    lines = [
        "[1] Example Author. Example Paper. "
        "doi:10.1038/s41586-021-03819-2."
    ]

    references = extract_numbered_references(lines)
    assert references[0].doi == "10.1038/s41586-021-03819-2"


def test_reference_includes_extracted_arxiv_id():
    lines = [
        "[10] I. J. Goodfellow et al. "
        "Maxout Networks. arXiv: 1302.4389, 2013."
    ]

    references = extract_numbered_references(lines)
    assert references[0].arxiv_id == "1302.4389"



def test_extract_references_when_year_starts_next_line():
    sections = [
        PaperSection(
            title="References",
            text=(
                "Angana Borah and Rada Mihalcea. 2024. Towards implicit\n"
                "bias detection in multi-agent interactions.\n"
                "Aylin Caliskan, Joanna J Bryson, and Arvind Narayanan.\n"
                "2017. Semantics derived automatically from language\n"
                "corpora contain human-like biases. Science, 356:183–186."
            ),
            start_page=8,
            end_page=8,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 2

    assert references[0].label is None
    assert references[0].raw_text == (
        "Angana Borah and Rada Mihalcea. 2024. Towards implicit "
        "bias detection in multi-agent interactions."
    )

    assert references[1].label is None
    assert references[1].raw_text == (
        "Aylin Caliskan, Joanna J Bryson, and Arvind Narayanan. "
        "2017. Semantics derived automatically from language "
        "corpora contain human-like biases. Science, 356:183–186."
    )









def test_extract_references_from_author_year_entries():
    sections = [
        PaperSection(
            title="References",
            text=(
                "Solomon E Asch. 1956. Studies of independence and\n"
                "conformity: I. a minority of one against a unanimous\n"
                "majority. Psychological monographs, 70(9):1.\n"
                "X Bai, A Wang, I Sucholutsky, and TL Griffiths. 2024.\n"
                "Measuring implicit bias in explicitly unbiased large\n"
                "language models. arXiv preprint arXiv:2402.04105."
            ),
            start_page=6,
            end_page=7,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 2

    assert references[0].label is None
    assert references[0].raw_text == (
        "Solomon E Asch. 1956. Studies of independence and "
        "conformity: I. a minority of one against a unanimous "
        "majority. Psychological monographs, 70(9):1."
    )

    assert references[1].label is None
    assert references[1].raw_text == (
        "X Bai, A Wang, I Sucholutsky, and TL Griffiths. 2024. "
        "Measuring implicit bias in explicitly unbiased large "
        "language models. arXiv preprint arXiv:2402.04105."
    )




def test_extract_references_joins_wrapped_lines():
    sections = [
        PaperSection(
            title="References",
            text=(
                "[1] First Author. First Paper. 2020.\n"
                "Something that continues on another line. 2020.\n"
                "[2] Second Author. Second Paper. 2021."

            ),
            start_page=6,
            end_page=7
        )
    ]
    references = extract_references(sections)

    assert len(references) == 2
    assert references[0].label == "1"
    assert references[0].raw_text == (
        "First Author. First Paper. 2020. "
        "Something that continues on another line. 2020."
    )
    assert references[1].label == "2"
    assert references[1].raw_text == (
        "Second Author. Second Paper. 2021."
    )


def test_extract_references_from_numbered_entries():
    sections = [
        PaperSection(
            title="References",
            text=(
                "[1] First Author. First Paper. 2020.\n"
                "[2] Second Author. Second Paper. 2021."

            ),
            start_page=6,
            end_page=7
        )
    ]
    references = extract_references(sections)

    assert len(references) == 2
    assert references[0].label == "1"
    assert references[0].raw_text == (
        "First Author. First Paper. 2020."
    )
    assert references[1].label == "2"




def test_extract_references_with_wrapped_author_list():
    sections = [
        PaperSection(
            title="References",
            text=(
                "Zhibo Chu, Zichong Wang, and Wenbin Zhang. 2024.\n"
                "Fairness in large language models: A taxonomic survey.\n"
                "Preprint, arXiv:2404.01349.\n"
                "Erica Coppolillo, Giuseppe Manco, and Luca Maria\n"
                "Aiello. 2025. Unmasking conversational bias in AI\n"
                "multiagent systems. Preprint, arXiv:2501.14844."
            ),
            start_page=8,
            end_page=9,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 2

    assert references[0].raw_text == (
        "Zhibo Chu, Zichong Wang, and Wenbin Zhang. 2024. "
        "Fairness in large language models: A taxonomic survey. "
        "Preprint, arXiv:2404.01349."
    )

    assert references[1].raw_text == (
        "Erica Coppolillo, Giuseppe Manco, and Luca Maria "
        "Aiello. 2025. Unmasking conversational bias in AI "
        "multiagent systems. Preprint, arXiv:2501.14844."
    )



def test_numbered_reference_includes_extracted_year():
    lines = [
        "[1] K. He, X. Zhang, S. Ren, and J. Sun. "
        "Deep residual learning. 2016."
    ]

    references = extract_numbered_references(lines)
    assert references[0].year == 2016




def test_author_year_reference_includes_extracted_year():
    lines = [
        "Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. "
        "2019. BERT: Pre-training of deep bidirectional transformers."
    ]

    references = extract_author_year_references(lines)

    assert references[0].year == 2019