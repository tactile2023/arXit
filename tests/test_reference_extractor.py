from arxit.models import PaperSection
from arxit.reference_extractor import extract_references, extract_numbered_references, extract_author_year_references


def test_numbered_references_reject_false_label_jump():
    sections = [
        PaperSection(
            title="References",
            text=(
                "[43] First Author. First paper. 2018.\n"
                "[44] Hector Zenil. Example chapter, "
                "pages 477–\n"
                "[496] World Scientific, 2011.\n"
                "[45] Second Author. Second paper. 2023."
            ),
            start_page=11,
            end_page=12,
        )
    ]

    references = extract_references(sections)

    assert [
        reference.label
        for reference in references
    ] == [
        "43",
        "44",
        "45",
    ]

    assert references[1].raw_text == (
        "Hector Zenil. Example chapter, "
        "pages 477– [496] World Scientific, 2011."
    )




def test_extracts_parenthesized_author_year_references():
    sections = [
        PaperSection(
            title="References",
            text=(
                "Anderson, T. W. (1962). On the "
                "distribution of a statistic.\n"
                "The Annals of Statistics, pages 1–10.\n"
                "Bai, Z. and Saranadasa, H. ( 1996). "
                "Effect of high dimension.\n"
                "Statistica Sinica, pages 311–329.\n"
                "40\n"
                "Chagnon, E. and Pandolfi, R. (2024). "
                "Benchmarking topic models.\n"
                "Natural Language Processing Journal."
            ),
            start_page=40,
            end_page=41,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 3
    assert references[0].year == 1962
    assert references[1].year == 1996
    assert references[2].year == 2024
    assert " 40 " not in (
        f" {references[2].raw_text} "
    )



def test_year_terminated_references_handle_wrapped_year_and_doi():
    sections = [
        PaperSection(
            title="References",
            text=(
                "Behnke Berit. A Directed Search. "
                "University Hannover,\n"
                "2013.\n"
                "Sylvia Biscoveanu. New Spin. "
                "Journal, 2021. doi:\n"
                "10.1103/example.\n"
                "Joseph Romano. Detection methods. "
                "Journal, 2017. doi: 10.1007/\n"
                "s41114-017-0004-1.\n"
                "Michael Ross. Precision Sensors. "
                "University of Washington,\n"
                "2020."
            ),
            start_page=6,
            end_page=7,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 4

    assert references[0].raw_text == (
        "Behnke Berit. A Directed Search. "
        "University Hannover, 2013."
    )

    assert references[1].raw_text == (
        "Sylvia Biscoveanu. New Spin. "
        "Journal, 2021. doi: "
        "10.1103/example."
    )

    assert references[2].raw_text == (
        "Joseph Romano. Detection methods. "
        "Journal, 2017. doi: 10.1007/ "
        "s41114-017-0004-1."
    )

    assert references[3].raw_text == (
        "Michael Ross. Precision Sensors. "
        "University of Washington, 2020."
    )










def test_year_terminated_references_include_doi_lines():
    sections = [
        PaperSection(
            title="References",
            text=(
                "First Author. First paper. "
                "Journal, 2021. doi:\n"
                "10.1234/first-paper.\n"
                "Second Author. Second paper. "
                "Journal, 2020. doi: "
                "10.1234/second-paper.\n"
                "Third Author. Third paper. "
                "University, 2019."
            ),
            start_page=6,
            end_page=6,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 3

    assert references[0].raw_text == (
        "First Author. First paper. "
        "Journal, 2021. doi: "
        "10.1234/first-paper."
    )

    assert references[1].raw_text == (
        "Second Author. Second paper. "
        "Journal, 2020. doi: "
        "10.1234/second-paper."
    )

    assert references[2].raw_text == (
        "Third Author. Third paper. "
        "University, 2019."
    )







def test_extracts_from_repeated_reference_sections():
    sections = [
        PaperSection(
            title="References",
            text="",
            start_page=6,
            end_page=6,
        ),
        PaperSection(
            title="References",
            text=(
                "Rana Adhikari. Sensitivity and noise "
                "analysis. MIT, 2004.\n"
                "Behnke Berit. A Directed Search for "
                "Gravitational Waves. Hannover, 2013."
            ),
            start_page=6,
            end_page=7,
        ),
    ]

    references = extract_references(sections)

    assert len(references) == 2

    assert references[0].raw_text == (
        "Rana Adhikari. Sensitivity and noise "
        "analysis. MIT, 2004."
    )

    assert references[1].raw_text == (
        "Behnke Berit. A Directed Search for "
        "Gravitational Waves. Hannover, 2013."
    )





def test_extracts_plain_numbered_references():
    sections = [
        PaperSection(
            title="References",
            text=(
                "1. First Author. First paper. (2023)\n"
                "Continuation of the first reference.\n"
                "2. Second Author. Second paper. (2024)"
            ),
            start_page=8,
            end_page=8,
        )
    ]

    references = extract_references(sections)

    assert [reference.label for reference in references] == [
        "1",
        "2",
    ]

    assert references[0].raw_text == (
        "First Author. First paper. (2023) "
        "Continuation of the first reference."
    )

    assert references[1].raw_text == (
        "Second Author. Second paper. (2024)"
    )


def test_extracts_unnumbered_references_ending_with_year():
    sections = [
        PaperSection(
            title="References",
            text=(
                "Anthropic. Claude 4 technical report. "
                "Technical report, Anthropic, 2025.\n"
                "Rahul Arora, Jason Wei, and Rebecca Hicks,\n"
                "Healthbench: Evaluating language models. "
                "arXiv:2505.08775, 2025.\n"
                "12\n"
                "Gemma Team, Thomas Mesnard, and Cassidy Hardin,\n"
                "Gemma: Open models based on Gemini research "
                "and technology. arXiv:2403.08295, 2024.\n"
                "13"
            ),
            start_page=11,
            end_page=13,
        )
    ]

    references = extract_references(sections)

    assert len(references) == 3

    assert references[0].raw_text == (
        "Anthropic. Claude 4 technical report. "
        "Technical report, Anthropic, 2025."
    )

    assert references[1].raw_text == (
        "Rahul Arora, Jason Wei, and Rebecca Hicks, "
        "Healthbench: Evaluating language models. "
        "arXiv:2505.08775, 2025."
    )

    assert references[2].raw_text == (
        "Gemma Team, Thomas Mesnard, and Cassidy Hardin, "
        "Gemma: Open models based on Gemini research "
        "and technology. arXiv:2403.08295, 2024."
    )

    assert all(
        " 12 " not in f" {reference.raw_text} "
        and " 13 " not in f" {reference.raw_text} "
        for reference in references
    )






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