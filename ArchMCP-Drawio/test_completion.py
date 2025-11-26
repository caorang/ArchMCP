#!/usr/bin/env python3
"""Test script for XML completion functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'ArchMCP-Common'))

from drawio_generator import DrawioGenerator
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Mock LLM client for testing
class MockLLMClient:
    def generate_response(self, prompt, max_tokens=None):
        # Return incomplete XML for testing
        return """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2025-11-25T17:00:00.000Z" agent="Draw.io" version="22.1.11">
  <diagram name="AWS Architecture" id="test-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="vpc-1" value="VPC" style="sketch=0;outlineConnect=0;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;vertexLabel"""

def test_fallback_completion():
    """Test the fallback XML completion"""
    print("\n=== Testing Fallback XML Completion ===\n")
    
    generator = DrawioGenerator(MockLLMClient())
    
    incomplete_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram name="Test">
    <mxGraphModel>
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="test" value="Test" style="shape=rect" vertex="1" parent="1"""
    
    result = generator._fallback_complete_xml(incomplete_xml)
    
    if result["success"]:
        print("✅ Fallback completion successful!")
        print(f"\nCompleted XML:\n{result['xml_content']}")
        
        # Validate
        validation = generator._validate_xml_completeness(result['xml_content'])
        print(f"\nValidation: {validation}")
    else:
        print(f"❌ Fallback completion failed: {result.get('error')}")

if __name__ == "__main__":
    test_fallback_completion()
