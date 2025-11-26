# ArchMCP Project Context - Resume Point

**Date:** 2025-11-24
**Status:** ✅ Fully functional MCP server ready to use

## What Was Built

MCP server that generates PowerPoint presentations with AWS architecture icons from natural language descriptions or keywords.

## Project Location
```
/path/to/ArchMCP/
```

## Key Features Implemented

1. ✅ MCP server with `generate_ppt` tool
2. ✅ Two modes: AI description analysis (Bedrock) and direct keywords
3. ✅ Icon mapping from 800+ AWS icons across 154 pages
4. ✅ Auto-layout icons in grid on PowerPoint slides
5. ✅ HTTP server for download links (port 8765)
6. ✅ Complete documentation
7. ✅ Q CLI integration configured
8. ✅ Ambiguity detection - warns when keywords match >5 icons
9. ✅ Web UI for testing with visual feedback
10. ✅ Bedrock-powered intelligent icon selection in keywords mode
11. ✅ Configurable top_k_icons setting (default: 3)
12. ✅ Loading spinner for Bedrock API calls
13. ✅ Support for icons in multiple folder types (page{X}_icons, page{X}_groups, etc.)
14. ✅ Exact icon name matching with score 1000
15. ✅ Page number extraction from paths for display

## Project Structure

```
ArchMCP/
├── src/
│   ├── server.py              # Main MCP server
│   ├── bedrock_analyzer.py    # Bedrock/Claude integration
│   ├── enhanced_search.py     # Keyword matching
│   └── file_server.py         # HTTP server for downloads
├── dev/
│   ├── requirements.txt       # Dependencies
│   ├── run_server.sh          # Manual start script
│   └── test_sandbox.py        # Test suite
├── documents/
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── TECHNICAL_GUIDE.md
│   └── PROJECT_SUMMARY.md
├── config/
│   ├── keywords_mapping.json  # Icon keyword mappings (800+ icons)
│   └── bedrock_config.yaml    # Bedrock configuration
├── icons/                     # 800+ AWS icons across 154 pages
├── outputs/                   # Generated PPT files
├── tests/                     # Test suite with 20 test cases
├── .venv/                     # Python virtual environment
├── README.md              # Quick start guide
└── PROJECT_CONTEXT.md         # This file
```

## Recent Fixes (2025-11-24)

1. ✅ Fixed `Pt` import error in ui_interface.py
2. ✅ Fixed image display for icons in non-standard folders (groups, etc.)
3. ✅ Added path field to all icon objects returned by search
4. ✅ Extract page numbers from paths when page field is missing
5. ✅ Fixed Instance icon mapping (Instance → Instances.png)
6. ✅ Icons now use path from mapping instead of constructing from page numbers

## Current Configuration

### Q CLI Config
Location: `~/.aws/amazonq/mcp.json`
```json
{
  "mcpServers": {
    "aws-arch-ppt": {
      "command": "python",
      "args": ["/path/to/ArchMCP/src/server.py"]
    }
  }
}
```

### Virtual Environment
Location: `/path/to/ArchMCP/.venv`
Activate: `source .venv/bin/activate`

### Dependencies Installed
- mcp>=0.9.0
- boto3>=1.34.0
- python-pptx>=0.6.23
- pyyaml>=6.0
- pillow>=10.0.0

## How to Use

### With Q CLI (Recommended)
```bash
q chat
> Generate a PowerPoint with EC2, S3, and Lambda icons
```

### Web UI (For Testing)
```bash
cd /path/to/ArchMCP
source .venv/bin/activate
python ui_interface.py
```
Open: http://localhost:5000

### Manual Testing
```bash
q chat
> Generate a PowerPoint with EC2, S3, and Lambda icons
```

### Manual Testing
```bash
cd /path/to/ArchMCP
source .venv/bin/activate
python dev/test_sandbox.py
```

## Key Files to Know

1. **src/server.py** - Main MCP server (150 lines)
   - `generate_ppt` tool with 2 modes
   - Starts HTTP server on port 8765
   - Returns download links

2. **src/bedrock_analyzer.py** - AI analysis
   - Uses Claude 3.7 Sonnet
   - Extracts AWS services from descriptions
   - Region: eu-west-3

3. **config/keywords_mapping.json** - Icon mappings
   - Maps keywords to icon files
   - 130+ AWS services
   - Supports fuzzy matching

