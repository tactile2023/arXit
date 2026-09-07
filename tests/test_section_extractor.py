from arxit.models import ParsedPage
from arxit.section_extractor import extract_sections


def test_numbered_reference_lines_do_not_end_references():
    pages = [
        ParsedPage(
            page_number=6,
            text=(
                "References\n"
                "1. First Author. A long citation. 2020.\n"
                "7. Druglib.com - Drug Information, "
                "Research, Clinical Trials, News\n"
                "8. Falk, Kim. Practical recommender "
                "systems. 2019.\n"
                "12 BOUMEDIENE HAMZI\n"
                "[13] Another Author. Another paper. 2021."
            ),
        )
    ]

    sections = extract_sections(pages)

    assert len(sections) == 1
    assert sections[0].title == "References"
    assert "7. Druglib.com" in sections[0].text
    assert "12 BOUMEDIENE HAMZI" in sections[0].text
    assert "[13] Another Author" in sections[0].text



def test_does_not_treat_decimal_prose_as_heading():
    pages = [
        ParsedPage(
            page_number=9,
            text=(
                "4 Experiments\n"
                "The feature-based approach performs within\n"
                "0.3 F1 behind fine-tuning the entire model. This\n"
                "demonstrates the effectiveness of BERT."
            ),
        ),
    ]

    sections = extract_sections(pages)

    assert [section.title for section in sections] == [
        "Experiments",
    ]

    assert (
        "0.3 F1 behind fine-tuning the entire model. This"
        in sections[0].text
    )



def test_references_end_at_unnumbered_lettered_appendix():
    pages = [
        ParsedPage(
            page_number=12,
            text=(
                "References\n"
                "Yukun Zhu et al. 2015. Aligning books and movies.\n"
                "Appendix for “BERT: Pre-training of Deep "
                "Bidirectional Transformers”\n"
                "We organize the appendix into three sections.\n"
                "A Additional Details for BERT\n"
                "The pre-training procedure follows."
            ),
        ),
    ]

    sections = extract_sections(pages)

    assert sections[0].title == "References"
    assert sections[0].text == (
        "Yukun Zhu et al. 2015. Aligning books and movies."
    )

    assert "Appendix for" not in sections[0].text
    assert "A Additional Details for BERT" not in sections[0].text



def test_extract_sections_finds_lettered_appendix_titles():
    pages = [
        ParsedPage(
            page_number=9,
            text=(
                "References\n"
                "[50] K. Simonyan and A. Zisserman. "
                "Very deep convolutional networks."
            ),
        ),
        ParsedPage(
            page_number=10,
            text=(
                "A. Object Detection Baselines\n"
                "Our detection method is based on Faster R-CNN [32].\n"
                "The experiment continues here."
            ),
        ),
        ParsedPage(
            page_number=11,
            text=(
                "B. Object Detection on COCO\n"
                "We evaluated the model on the COCO dataset."
            ),
        ),
    ]

    sections = extract_sections(pages)

    assert [section.title for section in sections] == [
        "References",
        "Appendix A: Object Detection Baselines",
        "Appendix B: Object Detection on COCO",
    ]

    assert sections[0].text == (
        "[50] K. Simonyan and A. Zisserman. "
        "Very deep convolutional networks."
    )

    assert "[32]" in sections[1].text
    assert "[32]" not in sections[0].text


    

def test_extract_sections_finds_lettered_appendix_headings():
    pages = [
        ParsedPage(
            page_number=8,
            text=(
                "Appendix Z\n"
                "A.1 Justification for Metrics\n"
                "Creativity measures novelty and clarity.\n"
                "A.2 Initial Experimental Setup\n"
                "The earlier experiments used a different prompt."
            )
        )
    ]

    sections = extract_sections(pages)
    assert [section.title for section in sections] == [
        "Appendix Z",
        "Justification for Metrics",
        "Initial Experimental Setup"
    ]

def test_does_not_treat_numbered_question_as_heading():
    pages = [
        ParsedPage(
            page_number=1,
            text=(
                "1 Results\n"
                "30 cars were originally on the motorway, how many cars\n"
                "drove through the traffic jam?"
            ),
        )
    ]

    sections = extract_sections(pages)

    assert [section.title for section in sections] == ["Results"]
    assert "30 cars" in sections[0].text


def test_does_not_treat_equation_as_heading():
    pages = [
        ParsedPage(
            page_number=1,
            text=(
                "1 Analysis\n"
                "3 + 5 = 8, 5 + 8 = 13"
            ),
        )
    ]

    sections = extract_sections(pages)

    assert [section.title for section in sections] == ["Analysis"]
    assert "3 + 5 = 8" in sections[0].text


def test_numbered_instructions_are_not_sections():
    pages = [
        ParsedPage(
            page_number=17,
            text=(
                "A.3 Sculpting (Constrained CoT)\n"
                "2. You must NOT use any outside common sense "
                "or real-world knowledge\n"
                "3. You must break down your calculation "
                "step-by-step. Show all intermediate arithmetic."
            ),
        )
    ]

    sections = extract_sections(pages)

    assert len(sections) == 1
    assert sections[0].title == "Sculpting (Constrained CoT)"






def test_extract_sections_does_not_treat_numbered_sentence_as_heading():
    pages = [
        ParsedPage(
            page_number=1,
            text=(
                "1 Methods\n"
                "1 participants completed the study."
            ),
        )
    ]

    sections = extract_sections(pages)

    assert len(sections) == 1
    assert sections[0].text == (
        "1 participants completed the study."
    )




def test_extract_sections_finds_headings():
    pages = [
        ParsedPage(page_number=1,
                   text=(
                       "Abstract\n"
                       "We introduce a new model. \n"
                       "1 Introduction\n"
                       "Machine learning has advanced rapidly."
                   )),
        ParsedPage(
            page_number=2,
            text=(
                "The introduction continues here.\n"
                "2 Methods\n"
                "We trained the model on several datasets."
                )),
        ParsedPage(
            page_number=3,
            text=(
                "The method description continues.\n"
                "References\n"
                "[1] Example Author. Example Paper."
                )),
    ]

    sections = extract_sections(pages)

    assert [section.title for section in sections] == [
        "Abstract",
        "Introduction",
        "Methods",
        "References"
    ]




def test_does_not_treat_author_initial_as_appendix():
    pages = [
        ParsedPage(
            page_number=9,
            text=(
                "References\n"
                "[14] G. Hinton, A. Krizhevsky, and\n"
                "R. Salakhutdinov. Improving neural networks by "
                "preventing co-adaptation.\n"
                "[15] S. Hochreiter and J. Schmidhuber. "
                "Long short-term memory."
            ),
        )
    ]

    sections = extract_sections(pages)

    assert [section.title for section in sections] == [
        "References",
    ]

    assert "R. Salakhutdinov" in sections[0].text
    assert "[15]" in sections[0].text
