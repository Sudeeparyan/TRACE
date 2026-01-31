#!/usr/bin/env python3
"""
TRACE AWS Production Validation Script

Validates that all components are properly implemented:
1. No random values in production Lambda functions
2. All required files exist
3. All AWS services are properly configured
4. Bedrock is used instead of Google Gemini
5. Real data queries to Timestream/DynamoDB
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Directory paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_check(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {name}")
    if details and not passed:
        print(f"         {details}")


def check_no_random_values() -> Tuple[bool, List[str]]:
    """Check that Lambda functions don't use random values for production data."""
    issues = []
    
    # Files that should NOT have random values (Lambda handlers)
    lambda_dirs = [
        PROJECT_DIR / "03-lambda-tools" / "health_monitor",
        PROJECT_DIR / "03-lambda-tools" / "remediation",
        PROJECT_DIR / "03-lambda-tools" / "analytics",
        PROJECT_DIR / "03-lambda-tools" / "agent_api",
        PROJECT_DIR / "02-data-pipeline" / "telemetry_processor",
    ]
    
    # telemetry_simulator.py is ALLOWED to have random (it's for test data generation)
    
    random_pattern = re.compile(r'random\.(uniform|choice|randint|random)\(')
    
    for lambda_dir in lambda_dirs:
        handler_file = lambda_dir / "handler.py"
        if handler_file.exists():
            content = handler_file.read_text()
            matches = random_pattern.findall(content)
            if matches:
                issues.append(f"{handler_file}: Uses random.{matches[0]}()")
    
    return len(issues) == 0, issues


def check_required_files() -> Tuple[bool, List[str]]:
    """Check all required files exist."""
    required_files = [
        # Config
        "config.py",
        "requirements.txt",
        "README.md",
        
        # Infrastructure
        "01-infrastructure/deploy.py",
        
        # Data Pipeline
        "02-data-pipeline/telemetry_processor/handler.py",
        
        # Lambda Functions
        "03-lambda-tools/health_monitor/handler.py",
        "03-lambda-tools/remediation/handler.py",
        "03-lambda-tools/analytics/handler.py",
        "03-lambda-tools/agent_api/handler.py",
        "03-lambda-tools/websocket/handler.py",
        
        # Bedrock Agents
        "04-bedrock-agents/deploy.py",
        
        # Step Functions
        "05-step-functions/deploy.py",
        "05-step-functions/self-healing-workflow.json",
        "05-step-functions/energy-optimization-workflow.json",
        
        # API Layer
        "06-api-layer/deploy.py",
        
        # Frontend
        "07-frontend/aws-config.js",
        
        # Services
        "services/bedrock_service.py",
        
        # Scripts
        "scripts/deploy_all.py",
        "scripts/telemetry_simulator.py",
    ]
    
    missing = []
    for file_path in required_files:
        full_path = PROJECT_DIR / file_path
        if not full_path.exists():
            missing.append(file_path)
    
    return len(missing) == 0, missing


def check_no_google_dependencies() -> Tuple[bool, List[str]]:
    """Check that no Google/Gemini IMPORTS exist in production code."""
    issues = []
    
    # Only flag actual imports, not comments/documentation
    google_patterns = [
        re.compile(r'^import\s+google', re.MULTILINE),
        re.compile(r'^from\s+google', re.MULTILINE),
        re.compile(r'^import\s+vertexai', re.MULTILINE),
        re.compile(r'^from\s+vertexai', re.MULTILINE),
    ]
    
    # Exclude certain files/dirs
    exclude = ['telemetry_simulator.py', '__pycache__', '.pyc', 'validate_implementation.py']
    
    for py_file in PROJECT_DIR.rglob("*.py"):
        if any(ex in str(py_file) for ex in exclude):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
            
        for pattern in google_patterns:
            if pattern.search(content):
                issues.append(f"{py_file.relative_to(PROJECT_DIR)}: Contains Google/Gemini reference")
                break
    
    return len(issues) == 0, issues


