# ArchMCP - AWS Architecture Diagram Generators

MCP servers for generating AWS architecture diagrams from natural language descriptions.



### PowerPoint Generator

```bash
kiro-cli chat
> Generate a PowerPoint with the icons for EC2, S3, and Lambda

> Generate a PowerPoint with the icons for a web application with:
> - Application Load Balancer
> - EC2 Auto Scaling
> - RDS database
> - ElastiCache
```

![PowerPoint Generator Demo](Arch-Ppt-demo1.gif)

### Draw.io Generator

```bash
kiro-cli chat
> Create a draw.io diagram with VPC, subnets, and NAT gateway

> Generate a draw.io architecture for a serverless application using:
> - API Gateway
> - Lambda functions
> - DynamoDB
> - S3 bucket
```

![PowerPoint Generator Demo](Arch-Drawio-demo1.gif)

## Project Structure

```
ArchMCP/
├── .venv/                  # Shared Python virtual environment
├── ArchMCP-Common/         # Shared code (Bedrock analyzer, search logic)
├── ArchMCP-Ppt/           # PowerPoint generator MCP server
└── ArchMCP-Drawio/        # Draw.io generator MCP server (coming soon)
```

## Quick Start

### 1. Setup (One-time)

```bash
cd /path/to/ArchMCP

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies for PowerPoint
cd ArchMCP-Ppt
pip install -r requirements.txt
```

### 2. Configure AWS

```bash
aws configure
# Enter your AWS Access Key, Secret Key, and region
```

### 3. Configure Bedrock (Optional)

Edit `ArchMCP-Ppt/config/bedrock_config.yaml` or `ArchMCP-Drawio/config/bedrock_config.yaml`:

```yaml
bedrock:
  # Model to use for architecture analysis
  model_id: "us.anthropic.claude-sonnet-4-20250514-v1:0"
  
  # AWS region for Bedrock
  region: "us-east-1"
  
  # Icon selection mode
  # "llm" - Use Bedrock for icon selection (more accurate, slower, more costly)
  # "local" - Use local semantic search (faster, cheaper)
  icon_selection_mode: "llm"
  
  # Number of top matching icons to return per service (default: 3)
  top_k_icons: 3
  
  # Generation parameters
  temperature: 0.1
  max_tokens: 4000
```

Key parameters:
- `top_k_icons`: Controls how many icon matches to return per service (1-10 recommended)
- `icon_selection_mode`: Choose between LLM-based or local search for icon matching
- `model_id`: Claude model to use for architecture analysis
- `region`: AWS region where Bedrock is available

### 4. Use PowerPoint Generator

See [ArchMCP-Ppt/README.md](ArchMCP-Ppt/README.md) for detailed instructions.

**Quick test:**
```bash
cd ArchMCP-Ppt
python ui_interface.py
# Open http://localhost:5000
```

### 5. Use with Kiro CLI

Add to `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "aws-arch-ppt": {
      "command": "/path/to/ArchMCP/.venv/bin/python",
      "args": ["/path/to/ArchMCP/ArchMCP-Ppt/server.py"]
    },
    "aws-arch-drawio": {
      "command": "/path/to/ArchMCP/.venv/bin/python",
      "args": ["/path/to/ArchMCP/ArchMCP-Drawio/server.py"]
    }
  }
}
```


## Components

### ArchMCP-Common
Shared libraries used by both servers:
- `bedrock_analyzer.py` - AWS Bedrock integration for AI-powered service extraction
- `enhanced_search.py` - Semantic search and icon matching

### ArchMCP-Ppt
PowerPoint presentation generator:
- 800+ AWS architecture icons
- Keywords and description modes
- Web UI for testing
- MCP server for Kiro CLI integration


### ArchMCP-Drawio
Draw.io diagram generator:
- AWS service to Draw.io shape mapping
- Same input modes as PPT
- XML output format for draw.io
- MCP server for Kiro CLI integration

## Development

All projects share the same virtual environment for convenience:

```bash
# Activate once
source .venv/bin/activate

# Work on PowerPoint
cd ArchMCP-Ppt
python ui_interface.py

# Work on Draw.io (when ready)
cd ../ArchMCP-Drawio
python ui_interface.py
```

## License

See individual project folders for licensing information.
