#!/usr/bin/env python3
"""Sandbox test for MCP server"""
import asyncio
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / "src"))
from server import parse_keywords, create_presentation

async def test_keywords():
    """Test keyword parsing"""
    print("Testing keyword parsing...")
    keywords = "ec2, s3, lambda, vpc"
    icons = parse_keywords(keywords)
    print(f"Input: {keywords}")
    print(f"Matched icons: {icons}")
    
async def test_ppt_creation():
    """Test PPT creation"""
    print("\nTesting PPT creation...")
    icons = ["Amazon_EC2", "Amazon_S3", "AWS_Lambda"]
    ppt_path = create_presentation(icons)
    print(f"Created: {ppt_path}")

async def main():
    await test_keywords()
    await test_ppt_creation()
    print("\n✅ Tests complete")

if __name__ == "__main__":
    asyncio.run(main())
