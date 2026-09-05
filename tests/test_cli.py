import subprocess
import sys
import arxit.cli as cli
from arxit.models import ArxivMetadata
import httpx
import pytest
from arxit.models import ArxivMetadata, ParsedPage, Finding, Reference
from pypdf.errors import PdfReadError



def test_cli_explains_arxiv_rate_limit(monkeypatch, capsys):
    request = httpx.Request("GET", "https://export.arxiv.org/api/query")
    response=httpx.Response(429, request=request)

    def fake_fetch(arxiv_id):
        raise httpx.HTTPStatusError("Too many requests", request=request, response=response)
    
    monkeypatch.setattr(cli, "fetch_arxiv_metadata_xml", fake_fetch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["arxit", "2507.01019"],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    captured = capsys.readouterr()

    assert error.value.code == 2
    assert "arXiv rate limit reached" in captured.err
    assert "Traceback" not in captured.err





def test_cli_handles_corrup_pdf(monkeypatch, capsys):
    metadata = ArxivMetadata(
        arxiv_id="1706.03762v7",
        title="Example Paper",
        summary="Example summary",
        authors=["Example Author"],
        published="2017-06-12T17:57:34Z",
        updated="2017-06-12T17:57:34Z",
        categories=["cs.CL"],
        pdf_url="https://arxiv.org/pdf/1706.03762v7",
    )

    monkeypatch.setattr(
        cli,
        "fetch_arxiv_metadata_xml",
        lambda arxiv_id: "<feed>fake</feed>",
    )
    monkeypatch.setattr(
        cli,
        "parse_arxiv_metadata",
        lambda xml_text: metadata
    )
    monkeypatch.setattr(
        cli, 
        "download_pdf",
        lambda pdf_url: b"%PDF-corrupt"
    )


    def fake_parse_pdf(pdf_bytes):
            raise PdfReadError("Broken PDF")

    monkeypatch.setattr(cli, "parse_pdf", fake_parse_pdf)
    monkeypatch.setattr(
        sys,
        "argv",
        ["arxit", "1706.03762"],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    captured = capsys.readouterr()

    assert error.value.code == 2
    assert "Could not parse PDF" in captured.err
    assert "Traceback" not in captured.err






def test_cli_handles_network_errors(monkeypatch, capsys):
    def fake_fetch(arxiv_id):
        raise httpx.ConnectError("Connection failed")

    monkeypatch.setattr(cli, "fetch_arxiv_metadata_xml", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["arxit", "1706.03762"])

    with pytest.raises(SystemExit) as error:
        cli.main()

    captured = capsys.readouterr()

    assert error.value.code ==2
    assert "Could not retrieve arXiv metadata" in captured.err

    

def test_cli_displays_metadata(monkeypatch, capsys):
    def fake_fetch(arxiv_id):
        assert arxiv_id == "2401.12345"
        return "<feed>fake XML</feed>"

    def fake_parse(xml_text):
        assert xml_text == "<feed>fake XML</feed>"

        return ArxivMetadata(
            arxiv_id="2401.12345v3",
            title="Example Paper",
            summary="Example summary",
            authors=["First Author", "Second Author"],
            published="2024-01-22T20:20:48Z",
            updated="2024-02-01T00:00:00Z",
            categories=["cs.LG"],
            pdf_url="https://arxiv.org/pdf/2401.12345v3",
        )


    def fake_download(pdf_url):
        assert pdf_url == "https://arxiv.org/pdf/2401.12345v3"
        return b"%PDF-fake"
    
    def fake_parse_pdf(pdf_bytes):
        assert pdf_bytes == b"%PDF-fake"
    
        return[ParsedPage(page_number=1, text="Example paper text")]


    reference = Reference(
        label="7",
        raw_text="Unknown paper. arXiv: 2401.99999.",
        arxiv_id="2401.99999",
        doi="10.9999/missing"
    )

    finding = Finding(finding_type="unresolved_arxiv_citation",
                      message=("arXiv ID 2401.99999 could not be resolved."),
                      reference=reference)

    doi_finding = Finding(finding_type="unresolved_doi_citation",
                          message=("DOI 10.9999/missing could not be resolved."),
                          reference = reference)


    monkeypatch.setattr(cli, "fetch_arxiv_metadata_xml", fake_fetch)
    monkeypatch.setattr(cli, "parse_arxiv_metadata", fake_parse)
    monkeypatch.setattr(
        sys,
        "argv",
        ["arxit", "https://arxiv.org/abs/2401.12345"],
    )
    monkeypatch.setattr(cli, "download_pdf", fake_download)
    monkeypatch.setattr(cli, "parse_pdf", fake_parse_pdf)
    monkeypatch.setattr(cli, "extract_references", lambda sections:[reference])
    monkeypatch.setattr(cli, "audit_arxiv_citations", lambda references: [finding])
    monkeypatch.setattr(cli, "audit_doi_citations", lambda references: [doi_finding])

    cli.main()

    output = capsys.readouterr().out

    assert "arXiv ID: 2401.12345v3" in output
    assert "Title: Example Paper" in output
    assert "Authors: First Author, Second Author" in output
    assert "Pages parsed: 1" in output
    assert "Characters extracted: 18" in output
    assert "Sections found: 0" in output
    assert "References found: 1" in output
    assert "Citation findings: 2" in output
    assert "arXiv ID 2401.99999 could not be resolved." in output
    assert "DOI 10.9999/missing could not be resolved." in output
    


def test_cli_rejects_invalid_input_without_traceback():
    result = subprocess.run(
        ["arxit", "invalid_input"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert "Invalid arXiv identifier" in result.stderr
