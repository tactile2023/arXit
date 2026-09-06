# arXit
arXit is an evidence-backed scientific paper integrity auditor for machine-learning papers on arXiv. 


## Motive
With there being a rise in papers submitted to academic journals, top conferences, and publishings on arXiv with AI slop, arXit was inspired to help readers evaluate papers by identifying potential integrity and reproducibility issues to filter submitted "AI Slop."


## Current Capabilities
arXit can:

- Normalize modern and legacy arXiv identifiers and URLs
- Retrieve paper metadata from the arXiv API
- Download and parse paper PDFs
- Preserve extracted text by page
- Detect numbered sections, subsections, and common appendix formats
- Extract numbered and unnumbered references
- Join references split across PDF lines
- Extract years, arXiv IDs, DOIs, and URLs from references
- Resolve cited arXiv identifiers in batches
- Route DOI lookups to Crossref or DataCite
- Detect unresolved arXiv and DOI citations
- Flag potential citation-year mismatches
- Flag potential citation-title mismatches
- Deduplicate external metadata requests
- Continue auditing when an individual citation service times out
- Display evidence-backed citation findings through the CLI

Academic PDF formatting varies, so unusual layouts may require additional rules. 


## Planned Capabilities
- Detect numerical inconsistencies across paper sections
- Audit reproducibility information
- Support local draft PDF input
- Detect potential semantic contradictions
- Generate JSON and HTML reports
- Evaluate accuracy using a manually annotated benchmark

## Installation
```bash
git clone git@github.com:tactile2023/arXit.git
cd arXit
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the tests:
```bash
pytest