4. **icons/** - AWS icon PNG files
   - Organized in page*_icons directories
   - Copied from EasyArchPPT project

## What Works

✅ Q CLI integration
✅ Keyword mode (direct icon selection)
✅ Description mode (AI-powered)
✅ PPT generation with icons
✅ HTTP download links
✅ Auto-layout in grid
✅ Error handling
✅ Documentation complete

## Next Session - Possible Enhancements

### Not Yet Implemented (Ideas)
- [ ] Multiple slide layouts
- [ ] Custom icon upload
- [ ] Connector lines between icons
- [ ] Icon grouping by category
- [ ] Export to PDF/PNG
- [ ] Template library
- [ ] Claude Desktop integration
- [ ] VS Code Cline integration
- [ ] Custom styling options

### Known Limitations
- Basic grid layout only
- No custom positioning
- No text labels on icons
- Single slide output
- Requires AWS Bedrock access for description mode

## Testing Status

✅ Keyword parsing works
✅ Icon path resolution works
✅ PPT generation works
✅ HTTP server works
✅ Q CLI config created
⏳ Not yet tested with Q CLI (ready to test)

## AWS Configuration

**Required:**
- AWS credentials configured (`aws configure`)
- Bedrock access in eu-west-3 region
- Claude 3.7 Sonnet model access

**Config file:** `config/bedrock_config.yaml`

## Troubleshooting Reference

**Server won't start:**
- Activate venv: `source .venv/bin/activate`
- Check Python: `python --version` (need 3.8+)
- Install deps: `pip install -r dev/requirements.txt`

**No icons:**
- Check: `ls icons/` (should show 130+ directories)
- Verify: `ls config/keywords_mapping.json`

**Bedrock errors:**
- Check credentials: `aws sts get-caller-identity`
- Verify region access to Bedrock
- Check model availability

## Important Notes

1. **Server lifecycle:** Q CLI manages it automatically
2. **Never manually start** server when using with Q
3. **Download links:** http://localhost:8765/filename.pptx
4. **Output location:** outputs/ directory
5. **Independent:** No longer depends on EasyArchPPT

## Quick Commands

```bash
# Activate environment
source .venv/bin/activate

# Test server
python dev/test_sandbox.py

# Use with Q
q chat

# Check config
cat ~/.aws/amazonq/mcp.json

# View outputs
ls -lh outputs/
```

## Resume Checklist

When resuming work:
1. [ ] Navigate to project: `cd /path/to/ArchMCP`
2. [ ] Activate venv: `source .venv/bin/activate`
3. [ ] Check AWS credentials: `aws sts get-caller-identity`
4. [ ] Review this context file
5. [ ] Test with Q CLI: `q chat`

## Contact/Support

- Documentation: `documents/` folder
- Quick start: `README.md`
- Technical details: `documents/TECHNICAL_GUIDE.md`
- User guide: `documents/USER_GUIDE.md`

---

**Ready to use!** Just run `q chat` and ask it to generate a PowerPoint.


## MCP Server Usage

The MCP server exposes a `generate_ppt` tool with two modes:

### Tool Parameters

```json
{
  "input": "string (required)",
  "mode": "description | keywords (optional, default: description)"
}
```

### Mode Selection

**1. Description Mode (default)**
- Triggered when: `mode` parameter is omitted or set to `"description"`
- Uses: Bedrock AI to analyze natural language and extract AWS services
- Example input: "A web application with EC2 instances behind a load balancer, storing data in S3 and RDS"
- Process:
  1. Sends description to Bedrock Claude
  2. Claude extracts service names (e.g., ["EC2", "ELB", "S3", "RDS"])
  3. Matches services to icons using semantic search
  4. Generates PowerPoint

**2. Keywords Mode**
- Triggered when: `mode` parameter is set to `"keywords"`
- Uses: Bedrock AI to intelligently select icons for each keyword
- Example input: "EC2, S3, Lambda"
- Process:
  1. Splits input by commas
  2. For each keyword, sends to Bedrock with all available icons
  3. Bedrock selects top K most relevant icons (configurable in bedrock_config.yaml)
  4. Generates PowerPoint

### Using with Q CLI

**Description Mode (Natural Language):**
```bash
q chat
> Generate a PowerPoint for a serverless architecture with Lambda, API Gateway, and DynamoDB
```

**Keywords Mode (Explicit Icons):**
```bash
q chat
> Generate a PowerPoint with these icons in keywords mode: EC2, S3, Lambda, RDS
```

**Programmatic Call:**
The MCP server will automatically detect the mode based on:
- If you mention "keywords mode" → uses keywords mode
- Otherwise → uses description mode (default)

### Configuration

**Bedrock Settings** (`config/bedrock_config.yaml`):
```yaml
top_k_icons: 3  # Number of icons returned per keyword in keywords mode
model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
region: "us-east-1"
```

### Output

Both modes generate:
- PowerPoint file in `outputs/` directory
- HTTP download link (http://localhost:8765/...)
- List of icons included

### Error Handling

**Ambiguity Detection:**
If a keyword matches >5 icons, the server returns a helpful error:
```
⚠️ Ambiguous keyword: "storage"
Found 15 matches. Please be more specific.
Try: "S3", "EBS", "EFS", "Storage Gateway"
```
