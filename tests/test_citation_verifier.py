from arxit.citation_verifier import (
    collect_unique_arxiv_ids,
)
from arxit.models import Reference, ArxivMetadata, ArxivCitationResult
import arxit.citation_verifier as verifier
import pytest
import httpx
from arxit.citation_verifier import (find_arxiv_title_mismatches, collect_unique_arxiv_ids, chunk_arxiv_ids, fetch_reference_metadata, verify_arxiv_references, match_reference_metadata, find_unresolved_arxiv_citations, find_year_mismatches, audit_arxiv_citations)



def test_find_arxiv_verification_errors():
    reference = Reference(
        label="7",
        raw_text="Example unavailable paper.",
        arxiv_id="1706.03762",
    )

    results = [
        ArxivCitationResult(
            reference=reference,
            metadata=None,
            error="The read operation timed out",
        ),
    ]

    findings = (
        verifier.find_arxiv_verification_errors(
            results
        )
    )

    assert len(findings) == 1
    assert findings[0].finding_type == (
        "arxiv_verification_error"
    )
    assert findings[0].message == (
        "Reference 7 could not be verified because "
        "arXiv returned an error: "
        "The read operation timed out."
    )
    assert findings[0].reference is reference



def test_verify_arxiv_references_continues_after_batch_timeout(monkeypatch):
    successful_reference = Reference(
        label="1",
        raw_text="Successful paper.",
        arxiv_id="1706.03762",
    )
    timed_out_reference = Reference(
        label="2",
        raw_text="Slow paper.",
        arxiv_id="1810.04805",
    )

    successful_metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="Example summary",
        authors=["Example Author"],
        published="2017-06-12T17:57:34Z",
        updated="2017-06-12T17:57:34Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    monkeypatch.setattr(
        verifier,
        "chunk_arxiv_ids",
        lambda arxiv_ids, batch_size: [
            ["1706.03762"],
            ["1810.04805"],
        ],
    )

    def fake_fetch(batch):
        if batch == ["1810.04805"]:
            request = httpx.Request(
                "GET",
                "https://export.arxiv.org/api/query",
            )
            raise httpx.ReadTimeout(
                "The read operation timed out",
                request=request,
            )

        return "<feed>successful</feed>"

    monkeypatch.setattr(
        verifier,
        "fetch_arxiv_metadata_batch_xml",
        fake_fetch,
    )
    monkeypatch.setattr(
        verifier,
        "parse_arxiv_metadata_batch",
        lambda xml_text: [successful_metadata],
    )

    results = verify_arxiv_references(
        [
            successful_reference,
            timed_out_reference,
        ]
    )

    assert len(results) == 2
    assert results[0].metadata is successful_metadata
    assert results[0].error is None
    assert results[1].metadata is None
    assert results[1].error == (
        "The read operation timed out"
    )





