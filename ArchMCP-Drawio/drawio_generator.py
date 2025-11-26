"""
Draw.io diagram generator using AWS icons and XML format
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from prompt_manager import PromptManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DrawioGenerator:
    """Generates Draw.io XML diagrams for AWS architectures"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.prompt_manager = PromptManager()
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_drawio(self, description: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Generate Draw.io XML diagram from architecture description with completeness validation
        
        Args:
            description: Architecture description text
            max_retries: Maximum number of retry attempts for incomplete XML
            
        Returns:
            Dict with success status, XML content, and file path
        """
        logger.info(f"Starting Draw.io generation. Max retries: {max_retries}")
        
        for attempt in range(max_retries + 1):
            logger.info(f"=== Attempt {attempt + 1}/{max_retries + 1} ===")
            
            try:
                # Load Draw.io prompt template
                prompt_template = self.prompt_manager.load_prompt("drawio_prompt")
                
                # Load system examples
                system_example1 = self._load_system_example("system-example1")
                system_example2 = self._load_system_example("system-example2")
                
                # Prepare prompt variables
                current_time = datetime.now(timezone.utc).isoformat(timespec='milliseconds') + 'Z'
                
                prompt_variables = {
                    "system_example1": system_example1,
                    "system_example2": system_example2,
                    "datetime.now(timezone.utc).isoformat(timespec='milliseconds') + 'Z'": current_time,
                    "diagram_description": description
                }
                
                # Add retry context if this is a retry attempt
                if attempt > 0:
                    prompt_variables["retry_instruction"] = f"\n\nIMPORTANT: This is retry attempt {attempt}. The previous response was incomplete. Please ensure you generate a COMPLETE XML file that ends with </mxfile>. Use shorter element names and fewer attributes if needed to stay within limits."
                    prompt_template += "\n{retry_instruction}"
                
                # Render the prompt
                final_prompt = self.prompt_manager.render_template(prompt_template, prompt_variables)
                logger.info(f"Prompt length: {len(final_prompt)} chars")
                
                # Generate XML with LLM
                logger.info("Calling LLM for XML generation...")
                response = self.llm_client.generate_response(final_prompt, max_tokens=8000)
                
                # Handle string response (BedrockClient returns string directly)
                if isinstance(response, str):
                    xml_content = response.strip()
                else:
                    # Handle dict response (for compatibility)
                    if not response.get("success"):
                        return {
                            "success": False,
                            "error": f"LLM generation failed: {response.get('error', 'Unknown error')}"
                        }
                    xml_content = response.get("content", "").strip()
                
                logger.info(f"Received XML response. Length: {len(xml_content)} chars")
                
                # Extract XML from response (handle markdown and explanatory text)
                xml_content = self._extract_xml(xml_content)
                
                # Validate XML format and completeness
                validation_result = self._validate_xml_completeness(xml_content)
                logger.info(f"Validation result: {validation_result}")
                
                if validation_result["is_complete"]:
                    # Save XML file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"aws_architecture_{timestamp}.drawio"
                    file_path = self.output_dir / filename
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(xml_content)
                    
                    logger.info(f"✅ Successfully generated complete XML on attempt {attempt + 1}")
                    
                    return {
                        "success": True,
                        "xml_content": xml_content,
                        "file_path": str(file_path),
                        "filename": filename,
                        "attempts": attempt + 1
                    }
                else:
                    logger.warning(f"XML incomplete: {validation_result['error']}")
                    logger.info("Attempting XML completion...")
                    
                    # Try to complete the incomplete XML
                    completion_result = self._complete_xml(xml_content)
                    
                    if completion_result["success"]:
                        completed_xml = completion_result["xml_content"]
                        
                        # Validate the completed XML
                        final_validation = self._validate_xml_completeness(completed_xml)
                        logger.info(f"Completed XML validation: {final_validation}")
                        
                        if final_validation["is_complete"]:
                            # Save completed XML file
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"aws_architecture_{timestamp}.drawio"
                            file_path = self.output_dir / filename
                            
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(completed_xml)
                            
                            logger.info(f"✅ Successfully completed and saved XML on attempt {attempt + 1}")
                            
                            return {
                                "success": True,
                                "xml_content": completed_xml,
                                "file_path": str(file_path),
                                "filename": filename,
                                "attempts": attempt + 1,
                                "completed": True
                            }
                        else:
                            logger.warning(f"Completed XML still invalid: {final_validation['error']}")
                    else:
                        logger.warning(f"XML completion failed: {completion_result.get('error', 'Unknown error')}")
                    
                    # If this is the last attempt, return the incomplete result with error
                    if attempt == max_retries:
                        logger.error(f"❌ Failed after {max_retries + 1} attempts")
                        return {
                            "success": False,
                            "error": f"XML incomplete after {max_retries + 1} attempts: {validation_result['error']}",
                            "xml_content": xml_content,
                            "attempts": attempt + 1
                        }
                    # Continue to next attempt
                    logger.info("Retrying with new generation...")
                    continue
                    
            except Exception as e:
                logger.error(f"Exception on attempt {attempt + 1}: {str(e)}", exc_info=True)
                if attempt == max_retries:
                    return {
                        "success": False,
                        "error": f"Draw.io generation error: {str(e)}",
                        "attempts": attempt + 1
                    }
                continue
        
        return {
            "success": False,
            "error": "Failed to generate complete XML after all attempts"
        }

    def _complete_xml(self, incomplete_xml: str, max_continuations: int = 3) -> Dict[str, Any]:
        """
        Complete incomplete XML by asking LLM to continue from where it left off
        
        Args:
            incomplete_xml: Incomplete XML content
            max_continuations: Maximum number of continuation attempts
            
        Returns:
            Dict with success status and completed XML
        """
        try:
            logger.info(f"Attempting to complete XML. Length: {len(incomplete_xml)}")
            
            current_xml = incomplete_xml
            
            for continuation in range(max_continuations):
                logger.info(f"Continuation attempt {continuation + 1}/{max_continuations}")
                
                # Check if already complete
                validation = self._validate_xml_completeness(current_xml)
                if validation["is_complete"]:
                    logger.info(f"✅ XML completed after {continuation} continuations")
                    return {"success": True, "xml_content": current_xml}
                
                # Ask LLM to continue from where it left off
                continuation_prompt = f"""Continue the incomplete Draw.io XML from where it was cut off.

INCOMPLETE XML (showing last 1500 characters):
...{current_xml[-1500:]}

INSTRUCTIONS:
1. Provide ONLY the continuation - do NOT repeat any existing XML
2. Start exactly where the XML was cut off
3. Complete any incomplete tags or attributes
4. Add all necessary closing tags to end with </mxfile>
5. No explanations, no markdown, just the continuation XML

Continue from here:"""

                response = self.llm_client.generate_response(continuation_prompt, max_tokens=4000)
                
                if isinstance(response, str):
                    continuation_xml = response.strip()
                else:
                    if not response.get("success"):
                        logger.warning("Continuation failed, trying fallback")
                        return self._fallback_complete_xml(current_xml)
                    continuation_xml = response.get("content", "").strip()
                
                # Clean continuation
                if continuation_xml.startswith("```xml"):
                    continuation_xml = continuation_xml[6:]
                if continuation_xml.startswith("```"):
                    continuation_xml = continuation_xml[3:]
                if continuation_xml.endswith("```"):
                    continuation_xml = continuation_xml[:-3]
                continuation_xml = continuation_xml.strip()
                
                logger.info(f"Received continuation of {len(continuation_xml)} chars")
                
                # Append continuation to current XML
                current_xml = current_xml + continuation_xml
                
            # After all continuations, check if complete
            validation = self._validate_xml_completeness(current_xml)
            if validation["is_complete"]:
                logger.info(f"✅ XML completed after {max_continuations} continuations")
                return {"success": True, "xml_content": current_xml}
            
            # If still incomplete, try fallback
            logger.warning("Still incomplete after continuations, trying fallback")
            return self._fallback_complete_xml(current_xml)
            
        except Exception as e:
            logger.error(f"Continuation error: {e}, trying fallback")
            return self._fallback_complete_xml(incomplete_xml)

    def _fallback_complete_xml(self, incomplete_xml: str) -> Dict[str, Any]:
        """
        Simple fallback XML completion by adding missing closing tags
        """
        try:
            xml_content = incomplete_xml.strip()
            logger.info("Using fallback XML completion")
            
            # Check for incomplete mxCell first
            lines = xml_content.split('\n')
            last_line = lines[-1].strip() if lines else ""
            
            # If last line is incomplete, try to complete it
            if last_line and not last_line.endswith('>') and not last_line.endswith('/>'):
                logger.info(f"Incomplete last line detected: {last_line[:100]}")
                
                if 'mxCell' in last_line:
                    # Complete the mxCell tag
                    if not last_line.endswith('"'):
                        last_line += '"'
                    
                    # Add missing attributes if needed
                    if 'vertex="1"' not in last_line and 'edge="1"' not in last_line:
                        last_line += ' vertex="1"'
                    if 'parent=' not in last_line:
                        last_line += ' parent="1"'
                    
                    last_line += '>'
                    
                    # Add geometry if this is a vertex and geometry is missing
                    if 'vertex="1"' in last_line:
                        last_line += '\n          <mxGeometry x="100" y="100" width="80" height="60" as="geometry" />'
                    
                    last_line += '\n        </mxCell>'
                    lines[-1] = last_line
                    xml_content = '\n'.join(lines)
                    logger.info("Completed incomplete mxCell")
            
            # Check for common unclosed tags in reverse order (innermost to outermost)
            required_closings = []
            
            # Check each tag pair
            if "<root>" in xml_content and "</root>" not in xml_content:
                required_closings.append("      </root>")
                logger.info("Adding missing </root>")
                
            if "<mxGraphModel" in xml_content and "</mxGraphModel>" not in xml_content:
                required_closings.append("    </mxGraphModel>")
                logger.info("Adding missing </mxGraphModel>")
                
            if "<diagram" in xml_content and "</diagram>" not in xml_content:
                required_closings.append("  </diagram>")
                logger.info("Adding missing </diagram>")
            
            if "<mxfile" in xml_content and "</mxfile>" not in xml_content:
                required_closings.append("</mxfile>")
                logger.info("Adding missing </mxfile>")
            
            # Add all required closing tags
            for closing_tag in required_closings:
                xml_content += f"\n{closing_tag}"
            
            logger.info(f"Fallback completion done. Final length: {len(xml_content)}")
            
            return {
                "success": True,
                "xml_content": xml_content
            }
            
        except Exception as e:
            logger.error(f"Fallback completion error: {str(e)}")
            return {
                "success": False,
                "error": f"Fallback completion error: {str(e)}"
            }
    
    def _extract_xml(self, response: str) -> str:
        """Extract XML content from LLM response, handling markdown and explanatory text"""
        content = response.strip()
        
        # Remove markdown code blocks
        if "```xml" in content:
            start = content.find("```xml") + 6
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
        
        # Find XML start
        xml_start = -1
        if "<?xml" in content:
            xml_start = content.find("<?xml")
        elif "<mxfile" in content:
            xml_start = content.find("<mxfile")
        
        if xml_start > 0:
            content = content[xml_start:]
        
        # Find XML end
        if "</mxfile>" in content:
            xml_end = content.rfind("</mxfile>") + 9
            content = content[:xml_end]
        
        return content.strip()
    
    def _validate_xml_completeness(self, xml_content: str) -> Dict[str, Any]:
        """
        Validate if XML content is complete and well-formed
        
        Args:
            xml_content: XML content to validate
            
        Returns:
            Dict with is_complete boolean and error message if incomplete
        """
        if not xml_content:
            return {"is_complete": False, "error": "Empty XML content"}
        
        # Check basic XML structure
        if not xml_content.startswith("<?xml") and not xml_content.startswith("<mxfile"):
            return {"is_complete": False, "error": "Invalid XML start"}
        
        # Check if XML ends properly
        if not xml_content.rstrip().endswith("</mxfile>"):
            return {"is_complete": False, "error": "XML does not end with </mxfile>"}
        
        # Check for basic required elements
        required_elements = ["<mxfile", "<diagram", "<mxGraphModel", "</mxGraphModel>", "</diagram>", "</mxfile>"]
        for element in required_elements:
            if element not in xml_content:
                return {"is_complete": False, "error": f"Missing required element: {element}"}
        
        # Check for truncated content (common signs of incomplete generation)
        truncation_indicators = [
            'fillColor=#ED',  # Incomplete color code
            'strokeColor=#',  # Incomplete stroke color
            'style="',        # Incomplete style attribute
            'value="',        # Incomplete value attribute
            '<mxCell id="',   # Incomplete cell definition
        ]
        
        lines = xml_content.split('\n')
        last_line = lines[-1] if lines else ""
        second_last_line = lines[-2] if len(lines) > 1 else ""
        
        for indicator in truncation_indicators:
            if last_line.strip().endswith(indicator) or second_last_line.strip().endswith(indicator):
                return {"is_complete": False, "error": f"XML appears truncated at: {indicator}"}
        
        # Basic XML balance check for critical tags
        critical_tags = ["mxfile", "diagram", "mxGraphModel", "root"]
        for tag in critical_tags:
            open_count = xml_content.count(f"<{tag}")
            close_count = xml_content.count(f"</{tag}>")
            if open_count != close_count:
                return {"is_complete": False, "error": f"Unbalanced {tag} tags: {open_count} open, {close_count} close"}
        
        return {"is_complete": True, "error": None}
    
    def _load_system_example(self, example_name: str) -> str:
        """Load system example from file"""
        try:
            example_file = Path("prompts") / f"{example_name}.txt"
            if example_file.exists():
                with open(example_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            else:
                return f"<example>{example_name} not found</example>"
        except Exception:
            return f"<example>Error loading {example_name}</example>"
    
    def fix_drawio_xml(self, xml_content: str, error_message: str) -> Dict[str, Any]:
        """
        Fix Draw.io XML errors
        
        Args:
            xml_content: Original XML content with errors
            error_message: Error message to fix
            
        Returns:
            Dict with success status and fixed XML content
        """
        try:
            # Load fix prompt (create a simple one for now)
            fix_prompt = f"""
You are a Draw.io XML expert. Fix the following XML content that has errors.

Original XML:
{xml_content}

Error Message:
{error_message}

Rules for fixing:
- Ensure valid XML structure
- Use only mxgraph.aws4 shapes
- Fix any syntax errors
- Maintain the original architecture intent
- Include proper mxfile header and structure

Provide ONLY the corrected XML content, no explanations.
"""
            
            response = self.llm_client.generate_response(fix_prompt)
            
            # Handle string response (BedrockClient returns string directly)
            if isinstance(response, str):
                fixed_xml = response.strip()
            else:
                # Handle dict response (for compatibility)
                if not response.get("success"):
                    return {
                        "success": False,
                        "error": f"Fix generation failed: {response.get('error', 'Unknown error')}"
                    }
                fixed_xml = response.get("content", "").strip()
            
            # Clean XML content
            if fixed_xml.startswith("```xml"):
                fixed_xml = fixed_xml[6:]
            if fixed_xml.startswith("```"):
                fixed_xml = fixed_xml[3:]
            if fixed_xml.endswith("```"):
                fixed_xml = fixed_xml[:-3]
            
            fixed_xml = fixed_xml.strip()
            
            return {
                "success": True,
                "xml_content": fixed_xml
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"XML fix error: {str(e)}"
            }
