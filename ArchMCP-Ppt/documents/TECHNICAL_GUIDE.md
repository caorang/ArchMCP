# AWS Architecture PPT MCP Server - Technical Guide

## Architecture

### Components

1. **MCP Server** (`src/server.py`)
   - Implements Model Context Protocol
   - Exposes `generate_ppt` tool
   - Handles icon matching and PPT generation

2. **Icon Mapping**
   - Uses keywords_mapping.json from EasyArchPPT
   - Maps keywords to AWS service icons
   - Supports fuzzy matching

3. **Bedrock Integration**
   - Analyzes architecture descriptions
   - Extracts AWS services
   - Uses Claude models

4. **PPT Generation**
   - Uses python-pptx library
   - Adds icons to slides
   - Auto-layouts icons in grid

## Data Flow

```
User Input (description/keywords)
    ↓
MCP Server receives request
    ↓
Mode: Description → Bedrock Analysis → Service List
Mode: Keywords → Direct Keyword Matching
    ↓
Icon Path Resolution
    ↓
PPT Creation with Icons
    ↓
Return PPT file path
```

## Icon Mapping

Icons are stored in `/EasyArchPPT/icons/page*_icons/` directories.

Mapping file: `/EasyArchPPT/input/keywords_mapping.json`

Format:
```json
{
  "Amazon_EC2": {
    "keywords": ["ec2", "instance", "compute", "virtual machine"],
    "category": "Compute"
  }
}
```

## Bedrock Configuration

Config file: `/EasyArchPPT/input/bedrock_config.yaml`

- Model: Claude 3.7 Sonnet
- Region: eu-west-3
- Temperature: 0.1
- Max tokens: 4000

## API

### Tool: generate_ppt

**Input:**
- `input` (string): Architecture description or keywords
- `mode` (string): "description" or "keywords"

**Output:**
- PPT file path
- List of matched icons

**Example:**
```json
{
  "input": "web application with load balancer, ec2 instances, and rds database",
  "mode": "description"
}
```

## File Structure

```
ArchMCP/
├── src/
│   └── server.py          # MCP server
├── dev/
│   ├── requirements.txt   # Dependencies
│   ├── run_server.sh      # Start script
│   └── test_sandbox.py    # Tests
├── documents/
│   ├── TECHNICAL_GUIDE.md # This file
│   └── USER_GUIDE.md      # User documentation
├── config/                # Input files
└── outputs/               # Generated PPTs
```

## Dependencies

- mcp>=0.9.0
- boto3>=1.34.0
- python-pptx>=0.6.23
- pyyaml>=6.0
- pillow>=10.0.0

## Error Handling

- Invalid keywords: Returns empty icon list
- Missing icons: Skips missing icons
- Bedrock errors: Falls back to keyword mode
- File errors: Returns error message

## Performance

- Icon lookup: O(n) where n = number of icons
- PPT generation: ~1-2 seconds for 10 icons
- Bedrock analysis: ~2-5 seconds

## Security

- No credentials in code
- Uses AWS SDK credential chain
- No external network calls except AWS
- File paths validated

## Testing

Run sandbox tests:
```bash
cd dev
python3 test_sandbox.py
```

## Troubleshooting

**Icons not found:**
- Check ICONS_PATH points to EasyArchPPT/icons
- Verify icon files exist

**Bedrock errors:**
- Check AWS credentials
- Verify region and model access
- Check bedrock_config.yaml

**PPT creation fails:**
- Check output directory permissions
- Verify python-pptx installed
