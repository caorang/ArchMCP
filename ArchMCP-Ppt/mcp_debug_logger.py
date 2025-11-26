#!/usr/bin/env python3
"""Debug logger for MCP server requests and Bedrock API calls"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

class MCPDebugLogger:
    def __init__(self, enabled: bool = False, debug_path: str = "debug/mcp_requests"):
        self.enabled = enabled
        self.debug_path = Path(debug_path)
        self.current_session = None
        
        if self.enabled:
            self.debug_path.mkdir(parents=True, exist_ok=True)
            self._start_session()
    
    def _start_session(self):
        """Start a new debug session"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_session = {
            'session_id': timestamp,
            'start_time': datetime.now().isoformat(),
            'requests': []
        }
    
    def log_mcp_request(self, tool_name: str, arguments: Dict[str, Any]):
        """Log incoming MCP tool request"""
        if not self.enabled:
            return
        
        request_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'mcp_request',
            'tool': tool_name,
            'arguments': arguments
        }
        self.current_session['requests'].append(request_log)
        self._write_log()
    
    def log_bedrock_request(self, keyword: str, model_id: str, available_icons_count: int):
        """Log Bedrock API request"""
        if not self.enabled:
            return
        
        bedrock_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'bedrock_request',
            'keyword': keyword,
            'model_id': model_id,
            'available_icons_count': available_icons_count
        }
        self.current_session['requests'].append(bedrock_log)
        self._write_log()
    
    def log_bedrock_response(self, keyword: str, selected_icons: List[str], raw_response: str = None):
        """Log Bedrock API response"""
        if not self.enabled:
            return
        
        response_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'bedrock_response',
            'keyword': keyword,
            'selected_icons': selected_icons,
            'icon_count': len(selected_icons)
        }
        if raw_response:
            response_log['raw_response'] = raw_response
        
        self.current_session['requests'].append(response_log)
        self._write_log()
    
    def log_mcp_response(self, icons: List[Dict[str, str]], error: str = None):
        """Log MCP tool response"""
        if not self.enabled:
            return
        
        response_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'mcp_response',
            'success': error is None,
            'icon_count': len(icons) if icons else 0,
            'icons': [icon['name'] for icon in icons] if icons else []
        }
        if error:
            response_log['error'] = error
        
        self.current_session['requests'].append(response_log)
        self._write_log()
    
    def _write_log(self):
        """Write current session to file"""
        if not self.enabled or not self.current_session:
            return
        
        log_file = self.debug_path / f"mcp_debug_{self.current_session['session_id']}.json"
        with open(log_file, 'w') as f:
            json.dump(self.current_session, f, indent=2)
        
        # Also write markdown version
        self._write_markdown()
    
    def _write_markdown(self):
        """Write human-readable markdown version"""
        if not self.enabled or not self.current_session:
            return
        
        md_file = self.debug_path / f"mcp_debug_{self.current_session['session_id']}.md"
        
        with open(md_file, 'w') as f:
            f.write(f"# MCP Debug Log\n")
            f.write(f"**Session ID:** {self.current_session['session_id']}\n")
            f.write(f"**Start Time:** {self.current_session['start_time']}\n\n")
            f.write("---\n\n")
            
            for idx, entry in enumerate(self.current_session['requests'], 1):
                f.write(f"## Entry {idx}: {entry['type']}\n")
                f.write(f"**Timestamp:** {entry['timestamp']}\n\n")
                
                if entry['type'] == 'mcp_request':
                    f.write(f"**Tool:** {entry['tool']}\n")
                    f.write(f"**Arguments:**\n```json\n{json.dumps(entry['arguments'], indent=2)}\n```\n\n")
                
                elif entry['type'] == 'bedrock_request':
                    f.write(f"**Keyword:** {entry['keyword']}\n")
                    f.write(f"**Model ID:** {entry['model_id']}\n")
                    f.write(f"**Available Icons:** {entry['available_icons_count']}\n\n")
                
                elif entry['type'] == 'bedrock_response':
                    f.write(f"**Keyword:** {entry['keyword']}\n")
                    f.write(f"**Selected Icons ({entry['icon_count']}):**\n")
                    for icon in entry['selected_icons']:
                        f.write(f"- {icon}\n")
                    if 'raw_response' in entry:
                        f.write(f"\n**Raw Response:**\n```\n{entry['raw_response']}\n```\n")
                    f.write("\n")
                
                elif entry['type'] == 'mcp_response':
                    f.write(f"**Success:** {entry['success']}\n")
                    f.write(f"**Icon Count:** {entry['icon_count']}\n")
                    if entry['icons']:
                        f.write(f"**Icons:**\n")
                        for icon in entry['icons']:
                            f.write(f"- {icon}\n")
                    if 'error' in entry:
                        f.write(f"\n**Error:** {entry['error']}\n")
                    f.write("\n")
                
                f.write("---\n\n")

# Global logger instance
_debug_logger = None

def get_debug_logger(config: Dict[str, Any] = None) -> MCPDebugLogger:
    """Get or create debug logger instance"""
    global _debug_logger
    if _debug_logger is None and config:
        debug_config = config.get('debug', {})
        _debug_logger = MCPDebugLogger(
            enabled=debug_config.get('mcp_debug', False),
            debug_path=debug_config.get('mcp_debug_path', 'debug/mcp_requests')
        )
    return _debug_logger
