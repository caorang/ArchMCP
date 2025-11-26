#!/usr/bin/env python3
"""Quick test for draw.io generator"""
import sys
from pathlib import Path
import boto3
import json

# Add ArchMCP-Common to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'ArchMCP-Common'))

from drawio_generator import DrawioGenerator

class LLMClient:
    def __init__(self, region_name="us-east-1", model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"):
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = model_id
    
    def generate_response(self, prompt, max_tokens=4000):
        """Generate response from Bedrock"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

# Test
llm_client = LLMClient()
generator = DrawioGenerator(llm_client)

description = "A simple web application with EC2 instances behind a load balancer, storing data in S3"

print("🧪 Testing Draw.io generation...")
print(f"Description: {description}\n")

result = generator.generate_drawio(description)

if result.get("success"):
    print(f"✅ Success!")
    print(f"📁 File: {result['file_path']}")
    print(f"📊 Services: {result.get('services_count', 'N/A')}")
else:
    print(f"❌ Failed: {result.get('error')}")
