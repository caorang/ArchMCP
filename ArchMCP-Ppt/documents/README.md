# AWS Architecture PowerPoint MCP Server

Generate PowerPoint presentations with AWS architecture icons using AI or keywords.

## Quick Start

```bash
# Install dependencies
cd dev
pip install -r requirements.txt

# Run server
./run_server.sh

# Test
python3 test_sandbox.py
```

## Features

- 🤖 **AI-Powered**: Describe architecture, get icons automatically
- 🔑 **Keyword Mode**: Direct icon selection via keywords
- 📊 **Auto-Layout**: Icons arranged in grid
- 🎨 **AWS Icons**: Official AWS architecture icons
- ⚡ **Fast**: Generate PPTs in seconds

## Usage

### Description Mode
```json
{
  "input": "web app with load balancer and database",
  "mode": "description"
}
```

### Keyword Mode
```json
{
  "input": "ec2, rds, alb, s3",
  "mode": "keywords"
}
```

## Documentation

- [User Guide](USER_GUIDE.md) - How to use
- [Technical Guide](TECHNICAL_GUIDE.md) - Architecture and API

## Requirements

- Python 3.8+
- AWS credentials with Bedrock access
- EasyArchPPT project (sibling directory)

## Project Structure

```
ArchMCP/
├── src/           # MCP server code
├── dev/           # Development files
├── documents/     # Documentation
├── config/        # Input files
└── outputs/       # Generated PPTs
```

## License

See EasyArchPPT project for icon licensing.