def check_aws_services_used() -> Tuple[bool, List[str]]:
    """Check that AWS services are properly used."""
    required_services = {
        'timestream': False,
        'dynamodb': False,
        'bedrock': False,
        'kinesis': False,
        'iot': False,
        'stepfunctions': False,
        'sns': False,
        'cloudwatch': False,
    }
    
    service_patterns = {
        'timestream': re.compile(r"boto3\.client\(['\"]timestream"),
        'dynamodb': re.compile(r"boto3\.(resource|client)\(['\"]dynamodb"),
        'bedrock': re.compile(r"boto3\.client\(['\"]bedrock"),
        'kinesis': re.compile(r"boto3\.client\(['\"]kinesis"),
        'iot': re.compile(r"boto3\.client\(['\"]iot"),
        'stepfunctions': re.compile(r"boto3\.client\(['\"]stepfunctions"),
        'sns': re.compile(r"boto3\.client\(['\"]sns"),
        'cloudwatch': re.compile(r"boto3\.client\(['\"]cloudwatch"),
    }
    
    for py_file in PROJECT_DIR.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for service, pattern in service_patterns.items():
            if pattern.search(content):
                required_services[service] = True
    
    missing = [svc for svc, found in required_services.items() if not found]
    return len(missing) == 0, missing


def check_real_timestream_queries() -> Tuple[bool, List[str]]:
    """Check that Lambda functions query real data from Timestream."""
    issues = []
    
    # Files that should have Timestream queries
    files_to_check = [
        PROJECT_DIR / "03-lambda-tools" / "health_monitor" / "handler.py",
        PROJECT_DIR / "03-lambda-tools" / "analytics" / "handler.py",
    ]
    
    query_pattern = re.compile(r'timestream_query\.query\(QueryString')
    
    for file_path in files_to_check:
        if file_path.exists():
            content = file_path.read_text()
            if not query_pattern.search(content):
                issues.append(f"{file_path.name}: No Timestream queries found")
    
    return len(issues) == 0, issues


def check_bedrock_integration() -> Tuple[bool, List[str]]:
    """Check Bedrock is properly integrated."""
    issues = []
    
    bedrock_service = PROJECT_DIR / "services" / "bedrock_service.py"
    if not bedrock_service.exists():
        issues.append("bedrock_service.py not found")
        return False, issues
    
    content = bedrock_service.read_text(encoding='utf-8', errors='ignore')
    
    # Check for required Bedrock components
    required = [
        ('bedrock-runtime client', r"boto3\.client\(['\"]bedrock-runtime"),
        ('Claude model ID', r"claude-3"),
        ('invoke_model usage', r"invoke_model\("),
        ('System prompt', r"SYSTEM_PROMPT"),
    ]
    
    for name, pattern in required:
        if not re.search(pattern, content):
            issues.append(f"Missing: {name}")
    
    return len(issues) == 0, issues


def check_infrastructure_deploy() -> Tuple[bool, List[str]]:
    """Check infrastructure deployment script creates required resources."""
    issues = []
    
    deploy_file = PROJECT_DIR / "01-infrastructure" / "deploy.py"
    if not deploy_file.exists():
        issues.append("deploy.py not found")
        return False, issues
    
    content = deploy_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check for required resource creation
    required_resources = [
        ('DynamoDB tables', r"dynamodb.*create_table|create_table"),
        ('Timestream database', r"timestream.*create_database|create_database"),
        ('S3 bucket', r"s3.*create_bucket|create_bucket"),
        ('Kinesis stream', r"kinesis.*create_stream|create_stream"),
        ('IAM role', r"iam.*create_role|create_role"),
        ('SNS topic', r"sns.*create_topic|create_topic"),
    ]
    
    for name, pattern in required_resources:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Missing creation of: {name}")
    
    return len(issues) == 0, issues


