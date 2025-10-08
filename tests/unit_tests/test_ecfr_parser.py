"""Tests for ECFR Parser."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from agent.ecfr_parser import ECFRParser


class TestECFRParser:
    """Test cases for ECFRParser."""

    @pytest.fixture
    def sample_xml(self):
        """Sample ECFR XML data for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<ECFR>
    <TITLE>
        <PART>
            <SECTION>
                <HEAD>§ 4.13 Effect of change of diagnosis.</HEAD>
                <P>This section describes the effect of change of diagnosis.</P>
                <P>Additional content for section 4.13.</P>
            </SECTION>
            <SECTION>
                <HEAD>§ 4.14 Avoidance of pyramiding.</HEAD>
                <P>This section describes avoidance of pyramiding.</P>
                <TABLE>
                    <TR><TD>Cell 1</TD><TD>Cell 2</TD></TR>
                </TABLE>
            </SECTION>
            <SECTION>
                <HEAD>Some other heading without section number</HEAD>
                <P>This should be ignored.</P>
            </SECTION>
            <SECTION>
                <HEAD>§ 4.15 Additional section.</HEAD>
                <P>Another section with content.</P>
            </SECTION>
        </PART>
    </TITLE>
</ECFR>"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_initialization(self, temp_dir):
        """Test parser initialization."""
        parser = ECFRParser(temp_dir)
        assert parser.output_dir == temp_dir
        assert os.path.exists(temp_dir)

    def test_parse_xml(self, sample_xml):
        """Test XML parsing."""
        parser = ECFRParser()
        root = parser.parse_xml(sample_xml)
        assert root.tag == "ECFR"

    def test_find_sections(self, sample_xml):
        """Test section finding."""
        parser = ECFRParser()
        root = parser.parse_xml(sample_xml)
        sections = parser.find_sections(root)

        # Should find 3 sections (4.13, 4.14, 4.15)
        assert len(sections) == 3

        section_names = [name for name, _ in sections]
        assert "section_4_13" in section_names
        assert "section_4_14" in section_names
        assert "section_4_15" in section_names

    def test_extract_text_content(self, sample_xml):
        """Test text content extraction."""
        parser = ECFRParser()
        root = parser.parse_xml(sample_xml)
        sections = parser.find_sections(root)

        # Find section 4.13 (should not have table)
        section_4_13 = next(
            (elem for name, elem in sections if name == "section_4_13"), None
        )
        assert section_4_13 is not None
        text_content = parser.extract_text_content(section_4_13)
        assert "table" not in text_content.lower()
        assert "effect of change of diagnosis" in text_content.lower()

        # Find section 4.14 (should have table)
        section_4_14 = next(
            (elem for name, elem in sections if name == "section_4_14"), None
        )
        assert section_4_14 is not None
        text_content = parser.extract_text_content(section_4_14)
        assert text_content == "table"

    def test_get_section_metadata(self, sample_xml):
        """Test metadata generation."""
        parser = ECFRParser()
        root = parser.parse_xml(sample_xml)
        sections = parser.find_sections(root)

        section_name, section_element = sections[0]  # First section
        metadata = parser.get_section_metadata(
            section_name, section_element, "http://test.url"
        )

        assert metadata["section_name"] == section_name
        assert "section_citation" in metadata
        assert "permalink" in metadata
        assert "raw_xml" in metadata
        assert metadata["permalink"] == f"http://test.url#{section_name}"

    def test_save_section_files(self, temp_dir, sample_xml):
        """Test file saving."""
        parser = ECFRParser(temp_dir)
        root = parser.parse_xml(sample_xml)
        sections = parser.find_sections(root)

        section_name, section_element = sections[0]
        metadata = parser.get_section_metadata(
            section_name, section_element, "http://test.url"
        )
        text_content = parser.extract_text_content(section_element)

        parser.save_section_files(section_name, metadata, text_content)

        # Check JSON file
        json_path = os.path.join(temp_dir, f"{section_name}.json")
        assert os.path.exists(json_path)

        with open(json_path, "r") as f:
            saved_metadata = json.load(f)
        assert saved_metadata == metadata

        # Check TXT file
        txt_path = os.path.join(temp_dir, f"{section_name}.txt")
        assert os.path.exists(txt_path)

        with open(txt_path, "r") as f:
            saved_text = f.read()
        assert saved_text == text_content

    def test_process_xml_content(self, temp_dir, sample_xml):
        """Test complete XML processing."""
        parser = ECFRParser(temp_dir)
        sections_count = parser.process_xml_content(sample_xml, "http://test.url")

        assert sections_count == 3

        # Check that files were created
        expected_files = [
            "section_4_13.json",
            "section_4_13.txt",
            "section_4_14.json",
            "section_4_14.txt",
            "section_4_15.json",
            "section_4_15.txt",
        ]

        for filename in expected_files:
            file_path = os.path.join(temp_dir, filename)
            assert os.path.exists(file_path), f"File {filename} was not created"

        # Verify section with table has "table" as text content
        with open(os.path.join(temp_dir, "section_4_14.txt"), "r") as f:
            content = f.read()
        assert content == "table"

        # Verify section without table has actual text content
        with open(os.path.join(temp_dir, "section_4_13.txt"), "r") as f:
            content = f.read()
        assert content != "table"
        assert "effect of change of diagnosis" in content.lower()

    @patch("urllib.request.urlopen")
    def test_fetch_xml(self, mock_urlopen, sample_xml):
        """Test XML fetching from URL."""
        # Mock the URL response
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = sample_xml.encode("utf-8")

        parser = ECFRParser()
        result = parser.fetch_xml("http://test.url")

        assert result == sample_xml
        mock_urlopen.assert_called_once_with("http://test.url")
