# ArchMCP Test Suite

## Comprehensive Test Suite

Run 30 tests across both modes to evaluate icon selection accuracy.

### Quick Start

```bash
cd /path/to/ArchMCP
./tests/run_comprehensive_test.sh
```

Or run directly:

```bash
cd /path/to/ArchMCP
source .venv/bin/activate
python tests/comprehensive_test.py
```

### What It Tests

**Keywords Mode (15 tests):**
- Single keywords: EC2, S3, Lambda, etc.
- Multiple keywords: RDS + DynamoDB, VPC + subnet, etc.
- Tests Bedrock's intelligent icon selection

**Description Mode (15 tests):**
- Simple architectures: web apps, APIs
- Complex architectures: microservices, data pipelines
- Specialized use cases: ML, IoT, disaster recovery
- Tests Bedrock's service extraction and semantic matching

### Output

Generates: `outputs/comprehensive_test_results.docx`

The Word document includes:
- Test input (keyword or description)
- Mode used
- Number of icons found
- List of icon names
- Images of the first 4 icons per test

### Test Cases

**Keywords:**
1. EC2
2. S3
3. Lambda
4. RDS, DynamoDB
5. VPC, subnet
6. CloudFront, Route53
7. ECS, EKS
8. API Gateway
9. SQS, SNS
10. CloudWatch
11. IAM, Cognito
12. ElastiCache
13. Kinesis
14. Step Functions
15. Glue, Athena

**Descriptions:**
1. Simple web application with EC2 and S3
2. Serverless API with Lambda, API Gateway, DynamoDB
3. Microservices with ECS and load balancer
4. Data pipeline with Kinesis and Lambda
5. ML workflow with SageMaker
6. Multi-tier app with EC2, RDS, ElastiCache
7. Event-driven with EventBridge, Lambda, SQS
8. Static website with S3 and CloudFront
9. Container orchestration with EKS
10. Real-time analytics with Kinesis and Redshift
11. Batch processing with AWS Batch
12. IoT solution with IoT Core and Lambda
13. Content delivery with CloudFront
14. Hybrid cloud with Direct Connect
15. Disaster recovery with S3 Glacier

### Analyzing Results

After running, review the Word document for:
- **Accuracy**: Are the selected icons relevant?
- **Completeness**: Are key services missing?
- **Ambiguity**: Are there too many/too few icons?
- **Consistency**: Similar inputs produce similar results?

### Configuration

Edit `config/bedrock_config.yaml` to adjust:
- `top_k_icons`: Number of icons per keyword (default: 3)
- `model_id`: Bedrock model to use
- `region`: AWS region

### Other Tests

- `test_icon_mapping.py`: Tests 20 specific scenarios with detailed analysis
- Run individual tests as needed
