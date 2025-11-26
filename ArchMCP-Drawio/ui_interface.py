#!/usr/bin/env python3
"""
Web UI for Draw.io generation with preview
"""
import sys
from pathlib import Path
import boto3
import json

from flask import Flask, render_template, request, jsonify, send_file
from drawio_generator import DrawioGenerator
import yaml

app = Flask(__name__)

# Load config
config_path = Path(__file__).parent.parent / 'ArchMCP-Common' / 'config' / 'bedrock_config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# LLM Client for draw.io generator
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

llm_client = LLMClient(
    region_name=config['bedrock']['region'],
    model_id=config['bedrock']['model_id']
)
drawio_gen = DrawioGenerator(llm_client)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    input_text = data.get('input', '')
    mode = data.get('mode', 'description')
    
    debug_info = {'mode': mode, 'input': input_text}
    
    try:
        # For both modes, we'll pass to draw.io generator
        # The generator handles service extraction internally
        result = drawio_gen.generate_drawio(input_text)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'file_path': result['file_path'],
                'file_name': Path(result['file_path']).name,
                'services_count': result.get('services_count', 'N/A'),
                'debug': debug_info
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'debug': debug_info
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'debug': debug_info
        }), 500

@app.route('/download/<filename>')
def download(filename):
    output_path = Path(__file__).parent / 'outputs' / filename
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    # Create HTML template
    template_dir = Path(__file__).parent / 'templates'
    template_dir.mkdir(exist_ok=True)
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>ArchMCP Draw.io Generator</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
        h1 { color: #232F3E; }
        .mode-selector { margin: 20px 0; }
        .mode-btn { padding: 10px 20px; margin-right: 10px; cursor: pointer; border: 2px solid #FF9900; background: white; }
        .mode-btn.active { background: #FF9900; color: white; }
        textarea { width: 100%; height: 150px; padding: 10px; font-size: 14px; }
        button { padding: 12px 30px; background: #232F3E; color: white; border: none; cursor: pointer; font-size: 16px; }
        button:hover { background: #FF9900; }
        .result { margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; }
        .success { color: #00AA00; }
        .error { color: #CC0000; }
        .loading { display: none; margin: 20px 0; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #FF9900; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>🎨 ArchMCP Draw.io Generator</h1>
    
    <div class="mode-selector">
        <button class="mode-btn active" onclick="setMode('description')">Description Mode</button>
        <button class="mode-btn" onclick="setMode('keywords')">Keywords Mode</button>
    </div>
    
    <div id="description-input">
        <h3>Enter Architecture Description:</h3>
        <textarea id="input-text" placeholder="Example: A serverless API using Lambda and API Gateway with DynamoDB database"></textarea>
    </div>
    
    <div id="keywords-input" style="display:none;">
        <h3>Enter AWS Service Keywords (comma-separated):</h3>
        <textarea id="keywords-text" placeholder="Example: Lambda, API Gateway, DynamoDB"></textarea>
    </div>
    
    <button onclick="generate()">Generate Draw.io Diagram</button>
    
    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p>Generating diagram with AI...</p>
    </div>
    
    <div class="result" id="result" style="display:none;"></div>
    
    <script>
        let currentMode = 'description';
        
        function setMode(mode) {
            currentMode = mode;
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            if (mode === 'description') {
                document.getElementById('description-input').style.display = 'block';
                document.getElementById('keywords-input').style.display = 'none';
            } else {
                document.getElementById('description-input').style.display = 'none';
                document.getElementById('keywords-input').style.display = 'block';
            }
        }
        
        async function generate() {
            const input = currentMode === 'description' 
                ? document.getElementById('input-text').value 
                : document.getElementById('keywords-text').value;
            
            if (!input.trim()) {
                alert('Please enter some text');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input: input, mode: currentMode})
                });
                
                const data = await response.json();
                document.getElementById('loading').style.display = 'none';
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                
                if (data.success) {
                    resultDiv.innerHTML = `
                        <h3 class="success">✅ Diagram Generated Successfully!</h3>
                        <p><strong>File:</strong> ${data.file_name}</p>
                        <p><strong>Services:</strong> ${data.services_count}</p>
                        <p><a href="/download/${data.file_name}" download>📥 Download Draw.io File</a></p>
                        <p><small>Open with <a href="https://app.diagrams.net" target="_blank">draw.io</a></small></p>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <h3 class="error">❌ Generation Failed</h3>
                        <p>${data.error}</p>
                    `;
                }
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').innerHTML = `
                    <h3 class="error">❌ Error</h3>
                    <p>${error.message}</p>
                `;
            }
        }
    </script>
</body>
</html>'''
    
    with open(template_dir / 'index.html', 'w') as f:
        f.write(html)
    
    print("🌐 Starting UI at http://localhost:5001")
    app.run(debug=True, port=5001)