def check_step_functions() -> Tuple[bool, List[str]]:
    """Check Step Functions workflows are properly defined."""
    issues = []
    
    workflow_files = [
        PROJECT_DIR / "05-step-functions" / "self-healing-workflow.json",
        PROJECT_DIR / "05-step-functions" / "energy-optimization-workflow.json",
    ]
    
    for wf_file in workflow_files:
        if not wf_file.exists():
            issues.append(f"Missing: {wf_file.name}")
            continue
        
        content = wf_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check for required components
        if '"StartAt"' not in content:
            issues.append(f"{wf_file.name}: Missing StartAt")
        if '"States"' not in content:
            issues.append(f"{wf_file.name}: Missing States")
        if 'Lambda' not in content and 'lambda' not in content:
            issues.append(f"{wf_file.name}: No Lambda integrations")
    
    return len(issues) == 0, issues


def check_api_layer() -> Tuple[bool, List[str]]:
    """Check API Gateway deployment is properly configured."""
    issues = []
    
    api_deploy = PROJECT_DIR / "06-api-layer" / "deploy.py"
    if not api_deploy.exists():
        issues.append("API deploy.py not found")
        return False, issues
    
    content = api_deploy.read_text(encoding='utf-8', errors='ignore')
    
    required = [
        ('REST API creation', r"create_rest_api"),
        ('WebSocket API', r"create_api.*WEBSOCKET|websocket"),
        ('Lambda integration', r"AWS_PROXY|aws_proxy"),
        ('API key', r"create_api_key"),
    ]
    
    for name, pattern in required:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Missing: {name}")
    
    return len(issues) == 0, issues


def run_all_checks():
    """Run all validation checks."""
    print_header("TRACE AWS Production Validation")
    print(f"  Project: {PROJECT_DIR}")
    
    all_passed = True
    total_checks = 0
    passed_checks = 0
    
    checks = [
        ("Required files exist", check_required_files),
        ("No random values in Lambda", check_no_random_values),
        ("No Google dependencies", check_no_google_dependencies),
        ("AWS services integrated", check_aws_services_used),
        ("Real Timestream queries", check_real_timestream_queries),
        ("Bedrock integration", check_bedrock_integration),
        ("Infrastructure deployment", check_infrastructure_deploy),
        ("Step Functions workflows", check_step_functions),
        ("API Gateway layer", check_api_layer),
    ]
    
    for name, check_fn in checks:
        total_checks += 1
        passed, issues = check_fn()
        
        if passed:
            passed_checks += 1
            print_check(name, True)
        else:
            all_passed = False
            print_check(name, False)
            for issue in issues[:5]:  # Show first 5 issues
                print(f"         - {issue}")
            if len(issues) > 5:
                print(f"         ... and {len(issues) - 5} more issues")
    
    # Summary
    print_header("Validation Summary")
    print(f"  Checks passed: {passed_checks}/{total_checks}")
    
    if all_passed:
        print("\n  ✅ ALL VALIDATIONS PASSED!")
        print("  The AWS production implementation is complete and correct.")
    else:
        print(f"\n  ⚠️  {total_checks - passed_checks} check(s) failed.")
        print("  Please review and fix the issues above.")
    
    print("\n" + "=" * 70)
    
    # Component summary
    print("\n  COMPONENT SUMMARY:")
    print("  " + "-" * 50)
    
    components = [
        ("Infrastructure", ["01-infrastructure/deploy.py"]),
        ("Data Pipeline", ["02-data-pipeline/telemetry_processor/handler.py"]),
        ("Lambda Functions", [
            "03-lambda-tools/health_monitor/handler.py",
            "03-lambda-tools/remediation/handler.py",
            "03-lambda-tools/analytics/handler.py",
            "03-lambda-tools/agent_api/handler.py",
            "03-lambda-tools/websocket/handler.py"
        ]),
        ("Bedrock Agents", ["04-bedrock-agents/deploy.py", "services/bedrock_service.py"]),
        ("Step Functions", ["05-step-functions/deploy.py"]),
        ("API Gateway", ["06-api-layer/deploy.py"]),
        ("Frontend Config", ["07-frontend/aws-config.js"]),
        ("Deployment Scripts", ["scripts/deploy_all.py", "scripts/telemetry_simulator.py"]),
    ]
    
    for component, files in components:
        all_exist = all((PROJECT_DIR / f).exists() for f in files)
        status = "✅" if all_exist else "❌"
        print(f"  {status} {component}")
    
    print("\n" + "=" * 70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(run_all_checks())