def test_find_arxiv_title_mismatch():
    reference = Reference(
        label="5",
        raw_text=(
            "Vaswani et al. Convolutional Networks "
            "for Image Classification. 2017. "
            "arXiv:1706.03762."
        ),
        year=2017,
        arxiv_id="1706.03762",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    results = [
        ArxivCitationResult(
            reference=reference,
            metadata=metadata,
        )
    ]

    findings = find_arxiv_title_mismatches(
        results
    )

    assert len(findings) == 1
    assert findings[0].finding_type == (
        "arxiv_title_mismatch"
    )
    assert findings[0].message == (
        "Reference 5 may contain the wrong title "
        "for arXiv ID 1706.03762. "
        "arXiv reports: Attention Is All You Need."
    )






def test_fetch_reference_metadata_uses_chunks(monkeypatch):
    references = [
        Reference(
            label=str(index),
            raw_text=f"Paper {index}.",
            arxiv_id=f"2401.{index:05d}",
        )
        for index in range(1, 6)
    ]

    requested_batches = []

    def fake_fetch(arxiv_ids):
        requested_batches.append(arxiv_ids)
        return ",".join(arxiv_ids)

    def fake_parse(xml_text):
        return [
            f"metadata:{arxiv_id}"
            for arxiv_id in xml_text.split(",")
        ]

    monkeypatch.setattr(
        verifier,
        "fetch_arxiv_metadata_batch_xml",
        fake_fetch,
    )
    monkeypatch.setattr(
        verifier,
        "parse_arxiv_metadata_batch",
        fake_parse,
    )

    results = fetch_reference_metadata(
        references,
        batch_size=2,
    )

    assert requested_batches == [
        ["2401.00001", "2401.00002"],
        ["2401.00003", "2401.00004"],
        ["2401.00005"],
    ]
    assert len(results) == 5






def test_chunk_arxiv_ids():
    arxiv_ids = [
        "1000.00001",
        "1000.00002",
        "1000.00003",
        "1000.00004",
        "1000.00005",
    ]

    assert chunk_arxiv_ids(
            arxiv_ids, batch_size=2) == [
            ["1000.00001", "1000.00002"],
            ["1000.00003", "1000.00004"],
            ["1000.00005"],
        ]


def test_chunk_arxiv_ids_rejects_invalid_size():
    with pytest.raises(ValueError, match="Batch size must be positive"):
        chunk_arxiv_ids(["1706.03762"], batch_size =0 )



def test_audit_arxiv_citations_combines_findings(monkeypatch):
    unresolved_reference = Reference(
        label="1",
        raw_text="Unknown paper.",
        arxiv_id="1706.99999",
    )

    wrong_year_reference = Reference(
        label="2",
        raw_text="Attention paper. 2019.",
        year=2019,
        arxiv_id="1706.03762",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    results = [
        ArxivCitationResult(
            reference=unresolved_reference,
            metadata=None,
        ),
        ArxivCitationResult(
            reference=wrong_year_reference,
            metadata=metadata,
        ),
    ]

    monkeypatch.setattr(
        verifier,
        "verify_arxiv_references",
        lambda references: results,
    )

    findings = audit_arxiv_citations([unresolved_reference, wrong_year_reference])

    assert [finding.finding_type for finding in findings] == [
        "unresolved_arxiv_citation",
        "arxiv_year_mismatch",
        "arxiv_title_mismatch"
    ]



def test_find_year_mismatch():
    reference = Reference(
        label="5",
        raw_text=(
            "Vaswani et al. Attention Is All You Need. "
            "arXiv:1706.03762, 2019."
        ),
        year=2019,
        arxiv_id="1706.03762",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    results = [
        ArxivCitationResult(
            reference=reference,
            metadata=metadata,
        )
    ]

    findings = find_year_mismatches(results)

    assert len(findings) == 1
    assert findings[0].finding_type == (
        "arxiv_year_mismatch"
    )
    assert findings[0].message == (
        "Reference 5 cites arXiv ID 1706.03762 "
        "as 2019, but arXiv reports 2017."
    )
    assert findings[0].reference == reference





def test_find_unresolved_arxiv_citations():
    unresolved_reference = Reference(
        label="12",
        raw_text=(
            "Example Author. Unknown Paper. "
            "arXiv:9999.99999."
        ),
        arxiv_id="9999.99999",
    )

    results = [
        ArxivCitationResult(
            reference=unresolved_reference,
            metadata=None,
        )
    ]

    findings = find_unresolved_arxiv_citations(
        results
    )

    assert len(findings) == 1
    assert findings[0].finding_type == (
        "unresolved_arxiv_citation"
    )
    assert findings[0].message == (
        "arXiv ID 9999.99999 could not be resolved."
    )
    assert findings[0].reference == (
        unresolved_reference
    )


def test_matching_year_creates_no_finding():
    reference = Reference(
        label="5",
        raw_text=(
            "Vaswani et al. Attention Is All You Need. "
            "arXiv:1706.03762, 2017."
        ),
        year=2017,
        arxiv_id="1706.03762",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    results = [
        ArxivCitationResult(
            reference=reference,
            metadata=metadata,
        )
    ]

    assert find_year_mismatches(results) == []

    


def test_resolved_arxiv_citation_creates_no_finding():
    reference = Reference(
        label="1",
        raw_text="Attention paper.",
        arxiv_id="1706.03762",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    results = [
        ArxivCitationResult(
            reference=reference,
            metadata=metadata,
        )
    ]

    assert find_unresolved_arxiv_citations(results) == []





def test_verify_arxiv_references(monkeypatch):
    reference = Reference(
        label="1",
        raw_text="Attention paper.",
        arxiv_id="1706.03762",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )


    def fake_fetch(batch):
        assert batch == ["1706.03762"]
        return "<feed>fake</feed>"

    def fake_parse(xml_text):
        assert xml_text == "<feed>fake</feed>"
        return [metadata]

    monkeypatch.setattr(
        verifier,
        "fetch_arxiv_metadata_batch_xml",
        fake_fetch,
    )
    monkeypatch.setattr(
        verifier,
        "parse_arxiv_metadata_batch",
        fake_parse,
    )

    results = verify_arxiv_references(
        [reference]
    )

    assert len(results) == 1
    assert results[0].reference == reference
    assert results[0].metadata == metadata


def test_match_reference_metadata():
    resolved_reference = Reference(
        label="1",
        raw_text="Attention paper.",
        arxiv_id="1706.03762",
    )
    missing_reference = Reference(
        label="2",
        raw_text="Unknown paper.",
        arxiv_id="9999.99999",
    )

    metadata = ArxivMetadata(
        title="Attention Is All You Need",
        summary="A Transformer architecture.",
        authors=["Ashish Vaswani"],
        published="2017-06-12T17:57:34Z",
        updated="2023-08-02T00:41:18Z",
        categories=["cs.CL"],
        arxiv_id="1706.03762v7",
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    results = match_reference_metadata(
        [resolved_reference, missing_reference],
        [metadata],
    )

    assert len(results) == 2

    assert results[0].reference == resolved_reference
    assert results[0].metadata == metadata

    assert results[1].reference == missing_reference
    assert results[1].metadata is None




def test_fetch_reference_metadata_uses_one_batch(monkeypatch):
    references = [
        Reference(
            label="1",
            raw_text="First paper.",
            arxiv_id="1302.4389",
        ),
        Reference(
            label="2",
            raw_text="Repeated paper.",
            arxiv_id="1302.4389",
        ),
        Reference(
            label="3",
            raw_text="Another paper.",
            arxiv_id="1706.03762",
        ),
    ]

    expected_metadata = ["first metadata", "second metadata"]

    def fake_fetch(arxiv_ids):
        assert arxiv_ids == [
            "1302.4389",
            "1706.03762",
        ]
        return "<feed>batch response</feed>"

    def fake_parse(xml_text):
        assert xml_text == "<feed>batch response</feed>"
        return expected_metadata

    monkeypatch.setattr(
        verifier,
        "fetch_arxiv_metadata_batch_xml",
        fake_fetch,
    )
    monkeypatch.setattr(
        verifier,
        "parse_arxiv_metadata_batch",
        fake_parse,
    )

    result = fetch_reference_metadata(references)

    assert result == expected_metadata


def test_fetch_reference_metadata_skips_empty_batch(
    monkeypatch,
):
    references = [
        Reference(
            label="1",
            raw_text="No arXiv identifier.",
        )
    ]

    def fail_if_called(arxiv_ids):
        raise AssertionError(
            "The arXiv API should not be called"
        )

    monkeypatch.setattr(
        verifier,
        "fetch_arxiv_metadata_batch_xml",
        fail_if_called,
    )

    assert fetch_reference_metadata(references) == []





def test_collect_unique_arxiv_ids():
    references = [
        Reference(
            label="1",
            raw_text="First paper. arXiv:1302.4389.",
            arxiv_id="1302.4389",
        ),
        Reference(
            label="2",
            raw_text="A reference without an arXiv ID.",
        ),
        Reference(
            label="3",
            raw_text="Repeated paper. arXiv:1302.4389.",
            arxiv_id="1302.4389",
        ),
        Reference(
            label="4",
            raw_text="Another paper. arXiv:1706.03762.",
            arxiv_id="1706.03762",
        ),
    ]

    assert collect_unique_arxiv_ids(references) == [
        "1302.4389",
        "1706.03762",
    ]


def test_collect_unique_arxiv_ids_returns_empty_list():
    references = [
        Reference(
            label="1",
            raw_text="A reference without an arXiv ID.",
        )
    ]

    assert collect_unique_arxiv_ids(references) == []