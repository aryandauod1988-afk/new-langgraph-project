"""ECFR XML Parser.

This module parses ECFR XML documents and extracts sections into JSON and TXT files.
Each section is identified by HEAD tags containing section numbers (e.g., § 4.13).
"""

import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from urllib.error import URLError


class ECFRParser:
    """Parser for ECFR XML documents."""

    def __init__(self, output_dir: str = "ecfr_sections"):
        """Initialize the parser.

        Args:
            output_dir: Directory to save the extracted files
        """
        self.output_dir = output_dir
        self.section_pattern = re.compile(r"§\s*(\d+\.\d+)")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def fetch_xml(self, url: str) -> str:
        """Fetch XML content from URL.

        Args:
            url: URL to fetch XML from

        Returns:
            XML content as string

        Raises:
            URLError: If URL cannot be fetched
        """
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode("utf-8")
        except URLError as e:
            raise URLError(f"Failed to fetch XML from {url}: {e}")

    def parse_xml(self, xml_content: str) -> ET.Element:
        """Parse XML content.

        Args:
            xml_content: XML content as string

        Returns:
            Root element of parsed XML
        """
        return ET.fromstring(xml_content)

    def find_sections(self, root: ET.Element) -> List[Tuple[str, ET.Element]]:
        """Find all sections with HEAD tags containing section numbers.

        Args:
            root: Root element of XML document

        Returns:
            List of tuples containing (section_name, section_element)
        """
        sections = []

        # Create a mapping of all elements to their parents
        parent_map = {c: p for p in root.iter() for c in p}

        # Find all HEAD elements
        for head in root.iter("HEAD"):
            if head.text:
                # Check if the HEAD contains a section number pattern
                match = self.section_pattern.search(head.text)
                if match:
                    section_num = match.group(1)
                    section_name = f"section_{section_num.replace('.', '_')}"

                    # Find the parent element that contains this section
                    section_element = parent_map.get(head)
                    if section_element is not None:
                        sections.append((section_name, section_element))

        return sections

    def extract_text_content(self, element: ET.Element) -> str:
        """Extract text content from an element.

        Args:
            element: XML element

        Returns:
            Text content, or "table" if element contains tables
        """
        # Check if element contains table elements
        if element.find(".//table") is not None or element.find(".//TABLE") is not None:
            return "table"

        # Extract all text content
        text_parts = []
        for text in element.itertext():
            text_parts.append(text.strip())

        return " ".join(text_parts).strip()

    def get_section_metadata(
        self, section_name: str, section_element: ET.Element, url: str
    ) -> Dict:
        """Generate metadata for a section.

        Args:
            section_name: Name of the section
            section_element: XML element containing the section
            url: Original URL of the document

        Returns:
            Dictionary containing metadata
        """
        # Find the HEAD element within this section
        head_element = section_element.find(".//HEAD")
        section_citation = head_element.text if head_element is not None else ""

        # Generate permalink (simplified version)
        permalink = f"{url}#{section_name}"

        # Get raw XML
        raw_xml = ET.tostring(section_element, encoding="unicode")

        return {
            "section_name": section_name,
            "section_citation": section_citation,
            "permalink": permalink,
            "raw_xml": raw_xml,
        }

    def save_section_files(
        self, section_name: str, metadata: Dict, text_content: str
    ) -> None:
        """Save JSON and TXT files for a section.

        Args:
            section_name: Name of the section
            metadata: Metadata dictionary
            text_content: Text content of the section
        """
        # Save JSON file
        json_path = os.path.join(self.output_dir, f"{section_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Save TXT file
        txt_path = os.path.join(self.output_dir, f"{section_name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)

    def process_url(self, url: str) -> int:
        """Process ECFR XML from URL and extract sections.

        Args:
            url: URL to the ECFR XML document

        Returns:
            Number of sections processed
        """
        print(f"Fetching XML from: {url}")
        xml_content = self.fetch_xml(url)

        print("Parsing XML content...")
        root = self.parse_xml(xml_content)

        print("Finding sections...")
        sections = self.find_sections(root)

        print(f"Found {len(sections)} sections")

        for section_name, section_element in sections:
            print(f"Processing {section_name}...")

            # Get metadata
            metadata = self.get_section_metadata(section_name, section_element, url)

            # Extract text content
            text_content = self.extract_text_content(section_element)

            # Save files
            self.save_section_files(section_name, metadata, text_content)

        print(f"Completed processing {len(sections)} sections")
        return len(sections)

    def process_xml_content(self, xml_content: str, url: str = "unknown") -> int:
        """Process ECFR XML content directly and extract sections.

        Args:
            xml_content: XML content as string
            url: Source URL (for metadata)

        Returns:
            Number of sections processed
        """
        print("Parsing XML content...")
        root = self.parse_xml(xml_content)

        print("Finding sections...")
        sections = self.find_sections(root)

        print(f"Found {len(sections)} sections")

        for section_name, section_element in sections:
            print(f"Processing {section_name}...")

            # Get metadata
            metadata = self.get_section_metadata(section_name, section_element, url)

            # Extract text content
            text_content = self.extract_text_content(section_element)

            # Save files
            self.save_section_files(section_name, metadata, text_content)

        print(f"Completed processing {len(sections)} sections")
        return len(sections)


def main():
    """Main function to demonstrate usage."""
    parser = ECFRParser()
    url = "https://www.govinfo.gov/bulkdata/ECFR/title-38/ECFR-title38.xml"

    try:
        sections_count = parser.process_url(url)
        print(f"Successfully processed {sections_count} sections")
    except Exception as e:
        print(f"Error processing URL: {e}")


if __name__ == "__main__":
    main()
