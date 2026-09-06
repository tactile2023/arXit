from dataclasses import dataclass

@dataclass
class ArxivMetadata:
    title: str
    summary: str
    authors: list[str]
    published: str
    updated: str
    categories: list[str]
    arxiv_id: str
    pdf_url: str


@dataclass
class Reference:
    label: str | None
    raw_text: str
    year: int | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    url: str | None = None


@dataclass
class ParsedPage:
    page_number: int
    text: str



@dataclass
class PaperSection:
    title: str
    text: str
    start_page: str
    end_page: str


@dataclass
class ParsedPaper:
    metadata: ArxivMetadata
    pages: list[ParsedPage]
    sections: list[PaperSection]
    references: list[Reference]




@dataclass
class ArxivCitationResult:
    reference: Reference
    metadata: ArxivMetadata | None


@dataclass
class Finding: 
    finding_type: str
    message: str
    reference: Reference



@dataclass
class DoiCitationResult:
    reference: Reference
    metadata: dict | None
    agency: str | None = None



