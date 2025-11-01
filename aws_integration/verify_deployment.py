"""
TRACE AWS Integration - Deployment Verification Script

This script verifies that all components are properly deployed and configured.
Run this after deployment to ensure everything is working.
"""

import boto3
import json
import os
from datetime import datetime


class DeploymentVerifier:
    """Verify TRACE AWS deployment."""

    def __init__(self):
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "warnings": [],
            "errors": [],
        }

    def add_result(self, category, name, status, message, details=None):
        """Add a verification result."""
        result = {
            "category": category,
            "name": name,
            "status": status,  # 'pass', 'fail', 'warning'
            "message": message,
        }
        if details:
            result["details"] = details
        self.results["checks"].append(result)

        # Print immediately
        icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
        print(f"{icon} [{category}] {name}: {message}")

    def verify_aws_credentials(self):
        """Verify AWS credentials are configured."""
        print("\n" + "=" * 80)
        print("1. AWS Credentials Verification")
        print("=" * 80)

        try:
            sts = boto3.client("sts")
            identity = sts.get_caller_identity()

            self.add_result(
                "AWS Credentials",
                "IAM Identity",
                "pass",
                f"Authenticated as {identity['Arn']}",
                identity,
            )
            return True
        except Exception as e:
            self.add_result(
                "AWS Credentials",
                "IAM Identity",
                "fail",
                f"Failed to authenticate: {str(e)}",
            )
            return False

    def verify_iam_roles(self):
        """Verify IAM roles exist."""
        print("\n" + "=" * 80)
        print("2. IAM Roles Verification")
        print("=" * 80)

        iam = boto3.client("iam")
        roles_to_check = [
            "agentcore-principal_tools-role",
            "agentcore-regional_coordinator-role",
        ]

        for role_name in roles_to_check:
            try:
                response = iam.get_role(RoleName=role_name)
                self.add_result(
                    "IAM Roles",
                    role_name,
                    "pass",
                    "Role exists",
                    {"Arn": response["Role"]["Arn"]},
                )
            except iam.exceptions.NoSuchEntityException:
                self.add_result("IAM Roles", role_name, "fail", "Role does not exist")
            except Exception as e:
                self.add_result(
                    "IAM Roles", role_name, "fail", f"Error checking role: {str(e)}"
                )

    def verify_cognito_pools(self):
        """Verify Cognito user pools exist."""
        print("\n" + "=" * 80)
        print("3. Cognito User Pools Verification")
        print("=" * 80)

        cognito = boto3.client("cognito-idp", region_name=self.region)

        try:
            response = cognito.list_user_pools(MaxResults=20)
            mcp_pools = [
                p for p in response["UserPools"] if "MCPServerPool" in p["Name"]
            ]

            if mcp_pools:
                for pool in mcp_pools:
                    self.add_result(
                        "Cognito",
                        "User Pool",
                        "pass",
                        f"Pool {pool['Name']} exists",
                        {"Id": pool["Id"]},
                    )
            else:
                self.add_result(
                    "Cognito", "User Pool", "warning", "No MCP user pools found"
                )
        except Exception as e:
            self.add_result(
                "Cognito", "User Pool", "fail", f"Error checking pools: {str(e)}"
            )

    def verify_ssm_parameters(self):
        """Verify SSM parameters exist."""
        print("\n" + "=" * 80)
        print("4. SSM Parameters Verification")
        print("=" * 80)

        ssm = boto3.client("ssm", region_name=self.region)

        required_params = [
            "/trace/principal_tools/agent_arn",
            "/trace/principal_tools/client_id",
            "/trace/regional_coordinator/agent_arn",
            "/trace/regional_coordinator/client_id",
        ]

        for param_name in required_params:
            try:
                response = ssm.get_parameter(Name=param_name)
                self.add_result(
                    "SSM Parameters",
                    param_name,
                    "pass",
                    "Parameter exists",
                    {"Value": response["Parameter"]["Value"][:50] + "..."},
                )
            except ssm.exceptions.ParameterNotFound:
                self.add_result(
                    "SSM Parameters", param_name, "fail", "Parameter not found"
                )
            except Exception as e:
                self.add_result(
                    "SSM Parameters",
                    param_name,
                    "fail",
                    f"Error checking parameter: {str(e)}",
                )

    def verify_secrets_manager(self):
        """Verify Secrets Manager secrets exist."""
        print("\n" + "=" * 80)
        print("5. Secrets Manager Verification")
        print("=" * 80)

        secrets = boto3.client("secretsmanager", region_name=self.region)

        required_secrets = [
            "/trace/principal_tools/cognito/credentials",
            "/trace/regional_coordinator/cognito/credentials",
        ]

        for secret_name in required_secrets:
            try:
                response = secrets.describe_secret(SecretId=secret_name)
                self.add_result(
                    "Secrets Manager",
                    secret_name,
                    "pass",
                    "Secret exists",
                    {"ARN": response["ARN"]},
                )
            except secrets.exceptions.ResourceNotFoundException:
                self.add_result(
                    "Secrets Manager", secret_name, "fail", "Secret not found"
                )
            except Exception as e:
                self.add_result(
                    "Secrets Manager",
                    secret_name,
                    "fail",
                    f"Error checking secret: {str(e)}",
                )

    def verify_local_files(self):
        """Verify local files exist."""
        print("\n" + "=" * 80)
        print("6. Local Files Verification")
        print("=" * 80)

        required_files = [
            "principal_agent_aws.py",
            "requirements.txt",
            ".env",
            "mcp_servers/principal_tools_server.py",
            "mcp_servers/regional_coordinator_server.py",
            "deployment/deploy_mcp_servers.py",
            "tests/test_mcp_connection.py",
        ]

        for file_path in required_files:
            if os.path.exists(file_path):
                self.add_result("Local Files", file_path, "pass", "File exists")
            else:
                self.add_result("Local Files", file_path, "fail", "File not found")

    def verify_python_environment(self):
        """Verify Python environment."""
        print("\n" + "=" * 80)
        print("7. Python Environment Verification")
        print("=" * 80)

        # Check Python version
        import sys

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        if sys.version_info.major >= 3 and sys.version_info.minor >= 9:
            self.add_result(
                "Python", "Version", "pass", f"Python {python_version} (>=3.9 required)"
            )
        else:
            self.add_result(
                "Python", "Version", "fail", f"Python {python_version} (>=3.9 required)"
            )

        # Check key packages
        packages = ["boto3", "mcp", "strands", "fastmcp"]

        for package in packages:
            try:
                __import__(package)
                self.add_result(
                    "Python Packages", package, "pass", f"{package} installed"
                )
            except ImportError:
                self.add_result(
                    "Python Packages",
                    package,
                    "warning",
                    f"{package} not installed (may be optional)",
                )

    def generate_report(self):
        """Generate final report."""
        print("\n" + "=" * 80)
        print("VERIFICATION REPORT")
        print("=" * 80)

        passed = sum(1 for c in self.results["checks"] if c["status"] == "pass")
        failed = sum(1 for c in self.results["checks"] if c["status"] == "fail")
        warnings = sum(1 for c in self.results["checks"] if c["status"] == "warning")
        total = len(self.results["checks"])

        print(f"\nTotal Checks: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if failed == 0:
            print("\n🎉 All critical checks passed! Deployment is ready.")
            print("\nNext steps:")
            print("  1. Run: python tests/test_mcp_connection.py")
            print("  2. Run: python principal_agent_aws.py")
        else:
            print("\n⚠️  Some checks failed. Please review the errors above.")
            print("\nFailed checks:")
            for check in self.results["checks"]:
                if check["status"] == "fail":
                    print(
                        f"  - [{check['category']}] {check['name']}: {check['message']}"
                    )

        # Save report
        report_file = "deployment_verification_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")

    def run_all_verifications(self):
        """Run all verification checks."""
        print("\n" + "=" * 80)
        print("TRACE AWS Integration - Deployment Verification")
        print("=" * 80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Region: {self.region}")

        # Run all checks
        if not self.verify_aws_credentials():
            print("\n❌ AWS credentials check failed. Cannot continue.")
            return

        self.verify_iam_roles()
        self.verify_cognito_pools()
        self.verify_ssm_parameters()
        self.verify_secrets_manager()
        self.verify_local_files()
        self.verify_python_environment()

        # Generate report
        self.generate_report()


def main():
    """Main entry point."""
    verifier = DeploymentVerifier()
    verifier.run_all_verifications()


if __name__ == "__main__":
    main()
