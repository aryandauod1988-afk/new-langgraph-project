#!/usr/bin/env python3
"""Script to extract ECFR sections from XML."""

import argparse
import sys
from pathlib import Path

# Add src to path so we can import our module
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.ecfr_parser import ECFRParser


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Extract ECFR sections from XML")
    parser.add_argument(
        "--url",
        default="https://www.govinfo.gov/bulkdata/ECFR/title-38/ECFR-title38.xml",
        help="URL to the ECFR XML file",
    )
    parser.add_argument(
        "--output-dir",
        default="ecfr_sections",
        help="Output directory for extracted sections",
    )
    parser.add_argument("--xml-file", help="Local XML file to parse instead of URL")

    args = parser.parse_args()

    ecfr_parser = ECFRParser(args.output_dir)

    try:
        if args.xml_file:
            print(f"Reading XML from local file: {args.xml_file}")
            with open(args.xml_file, "r", encoding="utf-8") as f:
                xml_content = f.read()
            sections_count = ecfr_parser.process_xml_content(xml_content, args.xml_file)
        else:
            print(f"Fetching XML from URL: {args.url}")
            sections_count = ecfr_parser.process_url(args.url)

        print(f"\n✅ Successfully processed {sections_count} sections")
        print(f"📁 Files saved to: {args.output_dir}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
