# ArchMCP-Drawio - AWS Architecture Draw.io Generator

MCP server that generates Draw.io diagrams with AWS architecture from natural language descriptions.

## Features

- Generate Draw.io XML diagrams from architecture descriptions
- Uses AWS Bedrock (Claude) for intelligent service extraction
- Comprehensive AWS service library with proper Draw.io shapes
- Two modes: keywords and description

## Setup

```bash
cd /path/to/ArchMCP

# Activate shared virtual environment
source .venv/bin/activate

# Install dependencies
cd ArchMCP-Drawio
pip install -r requirements.txt
```

## Configuration

The server uses the same Bedrock configuration as ArchMCP-Ppt.

## Usage with Kiro CLI

Add to `~/.aws/amazonq/mcp.json`:

```json
{
  "mcpServers": {
    "aws-arch-drawio": {
      "command": "python",
      "args": ["/path/to/ArchMCP/ArchMCP-Drawio/server.py"]
    }
  }
}
```

Then:
```bash
q chat
> Generate a Draw.io diagram for a serverless API with Lambda, API Gateway, and DynamoDB
```

## Modes

### Description Mode (default)
Provide a natural language description of your architecture:
```
"A web application with EC2 instances behind a load balancer, storing data in S3 and RDS"
```

### Keywords Mode
Provide comma-separated AWS service keywords:
```
"EC2, ELB, S3, RDS"
```

## Output

Diagrams are saved to `outputs/` directory as `.drawio` XML files that can be opened in:
- draw.io web app (https://app.diagrams.net)
- draw.io desktop application
- VS Code with draw.io extension

## Files

- `server.py` - MCP server implementation
- `drawio_generator.py` - Draw.io XML generation logic
- `prompt_manager.py` - Prompt template management
- `config/aws_classes_comprehensive.json` - AWS service to Draw.io shape mapping
- `prompts/` - LLM prompts for diagram generation
