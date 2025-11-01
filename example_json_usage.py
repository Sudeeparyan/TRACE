"""
Example Script: Using JSON Data Processor with TRACE

This script demonstrates how to use the JSON data processing tools
to load network data, analyze it with LLM, and get recommendations.
"""

import sys
from pathlib import Path

# Add parent directory to path to import TRACE modules
trace_root = Path(__file__).parent
sys.path.insert(0, str(trace_root))

from principal_agent.tools.json_data_processor import (
    add_json_data,
    analyze_json_data_with_llm,
    get_recommendations_from_json,
    compare_json_datasets,
)


def example_1_basic_loading():
    """Example 1: Load and validate a JSON file"""
    print("=" * 80)
    print("EXAMPLE 1: Loading JSON Data")
    print("=" * 80)

    # Load the sample data
    result = add_json_data("data/trace_reduced_20.json")

    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"\nNumber of records: {result.get('num_records', 0)}")
    print(f"Data type: {result.get('data_type', 'unknown')}")

    if "fields" in result:
        print(f"\nAvailable fields ({len(result['fields'])}):")
        for field in result["fields"][:10]:  # Show first 10 fields
            print(f"  - {field}")
        if len(result["fields"]) > 10:
            print(f"  ... and {len(result['fields']) - 10} more")

    if "sample_record" in result:
        print("\nSample record:")
        sample = result["sample_record"]
        for key, value in list(sample.items())[:5]:  # Show first 5 fields
            print(f"  {key}: {value}")
        print("  ...")


def example_2_comprehensive_analysis():
    """Example 2: Comprehensive data analysis"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Comprehensive Analysis")
    print("=" * 80)

    # First load the data
    add_json_data("data/trace_reduced_20.json")

    # Perform comprehensive analysis
    result = analyze_json_data_with_llm("comprehensive")

    print(f"\nStatus: {result['status']}")
    print(f"Analysis type: {result['analysis_type']}")
    print(f"Records analyzed: {result['num_records_analyzed']}")

    # Display summary
    analysis = result["analysis"]
    summary = analysis["summary"]
    print("\n--- Summary ---")
    print(f"Total records: {summary['total_records']}")
    print(f"Unique towers: {summary['unique_towers']}")
    print(f"Unique regions: {summary['unique_regions']}")
    print(
        f"Time span: {summary['time_span']['start']} to {summary['time_span']['end']}"
    )

    # Display insights
    print("\n--- Key Insights ---")
    for i, insight in enumerate(analysis["insights"][:5], 1):
        print(f"{i}. {insight}")

    # Display recommendations
    print("\n--- Recommendations ---")
    for i, rec in enumerate(analysis["recommendations"][:3], 1):
        print(f"\n{i}. [{rec['priority'].upper()}] {rec['title']}")
        print(f"   Category: {rec['category']}")
        print(f"   Expected Impact: {rec['expected_impact']}")
        print(f"   Action Items:")
        for action in rec["action_items"]:
            print(f"     - {action}")


def example_3_energy_focused():
    """Example 3: Energy-focused analysis"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Energy Optimization Analysis")
    print("=" * 80)

    # Load data
    add_json_data("data/trace_reduced_20.json")

    # Energy-focused analysis
    result = analyze_json_data_with_llm("energy", ["towers", "recommendations"])

    analysis = result["analysis"]

    print("\n--- Energy Insights ---")
    for insight in analysis["insights"]:
        print(f"💡 {insight}")

    print("\n--- Energy Recommendations ---")
    for rec in analysis["recommendations"]:
        if rec["category"] == "energy_optimization":
            print(f"\n🔋 {rec['title']}")
            print(f"   Priority: {rec['priority'].upper()}")
            print(f"   Impact: {rec['expected_impact']}")
            if "affected_towers" in rec:
                print(f"   Towers: {', '.join(rec['affected_towers'])}")


def example_4_specific_recommendations():
    """Example 4: Get specific tower recommendations"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Specific Tower Recommendations")
    print("=" * 80)

    # Load data
    add_json_data("data/trace_reduced_20.json")

    # Get recommendations for specific tower
    tower_id = "TX005"
    result = get_recommendations_from_json(tower_id=tower_id, metric_focus="all")

    print(f"\nAnalyzing tower: {tower_id}")
    print(f"Records analyzed: {result['records_analyzed']}")

    print("\n--- Recommendations ---")
    for i, rec in enumerate(result["recommendations"], 1):
        print(f"\n{i}. [{rec['priority'].upper()}] {rec['title']}")
        print(f"   {rec['description']}")
        print(f"   Expected Impact: {rec['expected_impact']}")


def example_5_health_analysis():
    """Example 5: Network health analysis"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Network Health Analysis")
    print("=" * 80)

    # Load data
    add_json_data("data/trace_reduced_20.json")

    # Health analysis
    result = analyze_json_data_with_llm("health", ["errors", "performance"])

    analysis = result["analysis"]

    print("\n--- Health Status ---")
    summary = analysis["summary"]
    print(
        f"Monitoring {summary['unique_towers']} towers across {summary['unique_regions']} regions"
    )

    print("\n--- Health Insights ---")
    for insight in analysis["insights"]:
        if any(word in insight for word in ["quality", "latency", "packet", "error"]):
            print(f"⚠️  {insight}")


def example_6_comparison():
    """Example 6: Compare two datasets"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Dataset Comparison")
    print("=" * 80)

    # Compare two datasets
    result = compare_json_datasets(
        "data/trace_reduced_20.json", "data/trace_llm_20.json"
    )

    if result["status"] == "success":
        print("\n--- Comparison Results ---")
        print(f"Dataset 1: {result['dataset1']['records']} records")
        print(f"Dataset 2: {result['dataset2']['records']} records")
        print(f"Size change: {result['comparison']['size_change']}")

        print("\n--- Metric Changes ---")
        for metric, changes in result["comparison"]["metrics"].items():
            print(f"\n{metric}:")
            print(f"  Dataset 1 average: {changes['dataset1_avg']}")
            print(f"  Dataset 2 average: {changes['dataset2_avg']}")
            print(f"  Change: {changes['change_percent']:+.2f}%")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "TRACE JSON Data Processor - Examples" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # Run each example
        example_1_basic_loading()
        example_2_comprehensive_analysis()
        example_3_energy_focused()
        example_4_specific_recommendations()
        example_5_health_analysis()
        example_6_comparison()

        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Try with your own JSON data")
        print("  2. Use these tools in the TRACE web interface (adk web)")
        print("  3. Customize analysis types and focus areas")
        print("  4. Integrate into your workflows")
        print("\nFor more information, see JSON_DATA_GUIDE.md")
        print()

    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        print("Make sure you're running from the TRACE root directory")
        print("and that the data files exist in the data/ folder")


if __name__ == "__main__":
    main()
