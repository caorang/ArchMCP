#!/usr/bin/env python3
"""MCP Server for AWS Architecture Draw.io Generation"""
import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import yaml
import logging

# Add ArchMCP-Common to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'ArchMCP-Common'))

from mcp.server import Server
from mcp.types import Tool, TextContent
import boto3

# Import from ArchMCP-Common
from bedrock_analyzer import BedrockAnalyzer

# Import local draw.io generator
from drawio_generator import DrawioGenerator

app = Server("aws-arch-drawio")

# Load configuration
config_path = Path(__file__).parent.parent / 'ArchMCP-Common' / 'config' / 'bedrock_config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Setup debug logging - always enabled
debug_log_path = Path(__file__).parent / 'debug' / 'mcp_server_debug.log'
debug_log_path.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(debug_log_path),
        logging.StreamHandler(sys.stderr)
    ],
    force=True
)
logger = logging.getLogger(__name__)
logger.info("=== MCP Server Started ===")
logger.info(f"Config loaded from: {config_path}")

# Initialize Bedrock client for LLM
class LLMClient:
    def __init__(self, region_name=None, model_id=None, temperature=None, max_tokens=None):
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name or config['bedrock']['region']
        )
        self.model_id = model_id or config['bedrock']['model_id']
        self.temperature = temperature or config['bedrock']['temperature']
        self.max_tokens = max_tokens or config['bedrock']['max_tokens']
    
    def generate_response(self, prompt, max_tokens=None):
        """Generate response from Bedrock"""
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

# Initialize components
llm_client = LLMClient()
drawio_gen = DrawioGenerator(llm_client)
analyzer = BedrockAnalyzer()

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_drawio",
            description="Generate Draw.io diagram with AWS architecture from description or keywords",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Architecture description or comma-separated keywords"},
                    "mode": {"type": "string", "enum": ["description", "keywords"], "default": "description"}
                },
                "required": ["input"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.debug(f"Tool called: {name}")
    logger.debug(f"Arguments: {json.dumps(arguments, indent=2)}")
    
    if name == "generate_drawio":
        input_text = arguments["input"]
        mode = arguments.get("mode", "description")
        
        logger.debug(f"Input text: {input_text}")
        logger.debug(f"Mode: {mode}")
        
        try:
            logger.debug("Calling drawio_gen.generate_drawio()")
            result = drawio_gen.generate_drawio(input_text)
            
            logger.debug(f"Result: {json.dumps(result, indent=2, default=str)}")
            
            if result.get("success"):
                return [TextContent(
                    type="text",
                    text=f"✅ Draw.io diagram created!\n\n📁 File: {result['file_path']}\n📊 Services: {result.get('services_count', 'N/A')}"
                )]
            else:
                logger.error(f"Generation failed: {result.get('error', 'Unknown error')}")
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to generate diagram: {result.get('error', 'Unknown error')}"
                )]
                
        except Exception as e:
            logger.exception("Exception during diagram generation")
            return [TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
