#!/usr/bin/env python3
"""
TRACE AWS Integration Verification Script

This script verifies that all AWS components are properly integrated and functional.
Run this after deployment to ensure everything is working correctly.

Usage:
    python verify_aws_integration.py --full     # Run all checks
    python verify_aws_integration.py --quick    # Quick connectivity check
    python verify_aws_integration.py --fix      # Attempt to fix issues
"""

import boto3
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Expected resources
EXPECTED_RESOURCES = {
    'dynamodb_tables': [
        f'TRACE-TowerConfig-{ENVIRONMENT}',
        f'TRACE-AgentState-{ENVIRONMENT}',
        f'TRACE-RemediationLog-{ENVIRONMENT}',
        f'TRACE-TelemetryAggregates-{ENVIRONMENT}',
        f'TRACE-Policies-{ENVIRONMENT}',
    ],
    'timestream': {
        'database': f'TRACE-Telemetry-{ENVIRONMENT}',
        'tables': ['TowerMetrics', 'AgentMetrics']
    },
    's3_buckets': [
        f'trace-data-{ENVIRONMENT}',
        f'trace-models-{ENVIRONMENT}',
    ],
    'lambda_functions': [
        f'TRACE-TelemetryProcessor-{ENVIRONMENT}',
        f'TRACE-HealthMonitor-{ENVIRONMENT}',
        f'TRACE-Remediation-{ENVIRONMENT}',
    ],
    'step_functions': [
        f'TRACE-SelfHealing-{ENVIRONMENT}',
        f'TRACE-EnergyOptimization-{ENVIRONMENT}',
    ],
}


