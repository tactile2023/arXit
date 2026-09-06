import pytest

from arxit.arxiv_parser import (parse_arxiv_metadata, parse_arxiv_metadata_batch)

SAMPLE_XML = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Attention Is 
    All You Need
    </title>

    <summary>
        We introduce the Transformer, an architecture based solely on attention mechanisms.
    </summary>

    <author>
        <name>Monkey See</name>
    </author>

    <author>
        <name>Monkey Do</name>
    </author>

    <published> 2017-06-12T17:57:34Z </published>
    <updated>2023-08-02T00:41:18Z</updated>

    <category term="cs.CL" />
    <category term="cs.LG" />

    <id>http://arxiv.org/abs/1706.03762v7</id>

    <link
        href="https://arxiv.org/abs/1706.03762v7"
        rel="alternate"
        type="text/html"
    />
    <link
        title="pdf"
        href="https://arxiv.org/pdf/1706.03762v7"
        rel="related"
        type="application/pdf"
    />



</entry>
</feed>
"""



BATCH_XML = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Maxout Networks</title>
    <summary>A maxout model.</summary>
    <author><name>Ian Goodfellow</name></author>
    <published>2013-02-18T20:11:11Z</published>
    <updated>2013-02-18T20:11:11Z</updated>
    <category term="cs.LG" />
    <id>http://arxiv.org/abs/1302.4389v4</id>
    <link
      title="pdf"
      href="https://arxiv.org/pdf/1302.4389v4"
    />
  </entry>

  <entry>
    <title>Attention Is All You Need</title>
    <summary>A Transformer architecture.</summary>
    <author><name>Ashish Vaswani</name></author>
    <published>2017-06-12T17:57:34Z</published>
    <updated>2023-08-02T00:41:18Z</updated>
    <category term="cs.CL" />
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <link
      title="pdf"
      href="https://arxiv.org/pdf/1706.03762v7"
    />
  </entry>
</feed>
"""

def test_parse_arxiv_metadata_batch():
    results = parse_arxiv_metadata_batch(BATCH_XML)

    assert len(results) == 2
    assert results[0].arxiv_id == "1302.4389v4"
    assert results[0].title == "Maxout Networks"
    assert results[1].arxiv_id == "1706.03762v7"
    assert results[1].title == "Attention Is All You Need"


def test_parse_arxiv_metadata_batch_returns_empty_list():
    empty_feed = """
    <feed xmlns="http://www.w3.org/2005/Atom">
    </feed>
    """

    assert parse_arxiv_metadata_batch(empty_feed) == []


xml_without_pdf = SAMPLE_XML.replace("""<link
        title="pdf"
        href="https://arxiv.org/pdf/1706.03762v7"
        rel="related"
        type="application/pdf"
    />""","")



def test_parser_extracts_id():
    metadata = parse_arxiv_metadata(SAMPLE_XML)
    assert metadata.arxiv_id == "1706.03762v7"

def test_parser_raises_for_missing_pdf():
    with pytest.raises(ValueError, match="arXiv entry is missing a PDF URL"):
        parse_arxiv_metadata(xml_without_pdf)

def test_parser_extracts_dates():
    metadata = parse_arxiv_metadata(SAMPLE_XML)

    assert metadata.published == "2017-06-12T17:57:34Z"
    assert metadata.updated == "2023-08-02T00:41:18Z"


def test_parser_extracts_authors():
    metadata = parse_arxiv_metadata(SAMPLE_XML)

    assert metadata.authors == [
    "Monkey See",
    "Monkey Do",
    ]

def test_parser_extracts_pdf_url():
    metadata = parse_arxiv_metadata(SAMPLE_XML)
    assert metadata.pdf_url == "https://arxiv.org/pdf/1706.03762v7"


def test_parser_extracts_summary():
    metadata = parse_arxiv_metadata(SAMPLE_XML)

    assert metadata.summary == (

        "We introduce the Transformer, an architecture based solely on attention mechanisms."
    )


def test_parser_extracts_categories():
    metadata = parse_arxiv_metadata(SAMPLE_XML)

    assert metadata.categories == [
        "cs.CL",
        "cs.LG"
    ]


def test_parser_rejects_feed_without_entry():
    emptyfeed = """
    <feed xmlns="http://www.w3.org/2005/Atom">
    </feed>
"""
    with pytest.raises(ValueError):
        parse_arxiv_metadata(emptyfeed)


        
def test_parser_extracts_title():
    metadata = parse_arxiv_metadata(SAMPLE_XML)
    
    assert metadata.title == "Attention Is All You Need"
