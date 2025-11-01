"""
Quick Test Script to Verify 500 Error Fix

This script tests the key changes made to resolve the Google Gemini 500 error.
Run this before your demo to ensure everything is working correctly.
"""

import sys
from pathlib import Path


def test_agent_configuration():
    """Test 1: Verify agent is using the correct model"""
    print("=" * 60)
    print("TEST 1: Agent Configuration")
    print("=" * 60)

    try:
        from principal_agent.agent import principal_agent

        print(f"✅ Agent Name: {principal_agent.name}")
        print(f"✅ Model: {principal_agent.model}")
        print(f"✅ Number of Tools: {len(principal_agent.tools)}")
        print(f"✅ Instruction Length: {len(principal_agent.instruction)} chars")

        # Verify model is correct
        assert (
            principal_agent.model == "gemini-2.0-flash-exp"
        ), "Model should be gemini-2.0-flash-exp"

        # Verify instruction is reasonably short
        assert (
            len(principal_agent.instruction) < 1500
        ), "Instruction should be < 1500 chars"

        print("\n✅ TEST 1 PASSED: Agent configured correctly\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}\n")
        return False


def test_json_processor_functions():
    """Test 2: Verify JSON processor has new functions"""
    print("=" * 60)
    print("TEST 2: JSON Processor Functions")
    print("=" * 60)

    try:
        from principal_agent.tools.json_data_processor import (
            add_json_data,
            analyze_json_data_with_llm,
            get_recommendations_from_json,
            compare_json_datasets,
            _sample_data_intelligently,
            _extract_energy_findings,
            _extract_congestion_findings,
            _extract_health_findings,
        )

        print("✅ add_json_data")
        print("✅ analyze_json_data_with_llm")
        print("✅ get_recommendations_from_json")
        print("✅ compare_json_datasets")
        print("✅ _sample_data_intelligently (new)")
        print("✅ _extract_energy_findings (new)")
        print("✅ _extract_congestion_findings (new)")
        print("✅ _extract_health_findings (new)")

        print("\n✅ TEST 2 PASSED: All functions exist\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}\n")
        return False


def test_json_data_loading():
    """Test 3: Load actual JSON data"""
    print("=" * 60)
    print("TEST 3: JSON Data Loading")
    print("=" * 60)

    try:
        from principal_agent.tools.json_data_processor import add_json_data

        result = add_json_data("data/trace_reduced_20.json")

        print(f"Status: {result.get('status')}")
        print(f"Records: {result.get('num_records')}")
        print(f"Data Type: {result.get('data_type')}")
        print(f"File Path: {result.get('file_path')}")

        # Verify success
        assert result["status"] == "success", "Should load successfully"
        assert result["num_records"] == 20, "Should have 20 records"

        print("\n✅ TEST 3 PASSED: JSON data loads correctly\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}\n")
        return False


def test_data_sampling():
    """Test 4: Test intelligent data sampling"""
    print("=" * 60)
    print("TEST 4: Data Sampling")
    print("=" * 60)

    try:
        from principal_agent.tools.json_data_processor import (
            add_json_data,
            _sample_data_intelligently,
            _loaded_json_data,
        )

        # Load data first
        result = add_json_data("data/trace_reduced_20.json")
        assert result["status"] == "success", "Data should load"

        # Get the loaded data
        data = _loaded_json_data["data"]

        # Test sampling
        sampled = _sample_data_intelligently(data, max_records=10)

        print(f"Original records: {len(data)}")
        print(f"Sampled records: {len(sampled)}")
        print(f"Sampling working: {len(sampled) <= 10}")

        assert len(sampled) <= 10, "Should sample to max 10 records"

        print("\n✅ TEST 4 PASSED: Sampling works correctly\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}\n")
        return False


def test_analysis_function():
    """Test 5: Test analysis without calling API"""
    print("=" * 60)
    print("TEST 5: Analysis Function (Local)")
    print("=" * 60)

    try:
        from principal_agent.tools.json_data_processor import (
            add_json_data,
            _perform_analysis,
            _loaded_json_data,
        )

        # Load data
        result = add_json_data("data/trace_reduced_20.json")
        assert result["status"] == "success", "Data should load"

        data = _loaded_json_data["data"]

        # Run analysis (local, no API)
        analysis = _perform_analysis(data, "energy", ["recommendations"])

        print(f"Summary exists: {bool(analysis.get('summary'))}")
        print(f"Insights count: {len(analysis.get('insights', []))}")
        print(f"Recommendations count: {len(analysis.get('recommendations', []))}")
        print(f"Key findings count: {len(analysis.get('key_findings', []))}")

        # Verify structure
        assert "summary" in analysis, "Should have summary"
        assert "insights" in analysis, "Should have insights"
        assert "recommendations" in analysis, "Should have recommendations"

        print("\n✅ TEST 5 PASSED: Analysis function works\n")
        return True

    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}\n")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 60)
    print("TESTING TRACE SYSTEM - 500 ERROR FIX VERIFICATION")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Agent Configuration", test_agent_configuration()))
    results.append(("JSON Processor Functions", test_json_processor_functions()))
    results.append(("JSON Data Loading", test_json_data_loading()))
    results.append(("Data Sampling", test_data_sampling()))
    results.append(("Analysis Function", test_analysis_function()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SYSTEM READY FOR DEMO! 🎉\n")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - CHECK ERRORS ABOVE ⚠️\n")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