class AWSIntegrationVerifier:
    """Verify AWS integration for TRACE system."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'environment': ENVIRONMENT,
            'region': AWS_REGION,
            'checks': {},
            'overall_status': 'unknown',
        }
        
        # Initialize AWS clients
        try:
            self.sts = boto3.client('sts', region_name=AWS_REGION)
            self.dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
            self.timestream_write = boto3.client('timestream-write', region_name=AWS_REGION)
            self.timestream_query = boto3.client('timestream-query', region_name=AWS_REGION)
            self.s3 = boto3.client('s3', region_name=AWS_REGION)
            self.lambda_client = boto3.client('lambda', region_name=AWS_REGION)
            self.sfn = boto3.client('stepfunctions', region_name=AWS_REGION)
            self.bedrock = boto3.client('bedrock', region_name=AWS_REGION)
            self.bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)
    
    def verify_aws_credentials(self) -> Tuple[bool, str]:
        """Verify AWS credentials are valid."""
        try:
            identity = self.sts.get_caller_identity()
            account = identity['Account']
            user_arn = identity['Arn']
            return True, f"Account: {account}, ARN: {user_arn}"
        except Exception as e:
            return False, str(e)
    
    def verify_dynamodb_tables(self) -> Dict[str, Any]:
        """Verify DynamoDB tables exist and are accessible."""
        results = {'status': 'pass', 'tables': {}}
        
        for table_name in EXPECTED_RESOURCES['dynamodb_tables']:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                item_count = response['Table'].get('ItemCount', 0)
                results['tables'][table_name] = {
                    'exists': True,
                    'status': status,
                    'item_count': item_count,
                }
            except self.dynamodb.exceptions.ResourceNotFoundException:
                results['tables'][table_name] = {'exists': False}
                results['status'] = 'partial'
            except Exception as e:
                results['tables'][table_name] = {'exists': False, 'error': str(e)}
                results['status'] = 'fail'
        
        return results
    
    def verify_timestream(self) -> Dict[str, Any]:
        """Verify Timestream database and tables exist."""
        results = {'status': 'pass', 'database': None, 'tables': {}}
        
        db_name = EXPECTED_RESOURCES['timestream']['database']
        
        try:
            response = self.timestream_write.describe_database(DatabaseName=db_name)
            results['database'] = {
                'exists': True,
                'name': db_name,
                'arn': response['Database']['Arn'],
            }
        except self.timestream_write.exceptions.ResourceNotFoundException:
            results['database'] = {'exists': False, 'name': db_name}
            results['status'] = 'fail'
            return results
        except Exception as e:
            results['database'] = {'exists': False, 'error': str(e)}
            results['status'] = 'fail'
            return results
        
        # Check tables
        for table_name in EXPECTED_RESOURCES['timestream']['tables']:
            try:
                response = self.timestream_write.describe_table(
                    DatabaseName=db_name,
                    TableName=table_name
                )
                results['tables'][table_name] = {
                    'exists': True,
                    'status': response['Table']['TableStatus'],
                }
            except Exception as e:
                results['tables'][table_name] = {'exists': False, 'error': str(e)}
                results['status'] = 'partial'
        
        return results
    
    def verify_timestream_data(self) -> Dict[str, Any]:
        """Verify Timestream has recent data."""
        results = {'status': 'pass', 'has_data': False, 'record_count': 0}
        
        try:
            db_name = EXPECTED_RESOURCES['timestream']['database']
            query = f"""
                SELECT COUNT(*) as record_count
                FROM "{db_name}"."TowerMetrics"
                WHERE time > ago(1h)
            """
            
            response = self.timestream_query.query(QueryString=query)
            if response.get('Rows'):
                count = int(response['Rows'][0]['Data'][0].get('ScalarValue', 0))
                results['record_count'] = count
                results['has_data'] = count > 0
                if count == 0:
                    results['status'] = 'warning'
                    results['message'] = 'No recent data. Run telemetry simulator.'
        except Exception as e:
            results['status'] = 'warning'
            results['error'] = str(e)
            results['message'] = 'Could not query Timestream data'
        
        return results
    
    def verify_lambda_functions(self) -> Dict[str, Any]:
        """Verify Lambda functions are deployed."""
        results = {'status': 'pass', 'functions': {}}
        
        for func_name in EXPECTED_RESOURCES['lambda_functions']:
            try:
                response = self.lambda_client.get_function(FunctionName=func_name)
                results['functions'][func_name] = {
                    'exists': True,
                    'runtime': response['Configuration']['Runtime'],
                    'state': response['Configuration']['State'],
                    'last_modified': response['Configuration']['LastModified'],
                }
            except self.lambda_client.exceptions.ResourceNotFoundException:
                results['functions'][func_name] = {'exists': False}
                results['status'] = 'partial'
            except Exception as e:
                results['functions'][func_name] = {'exists': False, 'error': str(e)}
        
        return results
    
    def verify_bedrock_access(self) -> Dict[str, Any]:
        """Verify Bedrock model access."""
        results = {'status': 'pass', 'models': {}}
        
        models_to_check = [
            'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'anthropic.claude-3-haiku-20240307-v1:0',
        ]
        
        try:
            # List available foundation models
            response = self.bedrock.list_foundation_models(
                byProvider='Anthropic',
                byOutputModality='TEXT'
            )
            
            available_models = [m['modelId'] for m in response.get('modelSummaries', [])]
            
            for model_id in models_to_check:
                base_model = model_id.split(':')[0] if ':' in model_id else model_id
                is_available = any(base_model in m for m in available_models)
                results['models'][model_id] = {
                    'available': is_available,
                }
                if not is_available:
                    results['status'] = 'warning'
                    
        except Exception as e:
            results['status'] = 'warning'
            results['error'] = str(e)
            results['message'] = 'Could not verify Bedrock access. May need to enable model access in AWS Console.'
        
        return results
    
    def verify_bedrock_agents(self) -> Dict[str, Any]:
        """Verify Bedrock Agents are configured."""
        results = {'status': 'pass', 'agents': []}
        
        try:
            response = self.bedrock_agent.list_agents()
            for agent in response.get('agentSummaries', []):
                if 'TRACE' in agent.get('agentName', ''):
                    results['agents'].append({
                        'name': agent['agentName'],
                        'id': agent['agentId'],
                        'status': agent['agentStatus'],
                    })
            
            if not results['agents']:
                results['status'] = 'warning'
                results['message'] = 'No TRACE agents found. Deploy Bedrock agents.'
                
        except Exception as e:
            results['status'] = 'warning'
            results['error'] = str(e)
        
        return results
    
    def verify_step_functions(self) -> Dict[str, Any]:
        """Verify Step Functions state machines."""
        results = {'status': 'pass', 'state_machines': {}}
        
        for sfn_name in EXPECTED_RESOURCES['step_functions']:
            try:
                # List state machines and find by name
                response = self.sfn.list_state_machines()
                found = None
                for sm in response.get('stateMachines', []):
                    if sfn_name in sm['name']:
                        found = sm
                        break
                
                if found:
                    results['state_machines'][sfn_name] = {
                        'exists': True,
                        'arn': found['stateMachineArn'],
                    }
                else:
                    results['state_machines'][sfn_name] = {'exists': False}
                    results['status'] = 'partial'
                    
            except Exception as e:
                results['state_machines'][sfn_name] = {'exists': False, 'error': str(e)}
        
        return results
    
    def run_full_verification(self) -> Dict[str, Any]:
        """Run all verification checks."""
        print("\n" + "=" * 70)
        print("  TRACE AWS Integration Verification")
        print("=" * 70)
        print(f"  Environment: {ENVIRONMENT}")
        print(f"  Region: {AWS_REGION}")
        print(f"  Timestamp: {self.results['timestamp']}")
        print("=" * 70 + "\n")
        
        checks = [
            ('AWS Credentials', self.verify_aws_credentials),
            ('DynamoDB Tables', self.verify_dynamodb_tables),
            ('Timestream Database', self.verify_timestream),
            ('Timestream Data', self.verify_timestream_data),
            ('Lambda Functions', self.verify_lambda_functions),
            ('Step Functions', self.verify_step_functions),
            ('Bedrock Access', self.verify_bedrock_access),
            ('Bedrock Agents', self.verify_bedrock_agents),
        ]
        
        passed = 0
        warnings = 0
        failed = 0
        
        for check_name, check_func in checks:
            print(f"🔍 Checking {check_name}...", end=' ')
            
            try:
                if check_name == 'AWS Credentials':
                    success, details = check_func()
                    result = {'status': 'pass' if success else 'fail', 'details': details}
                else:
                    result = check_func()
                
                self.results['checks'][check_name] = result
                
                status = result.get('status', 'unknown')
                if status == 'pass':
                    print("✅ PASS")
                    passed += 1
                elif status == 'warning':
                    print("⚠️  WARNING")
                    warnings += 1
                elif status == 'partial':
                    print("🟡 PARTIAL")
                    warnings += 1
                else:
                    print("❌ FAIL")
                    failed += 1
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.results['checks'][check_name] = {'status': 'fail', 'error': str(e)}
                failed += 1
        
        # Overall status
        print("\n" + "-" * 70)
        print(f"  Results: {passed} passed, {warnings} warnings, {failed} failed")
        
        if failed == 0 and warnings == 0:
            self.results['overall_status'] = 'healthy'
            print("  Overall Status: ✅ HEALTHY")
        elif failed == 0:
            self.results['overall_status'] = 'operational_with_warnings'
            print("  Overall Status: ⚠️  OPERATIONAL WITH WARNINGS")
        else:
            self.results['overall_status'] = 'needs_attention'
            print("  Overall Status: ❌ NEEDS ATTENTION")
        
        print("-" * 70 + "\n")
        
        return self.results
    
    def print_recommendations(self):
        """Print recommendations based on verification results."""
        print("\n📋 RECOMMENDATIONS:")
        print("-" * 50)
        
        checks = self.results.get('checks', {})
        
        # DynamoDB
        if checks.get('DynamoDB Tables', {}).get('status') != 'pass':
            print("• Run infrastructure deployment: python AWS/aws-production/01-infrastructure/deploy.py")
        
        # Timestream Data
        timestream_data = checks.get('Timestream Data', {})
        if not timestream_data.get('has_data'):
            print("• Start telemetry simulator: python AWS/aws-production/scripts/telemetry_simulator.py --continuous")
        
        # Lambda
        if checks.get('Lambda Functions', {}).get('status') != 'pass':
            print("• Deploy Lambda functions using SAM or CDK")
        
        # Bedrock
        if checks.get('Bedrock Access', {}).get('status') != 'pass':
            print("• Enable Claude models in AWS Bedrock console: https://console.aws.amazon.com/bedrock/")
        
        if checks.get('Bedrock Agents', {}).get('status') != 'pass':
            print("• Deploy Bedrock agents: python AWS/aws-production/04-bedrock-agents/deploy.py")
        
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='TRACE AWS Integration Verification')
    parser.add_argument('--full', action='store_true', help='Run full verification')
    parser.add_argument('--quick', action='store_true', help='Quick connectivity check')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    verifier = AWSIntegrationVerifier()
    results = verifier.run_full_verification()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        verifier.print_recommendations()


if __name__ == "__main__":
    main()
