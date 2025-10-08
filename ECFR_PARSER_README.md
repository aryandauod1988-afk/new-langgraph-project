# ECFR XML Parser

This tool extracts sections from ECFR (Electronic Code of Federal Regulations) XML documents and saves them as separate JSON and TXT files.

## Features

- Parses ECFR XML documents from URLs or local files
- Identifies sections by HEAD tags containing section numbers (e.g., "§ 4.13", "§ 4.14")
- Creates two files for each section:
  - **JSON file**: Contains metadata including section name, citation, permalink, and raw XML
  - **TXT file**: Contains the text content, or "table" placeholder for sections with tables

## Usage

### Command Line Script

```bash
# Extract from URL (default ECFR title 38)
python extract_ecfr_sections.py

# Extract from local XML file
python extract_ecfr_sections.py --xml-file path/to/your/file.xml

# Specify custom output directory
python extract_ecfr_sections.py --output-dir my_sections

# Extract from different URL
python extract_ecfr_sections.py --url "https://example.com/other-ecfr.xml"
```

### Python API

```python
from agent.ecfr_parser import ECFRParser

# Initialize parser
parser = ECFRParser(output_dir="my_sections")

# Process from URL
sections_count = parser.process_url("https://www.govinfo.gov/bulkdata/ECFR/title-38/ECFR-title38.xml")

# Process from XML content
with open("sample.xml", "r") as f:
    xml_content = f.read()
sections_count = parser.process_xml_content(xml_content, "sample.xml")
```

## Output Format

### JSON Files (e.g., `section_4_13.json`)
```json
{
  "section_name": "section_4_13",
  "section_citation": "§ 4.13 Effect of change of diagnosis.",
  "permalink": "https://example.com/file.xml#section_4_13",
  "raw_xml": "<SECTION>...</SECTION>"
}
```

### TXT Files (e.g., `section_4_13.txt`)
- For regular sections: Contains the extracted text content
- For sections with tables: Contains only the word "table"

## Section Detection

The parser identifies sections by searching for `<HEAD>` elements that contain section numbers matching the pattern `§ X.Y` where:
- X is one or more digits
- Y is one or more digits
- Examples: "§ 4.13", "§ 10.25", "§ 123.456"

## Requirements

- Python 3.9+
- Standard library modules: `xml.etree.ElementTree`, `urllib.request`, `json`, `os`, `re`

## Testing

Run the tests with:
```bash
make test
```

Or specifically test the ECFR parser:
```bash
python -m pytest tests/unit_tests/test_ecfr_parser.py -v
```

## Example

Given an XML structure like:
```xml
<ECFR>
  <TITLE>
    <PART>
      <SECTION>
        <HEAD>§ 4.13 Effect of change of diagnosis.</HEAD>
        <P>This section describes...</P>
      </SECTION>
    </PART>
  </TITLE>
</ECFR>
```

The parser will create:
- `section_4_13.json` with metadata and raw XML
- `section_4_13.txt` with the extracted text content