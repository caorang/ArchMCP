import os
from pathlib import Path
from typing import Dict, List
import re

class PromptManager:
    """Manages and renders LLM prompts"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_cache = {}
    
    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from file"""
        if prompt_name in self.prompts_cache:
            return self.prompts_cache[prompt_name]
        
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            # Return default prompt if file doesn't exist
            return self._get_default_prompt(prompt_name)
        
        with open(prompt_file, "r") as f:
            prompt = f.read()
        
        self.prompts_cache[prompt_name] = prompt
        return prompt
    
    def render_template(self, template: str, variables: Dict[str, str]) -> str:
        """Render prompt template with variables"""
        rendered = template
        
        for key, value in variables.items():
            # Replace {key} with value
            rendered = rendered.replace(f"{{{key}}}", str(value))
        
        return rendered
    
    def get_available_prompts(self) -> List[str]:
        """Get list of available prompt templates"""
        if not self.prompts_dir.exists():
            return ["master_orchestrator", "multi_step", "fix_code", "architecture_analysis", "class_mapping", "code_generation", "mermaid_master", "mermaid_flowchart", "mermaid_fix"]
        
        prompts = []
        for file in self.prompts_dir.glob("*.txt"):
            prompts.append(file.stem)
        
        return prompts
    
    def clear_cache(self):
        """Clear the prompts cache to force reload from files"""
        self.prompts_cache = {}
    
    def reload_prompt(self, prompt_name: str) -> str:
        """Force reload a specific prompt from file"""
        if prompt_name in self.prompts_cache:
            del self.prompts_cache[prompt_name]
        return self.load_prompt(prompt_name)
    
    def _get_default_prompt(self, prompt_name: str) -> str:
        """Get default prompt if file doesn't exist"""
        
        if prompt_name == "master_orchestrator":
            return """You are an AWS Architecture Diagram Generator. Create Python code using the Diagrams library to generate AWS architecture diagrams.

Application Description: {description}

Process this in 3 steps:

STEP 1 - ARCHITECTURE ANALYSIS:
Analyze the application and identify required AWS services, their purposes, and relationships.

STEP 2 - CLASS VALIDATION: 
Map each identified service to exact Diagrams library classes from the ALLOWED_CLASSES list below.

STEP 3 - CODE GENERATION:
Generate clean Python code using only validated classes.

ALLOWED_CLASSES (use EXACTLY as listed):
[
    "diagrams.aws.analytics.Athena",
    "diagrams.aws.analytics.EMR", 
    "diagrams.aws.analytics.Glue",
    "diagrams.aws.analytics.Kinesis",
    "diagrams.aws.analytics.KinesisDataFirehose",
    "diagrams.aws.analytics.KinesisDataStreams", 
    "diagrams.aws.analytics.Quicksight",
    "diagrams.aws.analytics.Redshift",
    "diagrams.aws.compute.EC2",
    "diagrams.aws.compute.ECS",
    "diagrams.aws.compute.EKS",
    "diagrams.aws.compute.ElasticBeanstalk", 
    "diagrams.aws.compute.Fargate",
    "diagrams.aws.compute.Lambda",
    "diagrams.aws.database.Aurora",
    "diagrams.aws.database.Dynamodb",
    "diagrams.aws.database.Elasticache",
    "diagrams.aws.database.RDS",
    "diagrams.aws.database.Redshift",
    "diagrams.aws.integration.APIGateway",
    "diagrams.aws.integration.Eventbridge", 
    "diagrams.aws.integration.SNS",
    "diagrams.aws.integration.SQS",
    "diagrams.aws.integration.StepFunctions",
    "diagrams.aws.network.ALB",
    "diagrams.aws.network.CloudFront",
    "diagrams.aws.network.ELB",
    "diagrams.aws.network.InternetGateway",
    "diagrams.aws.network.Route53",
    "diagrams.aws.network.VPC",
    "diagrams.aws.security.Cognito",
    "diagrams.aws.security.IAM", 
    "diagrams.aws.security.KMS",
    "diagrams.aws.security.WAF",
    "diagrams.aws.storage.EBS",
    "diagrams.aws.storage.S3",
    "diagrams.aws.general.User"
]

FINAL OUTPUT REQUIREMENTS:
- Provide ONLY the final Python code
- No explanations, analysis, or intermediate steps in the output
- Use filename="diagram" 
- Output formats: ["png", "svg"]
- Use exact class names from ALLOWED_CLASSES list
- Ensure proper imports and connections

Example structure:
```python
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.storage import S3

with Diagram("Title", filename="diagram", show=False, outformat=["png", "svg"]):
    # Your architecture code here
```"""
        
        elif prompt_name == "fix_code":
            return """You are a Python debugging expert. Fix the following Python code that uses the diagrams library.

Original Code:
{code}

Error Message:
{error}

CORRECT IMPORT MAPPINGS (use these exact imports):

COMPUTE:
- from diagrams.aws.compute import Lambda, EC2, ECS, EKS, Fargate

DATABASE: 
- from diagrams.aws.database import RDS, Aurora, Dynamodb, Elasticache

NETWORK:
- from diagrams.aws.network import APIGateway, ALB, ELB, CloudFront, Route53, VPC

INTEGRATION:
- from diagrams.aws.integration import SNS, SQS, StepFunctions

STORAGE:
- from diagrams.aws.storage import S3, EBS

COMMON FIXES:
- APIGateway is in diagrams.aws.network (NOT integration)
- Change "from diagrams.aws.integration import APIGateway" to "from diagrams.aws.network import APIGateway"

Provide ONLY the corrected Python code, no explanations."""
        
        elif prompt_name == "multi_step":
            return """Step 1: Analyze the architecture description and identify AWS services needed.

Application Description: {description}

Please identify the required AWS services and their relationships for this architecture."""
        
        elif prompt_name == "mermaid_master":
            return """You are an AWS Architecture Diagram Generator. Create Mermaid flowchart code to visualize AWS architecture.

Application Description: {description}

Create a clear Mermaid flowchart showing AWS services and their relationships.

Example:
```mermaid
flowchart TD
    User["Users"] --> CF["CloudFront"]
    CF --> S3["S3 Static Website"]
    CF --> ALB["Application Load Balancer"]
    
    subgraph "Application Tier"
        ALB --> ECS["ECS Fargate"]
    end
    
    subgraph "Data Tier"
        ECS --> RDS["RDS PostgreSQL"]
    end
```

Provide ONLY the Mermaid code, no explanations."""
        
        elif prompt_name == "mermaid_flowchart":
            return """Create a detailed Mermaid flowchart for: {description}

Use flowchart TD format with clear labels and logical groupings.
Provide ONLY the Mermaid code."""
        
        elif prompt_name == "mermaid_fix":
            return """Fix this Mermaid code: {code}

Error: {error}

Provide ONLY the corrected Mermaid code."""
        
        else:
            return """Generate a complete Draw.io XML diagram for: {description}

Create a valid mxfile XML structure with AWS architecture components.

Requirements:
- Start with <?xml version="1.0" encoding="UTF-8"?>
- Use <mxfile> as root element
- Include <diagram> and <mxGraphModel> elements
- Add AWS service shapes with proper positioning
- End with </mxfile>
- Keep it simple and complete

Example structure:
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram name="AWS Architecture">
    <mxGraphModel dx="800" dy="600">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Service Name" style="shape=rectangle" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

Provide ONLY the complete XML, no explanations."""
