#!/usr/bin/env python3
"""
Bedrock LLM Integration for AWS Icons Analysis
Enhanced with keyword-based matching
"""

import boto3
import base64
import json
import yaml
from pathlib import Path
from datetime import datetime
import os
from PIL import Image
import io
import re

# Import enhanced search if available
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from enhanced_search import EnhancedSearch
    ENHANCED_SEARCH_AVAILABLE = True
except ImportError:
    ENHANCED_SEARCH_AVAILABLE = False
    print("Enhanced search not available, using fallback matching")

class BedrockAnalyzer:
    def __init__(self, region_name="us-east-1", model_id="anthropic.claude-3-sonnet-20240229-v1:0"):
        """Initialize Bedrock client"""
        self.region_name = region_name
        self.model_id = model_id
        self.bedrock_client = None
        self.last_analysis_result = None
        
        # Initialize enhanced search if available
        if ENHANCED_SEARCH_AVAILABLE:
            try:
                self.enhanced_search = EnhancedSearch()
                print("✅ Enhanced keyword search initialized")
            except Exception as e:
                print(f"⚠️ Enhanced search initialization failed: {e}")
                self.enhanced_search = None
        else:
            self.enhanced_search = None
        
        # Initialize debug logging - always enabled
        self.debug_enabled = True
        self._init_debug_logging()
    
    def _init_debug_logging(self):
        """Initialize debug logging directory"""
        self.debug_dir = Path("debug")
        self.debug_dir.mkdir(exist_ok=True)
    
    def _check_debug_enabled(self):
        """Check if debug is enabled from config"""
        try:
            config = BedrockConfig()
            return config.debug_enabled
        except:
            return False
    
    def select_icons_for_keyword(self, keyword: str, available_icons: list, top_n: int = 3) -> list:
        """Use Bedrock to select the most relevant icons for a keyword"""
        
        # Log request if debug logger is available
        try:
            from mcp_debug_logger import get_debug_logger
            logger = get_debug_logger()
            if logger:
                logger.log_bedrock_request(keyword, self.model_id, len(available_icons))
        except:
            pass
        
        # Initialize Bedrock client if needed
        if not self.bedrock_client:
            try:
                self.bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.region_name
                )
            except Exception as e:
                error_msg = f"⚠️ Bedrock Access Error: Unable to initialize Bedrock client. {str(e)}"
                print(error_msg)
                raise RuntimeError(error_msg) from e
        
        # Create a concise list of icons for the prompt (just names, cleaned up)
        # Send ALL icons, not just first 200
        icon_list = [icon.replace('.png', '').replace('_', ' ') for icon in available_icons]
        
        prompt = f"""You are an AWS architecture expert. Given the keyword "{keyword}", select the top {top_n} most relevant AWS service icons from the available list.

Available icons ({len(icon_list)} total):
{', '.join(icon_list)}

Rules:
1. Return ONLY the icon names, one per line
2. Return exactly {top_n} icons (or fewer if not enough relevant matches)
3. Prioritize exact matches and closely related services
4. For "S3" or "Simple Storage Service", return "Amazon Simple Storage Service Amazon S3"
5. Use the EXACT icon names from the list (with spaces, not underscores)

Keyword: {keyword}

Top {top_n} most relevant icons:"""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "temperature": 0.1,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            result_text = response_body['content'][0]['text'].strip()
            self.last_bedrock_response = result_text
            
            # Parse the response - extract icon names
            selected_names = []
            for line in result_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('Top'):
                    # Remove numbering like "1. " or "- "
                    clean_line = re.sub(r'^\d+\.\s*|-\s*', '', line).strip()
                    if clean_line:
                        selected_names.append(clean_line)
            
            # Convert back to icon filenames - improved matching
            icon_filenames = []
            for name in selected_names[:top_n]:
                # Try exact match first (with .png)
                exact_match = name.replace(' ', '_') + '.png'
                if exact_match in available_icons:
                    icon_filenames.append(exact_match)
                    continue
                
                # Try fuzzy matching
                name_lower = name.lower()
                best_match = None
                best_score = 0
                
                for icon in available_icons:
                    icon_clean = icon.replace('.png', '').replace('_', ' ').lower()
                    # Calculate similarity
                    if icon_clean == name_lower:
                        best_match = icon
                        break
                    elif name_lower in icon_clean or icon_clean in name_lower:
                        score = len(set(name_lower.split()) & set(icon_clean.split()))
                        if score > best_score:
                            best_score = score
                            best_match = icon
                
                if best_match:
                    icon_filenames.append(best_match)
            
            # Log response if debug logger is available
            try:
                from mcp_debug_logger import get_debug_logger
                logger = get_debug_logger()
                if logger:
                    logger.log_bedrock_response(keyword, icon_filenames, result_text)
            except:
                pass
            
            print(f"✅ Bedrock selected {len(icon_filenames)} icons for '{keyword}': {icon_filenames}")
            return icon_filenames
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Check for common Bedrock access issues
            if 'AccessDenied' in error_msg or 'UnauthorizedOperation' in error_msg:
                detailed_error = f"⚠️ Bedrock Access Denied: Check IAM permissions for bedrock:InvokeModel"
            elif 'ValidationException' in error_msg and 'model' in error_msg.lower():
                detailed_error = f"⚠️ Bedrock Model Access: Model '{self.model_id}' not accessible. Enable model access in Bedrock console"
            elif 'ResourceNotFoundException' in error_msg:
                detailed_error = f"⚠️ Bedrock Not Available: Bedrock service not available in region '{self.region_name}'"
            elif 'ExpiredToken' in error_msg or 'InvalidClientTokenId' in error_msg:
                detailed_error = f"⚠️ AWS Credentials Error: Invalid or expired AWS credentials"
            else:
                detailed_error = f"❌ Bedrock Error ({error_type}): {error_msg}"
            
            print(detailed_error)
            self.last_bedrock_response = detailed_error
            
            # Log error if debug logger is available
            try:
                from mcp_debug_logger import get_debug_logger
                logger = get_debug_logger()
                if logger:
                    logger.log_bedrock_response(keyword, [], detailed_error)
            except:
                pass
            
            # Re-raise with clear message
            raise RuntimeError(detailed_error) from e
    

        """Initialize debug logging"""
        try:
            import datetime
            import os
            
            # Create debug folder if it doesn't exist
            debug_folder = Path("debug")
            debug_folder.mkdir(exist_ok=True)
            
            # Create timestamped debug file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.debug_file = debug_folder / f"bedrock_debug_{timestamp}.log"
            
            with open(self.debug_file, 'w') as f:
                f.write(f"=== Bedrock Analyzer Debug Log ===\n")
                f.write(f"Started: {datetime.datetime.now()}\n")
                f.write(f"Region: {self.region_name}\n")
                f.write(f"Model: {self.model_id}\n\n")
                
            print(f"🐛 Debug logging enabled: {self.debug_file}")
        except Exception as e:
            print(f"Failed to initialize debug logging: {e}")
            self.debug_enabled = False
    
    def _debug_log(self, message, include_stack=False):
        """Log debug message to file"""
        try:
            import datetime
            import traceback
            
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_entry = f"[{timestamp}] {message}\n"
            
            if include_stack:
                log_entry += f"Stack trace:\n{''.join(traceback.format_stack())}\n"
            
            # Always print to console
            print(message)
            
            # Also write to debug file if enabled
            if self.debug_enabled and hasattr(self, 'debug_file') and self.debug_file:
                with open(self.debug_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                    f.flush()  # Force write to disk
                
        except Exception as e:
            print(f"Debug logging failed: {e}")
            print(message)  # Still print the original message
        
    def analyze_groups_only(self, image_path):
        """Focus ONLY on containers and groupings"""
        try:
            self.current_image_path = image_path
            
            if not self.bedrock_client:
                if not self.initialize_client():
                    return []
            
            # Encode image
            image_base64 = self.encode_image(image_path)
            if not image_base64:
                return []
            
            prompt = """Analyze this AWS architecture diagram and identify ONLY containers and groupings (NOT individual services):

Look for:
- AWS Cloud - the outermost boundary
- Regions - geographical containers  
- VPCs (Virtual Private Clouds) - large containers
- Subnets (public/private) - smaller containers within VPCs  
- Availability Zones - regional groupings
- Security Groups - logical groupings
- Auto Scaling Groups - service groupings

DO NOT include individual services like EC2 instances, load balancers, databases, etc.
ONLY include containers, boundaries, and groupings.

IMPORTANT: Return ONLY container/group names with quantities.

GOOD examples: "1 AWS Cloud", "2 VPCs", "4 public subnets", "2 regions"
BAD examples: "4 EC2 instances", "2 load balancers", "1 database"

Return a JSON object with this structure (ALWAYS include counts):
{
    "services": ["1 AWS Cloud", "2 VPCs", "4 public subnets"],
    "connections": ["describe container relationships"],
    "text_labels": ["visible container labels"],
    "groups": ["AWS Cloud", "VPC", "Public Subnet", "Private Subnet"]
}"""

            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response (simplified version)
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                start_idx = text_response.find('{')
                end_idx = text_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = text_response[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                    
                    # Store full analysis result including raw response for groups analysis
                    analysis_result['raw_response'] = text_response
                    self.last_analysis_result = analysis_result
                    
                    return analysis_result.get('services', [])
            
            return []
            
        except Exception as e:
            self._debug_log(f"Groups-only analysis error: {str(e)}")
            return []
    
    def analyze_services_only(self, image_path):
        """Focus ONLY on individual AWS service icons"""
        try:
            self.current_image_path = image_path
            
            if not self.bedrock_client:
                if not self.initialize_client():
                    return []
            
            # Encode image
            image_base64 = self.encode_image(image_path)
            if not image_base64:
                return []
            
            prompt = """Analyze this AWS architecture diagram and identify ONLY individual AWS service icons (NOT containers or groupings):

Look for specific AWS service icons like:
- EC2 instances
- RDS databases  
- Lambda functions
- S3 buckets
- Load balancers (Application, Network, Classic)
- NAT gateways
- Internet gateways
- Route tables
- Users/clients
- Any other individual AWS services

DO NOT include containers like VPCs, subnets, regions, AWS Cloud, availability zones.
ONLY include actual service icons and resources.

IMPORTANT: Return ONLY service names with quantities.

GOOD examples: "2 EC2 instances", "1 Application Load Balancer", "1 Internet Gateway", "1 User"
BAD examples: "2 VPCs", "4 public subnets", "1 AWS Cloud", "2 regions"

Return a JSON object with this structure (ALWAYS include counts):
{
    "services": ["2 EC2 instances", "1 Application Load Balancer", "1 Internet Gateway"],
    "connections": ["describe service connections"],
    "text_labels": ["visible service labels"],
    "groups": ["any service groupings"]
}"""

            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                start_idx = text_response.find('{')
                end_idx = text_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = text_response[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                    
                    # Store full analysis result including raw response for services analysis
                    analysis_result['raw_response'] = text_response
                    self.last_analysis_result = analysis_result
                    
                    return analysis_result.get('services', [])
            
            return []
            
        except Exception as e:
            self._debug_log(f"Services-only analysis error: {str(e)}")
            return []
    
    def analyze_text_description(self, description, mode='local', top_k=3, available_icons=None):
        """Analyze text description to extract AWS services
        
        Args:
            description: Architecture description text
            mode: 'local' for local semantic search, 'llm' for Bedrock icon selection
            top_k: Number of icons to return per service (for LLM mode)
            available_icons: Dict of icon mappings (required for LLM mode)
        """
        if mode == 'llm':
            return self._analyze_with_llm_selection(description, top_k=top_k, available_icons=available_icons)
        else:
            return self._analyze_with_local_selection(description)
    
    def _analyze_with_llm_selection(self, description, top_k=3, available_icons=None):
        """Use Bedrock to both extract services AND select exact icons"""
        try:
            if not self.bedrock_client:
                try:
                    self.bedrock_client = boto3.client(
                        service_name='bedrock-runtime',
                        region_name=self.region_name
                    )
                except Exception as e:
                    error_msg = f"⚠️ Bedrock Access Error: Unable to initialize Bedrock client. {str(e)}"
                    print(error_msg)
                    raise RuntimeError(error_msg) from e
            
            # Use provided icon mapping or load from file
            if available_icons:
                mapping = available_icons
            else:
                try:
                    with open('config/keywords_mapping.json', 'r') as f:
                        mapping = json.load(f)
                except Exception as e:
                    print(f"Error loading icons: {e}")
                    mapping = {}
            
            # Create a simple list of icon names with their main alias
            icon_options = []
            for icon_name, data in mapping.items():
                aliases = data.get('aliases', [])
                main_alias = aliases[0] if aliases else icon_name.replace('.png', '').replace('_', ' ')
                icon_options.append(f"{icon_name}: {main_alias}")
            
            icon_list = '\n'.join(icon_options)  # Send ALL icons
            
            prompt = f"""Analyze this AWS architecture and select EXACT icon filenames from the list.

Description: {description}

Available icons (format: filename: service_name):
{icon_list}

CRITICAL: 
- Return ONLY the exact filenames (with .png extension) from the left side of the list above
- For each AWS service mentioned, return up to {top_k} relevant icon variations
- Look for SPECIALIZED icons based on context (e.g., if "Lambda for IoT" → prefer "IoT_Lambda_function" over generic "AWS_Lambda")
- Include both specific and generic icons when available
- Consider the use case and architecture context when selecting icons

Return a JSON array of exact filenames.

Example:
Input: "DynamoDB table with Lambda"
Output: ["Amazon_DynamoDB.png", "AWS_Lambda.png"]

Your response (JSON array only):"""

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            print(f"🤖 Bedrock icon selection: {content}")
            self.last_bedrock_response = content
            
            import re
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                icon_names = json.loads(json_match.group())
                print(f"✅ Selected icons: {icon_names}")
                self.last_icon_names = icon_names  # Store for debugging
                return icon_names
            else:
                print(f"❌ No JSON array found in response")
            
            return []
            
        except RuntimeError:
            # Re-raise Bedrock access errors
            raise
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Check for common Bedrock access issues
            if 'AccessDenied' in error_msg or 'UnauthorizedOperation' in error_msg:
                detailed_error = f"⚠️ Bedrock Access Denied: Check IAM permissions for bedrock:InvokeModel"
            elif 'ValidationException' in error_msg and 'model' in error_msg.lower():
                detailed_error = f"⚠️ Bedrock Model Access: Model '{self.model_id}' not accessible. Enable model access in Bedrock console"
            elif 'ResourceNotFoundException' in error_msg:
                detailed_error = f"⚠️ Bedrock Not Available: Bedrock service not available in region '{self.region_name}'"
            elif 'ExpiredToken' in error_msg or 'InvalidClientTokenId' in error_msg:
                detailed_error = f"⚠️ AWS Credentials Error: Invalid or expired AWS credentials"
            else:
                detailed_error = f"❌ Bedrock Error ({error_type}): {error_msg}"
            
            print(detailed_error)
            raise RuntimeError(detailed_error) from e
    
    def _analyze_with_local_selection(self, description):
        """Use Bedrock to extract services, then local semantic search for icons"""
        try:
            # Initialize client if needed
            if not self.bedrock_client:
                try:
                    self.bedrock_client = boto3.client(
                        service_name='bedrock-runtime',
                        region_name=self.region_name
                    )
                except Exception as e:
                    error_msg = f"⚠️ Bedrock Access Error: Unable to initialize Bedrock client. {str(e)}"
                    print(error_msg)
                    raise RuntimeError(error_msg) from e
            
            # Load available icons from mapping
            try:
                with open('config/keywords_mapping.json', 'r') as f:
                    mapping = json.load(f)
                
                # Get all aliases for common services
                common_services = []
                for icon_name, data in mapping.items():
                    aliases = data.get('aliases', [])
                    if aliases:
                        # Add primary alias and alternates
                        common_services.append(aliases[0])
                        if len(aliases) > 1:
                            common_services.append(f"({', '.join(aliases[1:3])})")
                
                # Limit to fit in prompt (about 150 services)
                icon_list = ', '.join(common_services[:150])
            except:
                icon_list = "EC2, S3, Lambda, RDS, DynamoDB, VPC, etc."
            
            prompt = f"""Analyze this AWS architecture description and extract ALL AWS services mentioned or implied.

Description: {description}

Available icons (use these EXACT names):
{icon_list}

CRITICAL RULES:
1. Extract EVERY AWS service mentioned in the description
2. Include services that are clearly implied by the workflow
3. Use EXACT names from the available icons list
4. Use the MOST GENERAL icon unless a specific variant is mentioned
5. DO NOT add services that aren't mentioned or implied

Examples:

Input: "To query an Amazon DynamoDB table, a user runs a SQL query from Athena. Athena initiates a Lambda function."
Output: ["DynamoDB", "Athena", "Lambda"]
NOT: ["DynamoDB", "Lambda"] ❌ (missing Athena)

Input: "Store files in S3"
Output: ["Amazon S3"]
NOT: ["S3 File Gateway"] ❌

Input: "EC2 instances behind a load balancer store data in RDS"
Output: ["EC2", "Application Load Balancer", "RDS"]

Input: "Lambda processes S3 events and writes to DynamoDB"
Output: ["Lambda", "Amazon S3", "DynamoDB"]

Read the description carefully and extract ALL services. Return ONLY a JSON array.

Your response (JSON array only):"""

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            print(f"🤖 Bedrock raw response: {content}")
            
            # Store raw response for UI
            self.last_bedrock_response = content
            
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                services = json.loads(json_match.group())
                print(f"✅ Extracted services: {services}")
                
                # Map to default icons if needed
                default_mappings = {
                    'S3': 'Amazon S3',
                    'EC2': 'EC2',
                    'Lambda': 'Lambda',
                    'RDS': 'RDS',
                    'DynamoDB': 'DynamoDB',
                    'VPC': 'VPC',
                    'ECS': 'ECS',
                    'EKS': 'EKS',
                    'API Gateway': 'API Gateway',
                    'CloudFront': 'CloudFront'
                }
                
                # Replace with defaults if service is too specific
                cleaned_services = []
                replacements = []
                for service in services:
                    # If it's a specialized variant, check if we should use default
                    if 'File Gateway' in service or 'IoT' in service:
                        # Check if description actually mentions these terms
                        if 'file gateway' not in description.lower() and 'iot' not in description.lower():
                            # Use default instead
                            if 'S3' in service:
                                cleaned_services.append('Amazon S3')
                                replacements.append(f"'{service}' → 'Amazon S3'")
                                print(f"⚠️ Replaced '{service}' with 'Amazon S3' (not explicitly mentioned)")
                            elif 'Lambda' in service:
                                cleaned_services.append('Lambda')
                                replacements.append(f"'{service}' → 'Lambda'")
                                print(f"⚠️ Replaced '{service}' with 'Lambda' (not explicitly mentioned)")
                            continue
                    cleaned_services.append(service)
                
                self.last_replacements = replacements
                return cleaned_services
            
            return []
            
        except RuntimeError:
            # Re-raise Bedrock access errors
            raise
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Check for common Bedrock access issues
            if 'AccessDenied' in error_msg or 'UnauthorizedOperation' in error_msg:
                detailed_error = f"⚠️ Bedrock Access Denied: Check IAM permissions for bedrock:InvokeModel"
            elif 'ValidationException' in error_msg and 'model' in error_msg.lower():
                detailed_error = f"⚠️ Bedrock Model Access: Model '{self.model_id}' not accessible. Enable model access in Bedrock console"
            elif 'ResourceNotFoundException' in error_msg:
                detailed_error = f"⚠️ Bedrock Not Available: Bedrock service not available in region '{self.region_name}'"
            elif 'ExpiredToken' in error_msg or 'InvalidClientTokenId' in error_msg:
                detailed_error = f"⚠️ AWS Credentials Error: Invalid or expired AWS credentials"
            else:
                detailed_error = f"❌ Bedrock Error ({error_type}): {error_msg}"
            
            print(detailed_error)
            raise RuntimeError(detailed_error) from e
        """Focus ONLY on text labels and annotations"""
        try:
            self.current_image_path = image_path
            
            if not self.bedrock_client:
                if not self.initialize_client():
                    return []
            
            # Encode image
            image_base64 = self.encode_image(image_path)
            if not image_base64:
                return []
            
            prompt = """Analyze this AWS architecture diagram and identify services from text labels and annotations:

Look for:
- Service names written as text
- Resource labels and identifiers
- Configuration details in text
- AWS service names mentioned in labels
- Quantities mentioned in text (e.g., "2x EC2")

IMPORTANT: Return ONLY simple service names with quantities. Do NOT include descriptions, locations, or context.

GOOD examples: "2 EC2 instances", "1 Lambda function", "1 S3 bucket"
BAD examples: "EC2 instances running web servers", "Lambda function for processing", "S3 bucket for storage"

Use the text to identify or confirm AWS services. Include visual services if text confirms them.

Return a JSON object with this structure (ALWAYS include counts):
{
    "services": ["services identified from text with quantities"],
    "connections": ["connections mentioned in text"],
    "text_labels": ["all visible text labels"],
    "groups": ["groupings mentioned in text"]
}"""

            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                start_idx = text_response.find('{')
                end_idx = text_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = text_response[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                    
                    # Store full analysis result including raw response for text analysis
                    analysis_result['raw_response'] = text_response
                    self.last_analysis_result = analysis_result
                    
                    return analysis_result.get('services', [])
            
            return []
            
        except Exception as e:
            self._debug_log(f"Text-only analysis error: {str(e)}")
            return []

    def detect_architecture_pattern(self, image_path):
        """Detect the architecture pattern type from the image"""
        try:
            self.current_image_path = image_path
            
            if not self.bedrock_client:
                if not self.initialize_client():
                    return None
            
            # Load architecture patterns
            patterns = self.load_architecture_patterns()
            if not patterns:
                return None
            
            # Create pattern descriptions for LLM
            pattern_descriptions = []
            for pattern_id, pattern_data in patterns.items():
                services = [s["service"] for s in pattern_data["common_services"][:5]]  # Top 5 services
                pattern_descriptions.append(f"- {pattern_data['name']}: {pattern_data['description']} (typical services: {', '.join(services)})")
            
            patterns_text = "\n".join(pattern_descriptions)
            
            # Encode image
            image_base64 = self.encode_image(image_path)
            if not image_base64:
                return None
            
            prompt = f"""Analyze this AWS architecture diagram and identify which architecture pattern it most closely matches:

{patterns_text}

Look at the overall structure, service types, and connections to determine the best match.

Return a JSON object with the pattern identification:
{{
    "pattern": "pattern_id (e.g., web_application, serverless, etc.)",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation of why this pattern matches"
}}"""

            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                start_idx = text_response.find('{')
                end_idx = text_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = text_response[start_idx:end_idx]
                    pattern_result = json.loads(json_str)
                    
                    pattern_id = pattern_result.get('pattern')
                    if pattern_id in patterns:
                        return {
                            'pattern_id': pattern_id,
                            'pattern_data': patterns[pattern_id],
                            'confidence': pattern_result.get('confidence', 'medium'),
                            'reasoning': pattern_result.get('reasoning', '')
                        }
            
            return None
            
        except Exception as e:
            self._debug_log(f"Pattern detection error: {str(e)}")
            return None
    
    def load_architecture_patterns(self):
        """Load architecture patterns from JSON file"""
        try:
            import os
            patterns_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'architecture_patterns.json')
            
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    return json.load(f)
            else:
                self._debug_log(f"Architecture patterns file not found: {patterns_file}")
                return {}
                
        except Exception as e:
            self._debug_log(f"Failed to load architecture patterns: {str(e)}")
            return {}

    def validate_quantities(self, image_path, reconciled_services):
        """Pass 4: Validate quantities by visual counting"""
        try:
            self.current_image_path = image_path
            
            if not self.bedrock_client:
                if not self.initialize_client():
                    return []
            
            # Encode image
            image_base64 = self.encode_image(image_path)
            if not image_base64:
                return []
            
            services_text = ", ".join(reconciled_services)
            
            prompt = f"""Looking at this AWS architecture diagram, I found these services: {services_text}

Please carefully count each service type by visually examining the diagram and confirm the correct quantities.

For each service, count the actual visual instances you can see:
- Count individual EC2 instance icons
- Count individual database icons  
- Count individual gateway icons
- Count container boundaries (VPCs, subnets)

Return a JSON object with the validated quantities:
{{
    "services": ["correct quantity and service name based on visual count"],
    "connections": [],
    "text_labels": [],
    "groups": []
}}"""

            # Prepare request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                start_idx = text_response.find('{')
                end_idx = text_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = text_response[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                    return analysis_result.get('services', [])
            
            return []
            
        except Exception as e:
            self._debug_log(f"Validation pass error: {str(e)}")
            return []

    def improve_analysis(self, image_path, icons_catalog, current_icons):
        """Improve analysis by asking LLM to find missed services or refine results"""
        try:
            # Store image path for potential disambiguation
            self.current_image_path = image_path
            
            if not self.bedrock_client:
                if not self.initialize_client():
                    return []
            
            # Create improvement prompt with current context
            current_icons_text = ", ".join(current_icons) if current_icons else "none"
            
            prompt = f"""I previously analyzed this AWS architecture diagram and found these icons: {current_icons_text}

Please re-examine this diagram more carefully and look for:
1. Any AWS services I might have missed
2. Additional instances of services already found
3. Supporting services (like Internet Gateways, Route Tables, etc.)
4. Any containers or groupings I missed

Focus on finding services that are clearly visible but might have been overlooked in the initial analysis.

Respond in the same JSON format:
{{
    "services": ["list of AWS services with quantities"],
    "connections": ["describe connections"],
    "text_labels": ["visible text labels"],
    "groups": ["containers and groupings"]
}}"""

            # Encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare message for Claude
            message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }

            # Call Claude
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [message]
                })
            )

            response_body = json.loads(response['body'].read())
            text_response = response_body['content'][0]['text']
            
            self._debug_log(f"Improvement analysis response: {text_response}")
            
            # Parse JSON response
            try:
                json_start = text_response.find('{')
                json_end = text_response.rfind('}') + 1
                json_str = text_response[json_start:json_end]
                
                analysis_result = json.loads(json_str)
                services = analysis_result.get('services', [])
                
                # Store the improved analysis result
                self.last_analysis_result = analysis_result
                
                self._debug_log(f"Improved services found: {services}")
                return services
                
            except json.JSONDecodeError as e:
                self._debug_log(f"JSON parsing failed: {e}")
                return []
            
        except Exception as e:
            self._debug_log(f"Improvement analysis failed: {e}")
            return []

    def save_debug_info(self, debug_data):
        """Save debug information to file"""
        try:
            import datetime
            
            # Create debug folder if it doesn't exist
            debug_folder = Path("debug")
            debug_folder.mkdir(exist_ok=True)
            
            # Create timestamped debug file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = debug_folder / f"analysis_debug_{timestamp}.json"
            
            with open(debug_file, 'w') as f:
                json.dump(debug_data, f, indent=2)
                
            self._debug_log(f"Debug info saved to: {debug_file}")
            return str(debug_file)
        except Exception as e:
            self._debug_log(f"Failed to save debug info: {e}")
            return None

    def resolve_ambiguous_match(self, image_path, service_name, match_options):
        """Use LLM to resolve ambiguous icon matches by analyzing the image"""
        try:
            self._debug_log(f"🤖 Starting LLM disambiguation for '{service_name}'")
            
            # Prepare the disambiguation prompt
            options_text = "\n".join([f"- {opt['name']}" for opt in match_options])
            
            prompt = f"""Looking at this architecture diagram, I need to identify the specific type of "{service_name}" shown.

The possible options are:
{options_text}

Please analyze the image and determine which specific option best matches what is actually shown in the diagram. Consider:
1. The visual appearance of the icon/component
2. The architectural context and connections
3. Any labels or text near the component
4. Common usage patterns in AWS architectures

Respond with just the exact name from the options above that best matches what you see."""

            # Encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare message for Claude
            message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }

            # Call Claude
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [message]
                })
            )

            response_body = json.loads(response['body'].read())
            self._debug_log(f"DEBUG: Response body type: {type(response_body)}")
            self._debug_log(f"DEBUG: Response body: {response_body}")
            
            # Handle response parsing safely
            try:
                content = response_body.get('content', [])
                if isinstance(content, list) and len(content) > 0:
                    llm_choice = content[0].get('text', '').strip()
                else:
                    llm_choice = str(content).strip()
            except Exception as parse_error:
                self._debug_log(f"❌ Response parsing error: {parse_error}")
                return match_options[0]
            
            self._debug_log(f"🤖 LLM disambiguation for '{service_name}': {llm_choice}")
            
            # Find the matching option
            for option in match_options:
                if option['name'] in llm_choice or llm_choice in option['name']:
                    self._debug_log(f"✅ LLM selected: {option['name']}")
                    return option
            
            # Fallback to first option if no clear match
            self._debug_log(f"⚠️ LLM response unclear, using top match: {match_options[0]['name']}")
            return match_options[0]
            
        except Exception as e:
            self._debug_log(f"❌ LLM disambiguation failed: {e}")
            import traceback
            traceback.print_exc()
            return match_options[0]  # Fallback to top match
        """Save debug information to file"""
        try:
            # Create debug folder if it doesn't exist
            debug_folder = Path("debug")
            debug_folder.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%m%d%Y-%H%M")
            debug_file = debug_folder / f"trace-{timestamp}.txt"
            
            # Write debug info to file
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("AWS ICONS ANALYSIS DEBUG TRACE\n")
                f.write("=" * 50 + "\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {self.model_id}\n")
                f.write(f"Region: {self.region_name}\n\n")
                
                if 'identified_services' in debug_data:
                    f.write("IDENTIFIED SERVICES:\n")
                    f.write("-" * 20 + "\n")
                    for i, service in enumerate(debug_data['identified_services'], 1):
                        f.write(f"{i}. {service}\n")
                    f.write("\n")
                
                if 'matching_icons' in debug_data:
                    f.write("ICON MATCHING RESULTS:\n")
                    f.write("-" * 25 + "\n")
                    for service, matches in debug_data['matching_icons'].items():
                        f.write(f"• {service}\n")
                        if matches:
                            for match in matches:
                                f.write(f"  → {match['name']} ({match['category']})\n")
                        else:
                            f.write("  → No icon matches found\n")
                    f.write("\n")
                
                if 'raw_response' in debug_data:
                    f.write("RAW LLM RESPONSE:\n")
                    f.write("-" * 18 + "\n")
                    f.write(debug_data['raw_response'])
                    f.write("\n\n")
                
                if 'analysis_result' in debug_data:
                    f.write("PARSED ANALYSIS:\n")
                    f.write("-" * 16 + "\n")
                    f.write(json.dumps(debug_data['analysis_result'], indent=2))
                    f.write("\n")
            
            print(f"Debug info saved to: {debug_file}")
            return str(debug_file)
            
        except Exception as e:
            print(f"Failed to save debug info: {e}")
            return None
        
    def initialize_client(self):
        """Initialize Bedrock client"""
        try:
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
            return True
        except Exception as e:
            error_msg = f"⚠️ Bedrock Access Error: Unable to initialize Bedrock client. {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg) from e
    
    def encode_image(self, image_path):
        """Encode image to base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Failed to encode image: {e}")
            return None
    
    def analyze_image(self, image_path, icons_catalog):
        """Analyze image for AWS services and icons"""
        # Store image path for potential disambiguation
        self.current_image_path = image_path
        
        if not self.bedrock_client:
            if not self.initialize_client():
                return [], None
        
        # Encode image
        image_base64 = self.encode_image(image_path)
        if not image_base64:
            return [], None
        
        # Create analysis prompt
        prompt = """
        Analyze this AWS architecture diagram and identify:
        
        1. AWS SERVICES: List all AWS service icons you can see
        2. CONNECTIONS: Describe arrows and lines connecting components  
        3. TEXT LABELS: List any text labels or service names visible
        4. GROUPS: Describe any grouped components or containers
        
        IMPORTANT: For subnets, try to identify if they are:
        - "private subnet" (no direct internet access, typically contains databases/backend)
        - "public subnet" (has internet gateway access, typically contains load balancers/web servers)
        If you can't determine the type, include both "private subnet" and "public subnet"
        
        Return a JSON object with this structure (ALWAYS include counts):
        {
            "services": ["2 EC2 instances", "1 Application Load Balancer", "1 Internet Gateway"],
            "connections": ["arrow from A to B", "bidirectional between X and Y"],
            "text_labels": ["label1", "label2"],
            "groups": ["VPC container", "private subnet", "public subnet"]
        }
        """
        
        # Prepare request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                
                # Try to extract JSON from response
                try:
                    start_idx = text_response.find('{')
                    end_idx = text_response.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = text_response[start_idx:end_idx]
                        analysis_result = json.loads(json_str)
                        # Always include raw response for debugging
                        analysis_result['raw_response'] = text_response
                        services = analysis_result.get('services', [])
                        
                        # Save debug info if enabled
                        config = BedrockConfig()
                        print(f"DEBUG: debug_enabled = {config.debug_enabled}")
                        if config.debug_enabled:
                            print("DEBUG: Creating debug info...")
                            debug_data = {
                                'identified_services': services,
                                'raw_response': text_response,
                                'analysis_result': analysis_result
                            }
                            debug_file = self.save_debug_info(debug_data)
                            print(f"DEBUG: Debug file saved to: {debug_file}")
                            analysis_result['debug_file'] = debug_file
                            analysis_result['debug_enabled'] = True
                        
                        # Store analysis result for debug access
                        self.last_analysis_result = analysis_result
                        return services
                    
                except json.JSONDecodeError:
                    pass
                
                # Fallback: extract service names from text
                all_icon_names = []
                for category, icons in icons_catalog.items():
                    all_icon_names.extend(icons.keys())
                
                identified_services = []
                for icon_name in all_icon_names:
                    if icon_name.lower() in text_response.lower():
                        identified_services.append(icon_name)
                
                return identified_services[:10], {"raw_response": text_response}
            
            return [], None
            
        except Exception as e:
            print(f"Bedrock analysis failed: {e}")
            return [], None
    
    def find_matching_icons(self, identified_services, icons_catalog):
        """Find matching icons using enhanced keyword search or fallback"""
        
        # Try enhanced search first if available
        if self.enhanced_search:
            return self.find_matching_icons_enhanced(identified_services, icons_catalog)
        else:
            return self.find_matching_icons_fallback(identified_services, icons_catalog)
    
    def find_matching_icons_enhanced(self, identified_services, icons_catalog):
        """Enhanced matching using LLM-generated keywords"""
        matching_icons = []
        
        self._debug_log("🚀 Using enhanced keyword matching")
        self._debug_log(f"Input services: {identified_services}")
        
        # Basic safety check
        if not identified_services:
            self._debug_log(f"❌ No services provided")
            return []
        
        # Handle case where identified_services is a tuple like ([], None)
        if isinstance(identified_services, tuple):
            identified_services = identified_services[0] if identified_services[0] else []
        
        if not isinstance(identified_services, list):
            self._debug_log(f"❌ Services not a list: {type(identified_services)}")
            return []
        
        # Process both services and groups from LLM analysis
        all_items = identified_services[:]
        
        # Check if groups were found in analysis
        groups_found = []
        if hasattr(self, 'last_analysis_result') and self.last_analysis_result:
            groups_found = self.last_analysis_result.get('groups', [])
            if groups_found:
                self._debug_log(f"📦 Found {len(groups_found)} groups: {groups_found}")
                all_items.extend(groups_found)
        
        self._debug_log(f"All items to process: {all_items}")
        
        for service in all_items:
            self._debug_log(f"Processing service: {service}")
            
            # Extract quantity and clean service name
            quantity, cleaned_service = self.extract_quantity_and_clean(service)
            self._debug_log(f"Enhanced matching for '{service}' -> Quantity: {quantity}, Cleaned: '{cleaned_service}'")
            
            # PRIORITY RULE: For services containing "Group", prioritize Group_ icons
            prefer_groups = "group" in cleaned_service.lower()
            
            # RULE: If this is a group item, ensure we process it (don't skip group icons)
            is_group_item = self._is_group_service(cleaned_service)
            if is_group_item:
                self._debug_log(f"🏗️ Processing group item: '{cleaned_service}'")
            else:
                # RULE: Skip group icons if groups were found in analysis AND this is not explicitly a group
                if groups_found and not prefer_groups:
                    # This is a service item, process normally but don't prefer group icons
                    pass
            
            # Use enhanced search to find matches
            matches = self.enhanced_search.find_service_matches(cleaned_service, icons_catalog)
            self._debug_log(f"Enhanced search returned {len(matches)} matches: {[m['name'] for m in matches]}")
            
            if matches:
                # If service name contains "Group", prioritize Group_ icons
                if prefer_groups:
                    group_matches = [m for m in matches if m['name'].startswith('Group_')]
                    if group_matches:
                        matches = group_matches + [m for m in matches if not m['name'].startswith('Group_')]
                        self._debug_log(f"🏗️ Prioritized group matches: {[m['name'] for m in group_matches]}")
                
                best_match = matches[0]
                
                # Check for multiple high-scoring matches that need visual disambiguation
                high_score_matches = [m for m in matches if m.get('score', 0) >= best_match.get('score', 0) * 0.8]
                
                if len(high_score_matches) > 1 and hasattr(self, 'current_image_path') and self.current_image_path:
                    self._debug_log(f"🤖 Multiple high-scoring matches found for '{cleaned_service}': {[m['name'] for m in high_score_matches]}")
                    self._debug_log(f"🤖 Using visual comparison to select best match")
                    best_match = self.resolve_ambiguous_match(self.current_image_path, cleaned_service, high_score_matches)
                    self._debug_log(f"🤖 Visual analysis selected: {best_match['name']}")
                elif best_match.get('ambiguous', False) and hasattr(self, 'current_image_path'):
                    self._debug_log(f"🤖 Using LLM to resolve ambiguous match for '{cleaned_service}'")
                    alternatives = [best_match] + best_match.get('alternatives', [])
                    best_match = self.resolve_ambiguous_match(self.current_image_path, cleaned_service, alternatives)
                    self._debug_log(f"🤖 LLM selected: {best_match}")
                
                self._debug_log(f"Best match: {best_match}")
                
                for i in range(quantity):
                    icon_entry = {
                        "name": best_match['name'],
                        "path": best_match['path'],
                        "category": best_match['category']
                    }
                    matching_icons.append(icon_entry)
                    self._debug_log(f"Added icon {i+1}/{quantity}: {icon_entry}")
                    
                self._debug_log(f"✅ Enhanced match: '{cleaned_service}' -> '{best_match['name']}' x{quantity} (score: {best_match.get('score', 'N/A')})")
            else:
                self._debug_log(f"❌ No enhanced match found for '{service}'")
        
        self._debug_log(f"Final matching_icons count: {len(matching_icons)}")
        self._debug_log(f"Final matching_icons: {matching_icons}")
        return matching_icons
    
    def _is_group_service(self, service_name):
        """Check if a service name refers to a group/container"""
        group_indicators = [
            'vpc', 'availability zone', 'subnet', 'security group', 
            'auto scaling group', 'aws cloud', 'region', 'account'
        ]
        service_lower = service_name.lower()
        return any(indicator in service_lower for indicator in group_indicators)
    
    def find_matching_icons_fallback(self, identified_services, icons_catalog):
        """Fallback matching using original algorithm"""
        self._debug_log("⚠️ Using fallback matching (enhanced search not available)")
        return self.find_matching_icons_original(identified_services, icons_catalog)
    
    def find_matching_icons_original(self, identified_services, icons_catalog):
        """Find matching icons in catalog with improved matching"""
        matching_icons = []
        
        # Enhanced service name mappings (exclude group icons)
        service_mappings = {
            'ec2': ['ec2', 'elastic_compute_cloud', 'amazon_ec2'],
            'application load balancer': ['application_load_balancer'],
            'internet gateway': ['internet_gateway'],
            'auto scaling': ['auto_scaling', 'ec2_auto_scaling'],
            'load balancer': ['load_balancer', 'elastic_load_balancing', 'application_load_balancer'],
            'nat gateway': ['nat_gateway'],
            'nat gateways': ['nat_gateway'],  # Handle plural form
            'vpc': ['virtual_private_cloud'],  # Service VPC, not group
            'rds': ['relational_database_service', 'amazon_rds'],
            's3': ['simple_storage_service', 'amazon_s3'],
            'lambda': ['lambda'],
            'api gateway': ['api_gateway'],
            'cloudfront': ['cloudfront'],
            'route 53': ['route_53'],
            'elastic beanstalk': ['elastic_beanstalk']
        }
        
        # Group/Container mappings (only for items identified as groups)
        # Updated group mappings with correct icon names (for search terms)
        group_mappings = {
            'aws cloud': ['Group_AWSCloud_1'],
            'vpc': ['Group_VirtualPrivateCloud'],
            'vpcs': ['Group_VirtualPrivateCloud'],
            'auto scaling group': ['Group_AutoScalingGroup'],
            'availability zone': ['Group_AvailabilityZone'],
            'region': ['Group_Region'],
            'regions': ['Group_Region'],
            'public subnet': ['Group_PublicSubnet'],
            'public subnets': ['Group_PublicSubnet'],
            'private subnet': ['Group_Privatesubnet'],
            'private subnets': ['Group_Privatesubnet'],
            'subnet': ['Group_PublicSubnet', 'Group_Privatesubnet'],
            'subnets': ['Group_PublicSubnet', 'Group_Privatesubnet'],
            'security group': ['Group_Securitygroup'],
            'security groups': ['Group_Securitygroup'],
            'account': ['Group_AWSAccount'],
            'container': ['Group_GenericGroup'],
            'group': ['Group_GenericGroup']
        }
        
        for service in identified_services:
            found_match = False
            
            # Extract quantity and clean the service name
            quantity, cleaned_service = self.extract_quantity_and_clean(service)
            self._debug_log(f"DEBUG: Original service: '{service}' -> Quantity: {quantity}, Cleaned: '{cleaned_service}'")
            
            # Determine if this is a group/container or a service
            is_group = self.is_group_item(service, cleaned_service)
            self._debug_log(f"DEBUG: '{service}' identified as {'GROUP' if is_group else 'SERVICE'}")
            self._debug_log(f"DEBUG: Will search in {'GROUP' if is_group else 'SERVICE'} mappings")
            
            # Use appropriate mappings based on type
            if is_group:
                search_mappings = group_mappings
                # Only search in Groups category for group items
                search_categories = {k: v for k, v in icons_catalog.items() if 'group' in k.lower()}
                self._debug_log(f"DEBUG: Using group mappings: {list(group_mappings.keys())}")
                self._debug_log(f"DEBUG: Group categories available: {list(search_categories.keys())}")
            else:
                search_mappings = service_mappings
                # Exclude Groups category for service items
                search_categories = {k: v for k, v in icons_catalog.items() if 'group' not in k.lower()}
                self._debug_log(f"DEBUG: Using service mappings: {list(service_mappings.keys())}")
                self._debug_log(f"DEBUG: Service categories available: {list(search_categories.keys())}")
            
            # Try exact match first
            for category, icons in search_categories.items():
                if cleaned_service in icons:
                    # Add multiple instances based on quantity
                    for i in range(quantity):
                        matching_icons.append({
                            "name": cleaned_service,
                            "path": icons[cleaned_service],
                            "category": category
                        })
                    found_match = True
                    self._debug_log(f"DEBUG: Exact match found for '{cleaned_service}' x{quantity}")
                    break
            
            if not found_match:
                # Try mapped service names
                search_terms = search_mappings.get(cleaned_service.lower(), [cleaned_service.lower()])
                self._debug_log(f"DEBUG: Trying search terms: {search_terms}")
                self._debug_log(f"DEBUG: Available mappings: {list(search_mappings.keys())}")
                
                for search_term in search_terms:
                    if found_match:
                        break
                    self._debug_log(f"DEBUG: Searching for term: '{search_term}'")
                    for category, icons in search_categories.items():
                        self._debug_log(f"DEBUG: Checking category '{category}' with {len(icons)} icons")
                        for icon_name, icon_path in icons.items():
                            icon_name_lower = icon_name.lower()
                            if search_term in icon_name_lower:
                                self._debug_log(f"DEBUG: MATCH FOUND! '{search_term}' matches '{icon_name}'")
                                # Add multiple instances based on quantity
                                for i in range(quantity):
                                    matching_icons.append({
                                        "name": icon_name,
                                        "path": icon_path,
                                        "category": category
                                    })
                                found_match = True
                                self._debug_log(f"DEBUG: Match found: '{search_term}' -> '{icon_name}' x{quantity}")
                                break
                        if found_match:
                            break
                
                # If still no match, try broader partial matching
                if not found_match:
                    key_words = cleaned_service.lower().replace('-', ' ').replace('_', ' ').split()
                    self._debug_log(f"DEBUG: Trying key words: {key_words}")
                    for key_word in key_words:
                        if found_match or len(key_word) < 3:
                            break
                        for category, icons in search_categories.items():
                            for icon_name, icon_path in icons.items():
                                icon_name_lower = icon_name.lower()
                                # More precise matching: word boundaries or exact substring at start
                                if (key_word == icon_name_lower or 
                                    icon_name_lower.startswith(key_word + '_') or
                                    icon_name_lower.startswith(key_word + ' ') or
                                    ('_' + key_word + '_' in icon_name_lower) or
                                    ('_' + key_word) == icon_name_lower[-len(key_word)-1:]):
                                    # Add multiple instances based on quantity
                                    for i in range(quantity):
                                        matching_icons.append({
                                            "name": icon_name,
                                            "path": icon_path,
                                            "category": category
                                        })
                                    found_match = True
                                    self._debug_log(f"DEBUG: Keyword match: '{key_word}' -> '{icon_name}' x{quantity}")
                                    break
                            if found_match:
                                break
            
            if not found_match:
                self._debug_log(f"DEBUG: No match found for '{service}' (cleaned: '{cleaned_service}')")
        
        return matching_icons
    
    def extract_quantity_and_clean(self, service_name):
        """Extract quantity from service name and return cleaned name"""
        import re
        
        self._debug_log(f"extract_quantity_and_clean called with: {service_name} (type: {type(service_name)})")
        
        # Safety check - ensure service_name is a string
        if isinstance(service_name, list):
            self._debug_log(f"WARNING: service_name is a list: {service_name}", include_stack=True)
            service_name = str(service_name[0]) if service_name else ""
        elif not isinstance(service_name, str):
            self._debug_log(f"WARNING: service_name is not a string: {type(service_name)} - {service_name}", include_stack=True)
            service_name = str(service_name)
        
        try:
            # Extract number at the beginning: "2 EC2 instances" -> quantity=2, name="EC2 instances"
            match = re.match(r'^(\d+)\s+(.+)', service_name.strip())
        except Exception as e:
            self._debug_log(f"ERROR in extract_quantity_and_clean: {e}", include_stack=True)
            raise
        if match:
            quantity = int(match.group(1))
            cleaned_name = match.group(2)
        else:
            quantity = 1
            cleaned_name = service_name
        
        # Apply additional cleaning
        cleaned_name = self.clean_service_name(cleaned_name)
        
        return quantity, cleaned_name
    
    def is_group_item(self, original_service, cleaned_service):
        """Determine if an item is a group/container or a service"""
        # Check for explicit group indicators
        group_indicators = [
            'aws cloud', 'vpc', 'vpcs', 'subnet', 'subnets', 'public subnet', 'private subnet',
            'availability zone', 'region', 'regions', 'account', 'security group', 
            'auto scaling group', 'container', 'group'
        ]
        
        original_lower = original_service.lower()
        cleaned_lower = cleaned_service.lower()
        
        # Also check a version with parentheses removed for better matching
        import re
        original_no_parens = re.sub(r'\s*\([^)]*\)', '', original_service).lower()
        cleaned_no_parens = re.sub(r'\s*\([^)]*\)', '', cleaned_service).lower()
        
        self._debug_log(f"DEBUG GROUP CHECK: original='{original_service}' -> '{original_lower}'")
        self._debug_log(f"DEBUG GROUP CHECK: cleaned='{cleaned_service}' -> '{cleaned_lower}'")
        self._debug_log(f"DEBUG GROUP CHECK: original_no_parens='{original_no_parens}'")
        self._debug_log(f"DEBUG GROUP CHECK: cleaned_no_parens='{cleaned_no_parens}'")
        
        # Check if it contains group indicators (exact matches or contains)
        for indicator in group_indicators:
            if (indicator in original_lower or indicator in cleaned_lower or 
                indicator in original_no_parens or indicator in cleaned_no_parens):
                self._debug_log(f"DEBUG GROUP MATCH: Found indicator '{indicator}' in service")
                return True
        
        # Check if it has container descriptions in parentheses
        if '(' in original_service and ')' in original_service:
            self._debug_log(f"DEBUG GROUP MATCH: Found parentheses in '{original_service}'")
            return True
        
        self._debug_log(f"DEBUG GROUP CHECK: No group indicators found")
        return False
    
    def clean_service_name(self, service_name):
        """Clean service name by removing numbers and common prefixes"""
        import re
        
        # Remove numbers and common prefixes like "1 ", "2 ", etc.
        cleaned = re.sub(r'^\d+\s+', '', service_name)
        
        # Remove common suffixes like "instances" -> "instance"
        cleaned = re.sub(r'instances?$', 'instance', cleaned, flags=re.IGNORECASE)
        
        # DON'T remove "Group" - it's important for group icon matching!
        # The old line was: cleaned = re.sub(r'\s+group$', '', cleaned, flags=re.IGNORECASE)
        
        # Handle container descriptions - extract the main part
        # "AWS Cloud (outer container)" -> "AWS Cloud"
        # "VPC (main container)" -> "VPC"
        # "Auto Scaling Group (contains EC2 instances)" -> "Auto Scaling Group"
        cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)
        
        return cleaned.strip()

# Configuration class with Claude model selection
class BedrockConfig:
    def __init__(self):
        self.debug_enabled = False
        self.load_config()
        
        # Available Claude models
        self.models = {
            "US Models": {
                "Claude 3.7 Sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "Claude Sonnet 4": "us.anthropic.claude-sonnet-4-20250514-v1:0", 
                "Claude Opus 4.1": "us.anthropic.claude-opus-4-1-20250805-v1:0",
                "Claude Sonnet 4.5": "anthropic.claude-sonnet-4-5-20250929-v1:0"
            },
            "EU Models": {
                "Claude 3.7 Sonnet": "eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "Claude Sonnet 4": "eu.anthropic.claude-sonnet-4-20250514-v1:0"
            }
        }
        
        self.regions = {
            "US": ["us-east-1", "us-west-2"],
            "EU": ["eu-west-3", "eu-central-1"]
        }
        
        # Default settings
        self.region = "us-east-1"
        self.model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        self.max_tokens = 4000
        self.temperature = 0.1
        self.top_k_icons = 3  # Default number of icons to return per keyword
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            # Try different possible paths for the config file
            config_paths = [
                Path(__file__).parent.parent / "inputs" / "bedrock_config.yaml",  # ArchMCP inputs
                Path("bedrock_config.yaml"),  # Current directory
                Path("../../input/bedrock_config.yaml"),  # Input folder from src/application
                Path(__file__).parent.parent.parent / "input" / "bedrock_config.yaml"  # Absolute path to input folder
            ]
            
            config_found = False
            for config_path in config_paths:
                print(f"DEBUG: Trying config at: {config_path}")
                if config_path.exists():
                    print(f"DEBUG: Config found at: {config_path}")
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        debug_setting = config.get('debug', {}).get('enabled', False)
                        print(f"DEBUG: Config loaded, debug.enabled = {debug_setting}")
                        self.debug_enabled = debug_setting
                        
                        # Load top_k_icons setting
                        bedrock_config = config.get('bedrock', {})
                        self.top_k_icons = bedrock_config.get('top_k_icons', 3)
                        print(f"DEBUG: top_k_icons = {self.top_k_icons}")
                        
                        config_found = True
                        break
            
            if not config_found:
                print("DEBUG: No config file found in any location")
                
        except Exception as e:
            print(f"Failed to load config: {e}")
    
    def get_models_for_region_group(self, region_group):
        """Get available models for region group (US/EU)"""
        return self.models.get(region_group, {})
    
    def get_regions_for_group(self, region_group):
        """Get available regions for region group"""
        return self.regions.get(region_group, [])
    
    def get_analyzer(self):
        return BedrockAnalyzer(self.region, self.model_id)
