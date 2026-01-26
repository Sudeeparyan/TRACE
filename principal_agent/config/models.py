"""
TRACE Multi-Model Configuration

Supports multiple LLM providers with both fast and reasoning models:
- Google: Gemini 2.0 Flash (fast), Gemini 1.5 Pro (reasoning)
- Anthropic: Claude Sonnet 4.5 (fast), Claude Opus 4.5 (reasoning)
- OpenAI: GPT-5 Mini (fast), GPT-5.2 (reasoning)
- DeepSeek: DeepSeek V3 (fast), DeepSeek Reasoning (reasoning)
"""

import os
from typing import Dict, Any, Optional
from enum import Enum


class ModelProvider(Enum):
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"


class ModelType(Enum):
    FAST = "fast"  # Quick responses, lower cost
    REASONING = "reasoning"  # Complex analysis, higher accuracy


# Model Configuration Registry
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Google Models
    "gemini-2.0-flash": {
        "provider": ModelProvider.GOOGLE,
        "type": ModelType.FAST,
        "model_id": "gemini-2.0-flash",
        "description": "Google Gemini 2.0 Flash - Fast inference for real-time operations",
        "max_tokens": 8192,
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "latency_ms": 200,
        "use_cases": ["monitoring", "quick_decisions", "data_streaming"],
    },
    "gemini-1.5-pro": {
        "provider": ModelProvider.GOOGLE,
        "type": ModelType.REASONING,
        "model_id": "gemini-1.5-pro",
        "description": "Google Gemini 1.5 Pro - Advanced reasoning for complex analysis",
        "max_tokens": 32768,
        "cost_per_1k_input": 0.00125,
        "cost_per_1k_output": 0.005,
        "latency_ms": 800,
        "use_cases": ["root_cause_analysis", "optimization_planning", "learning"],
    },
    # Anthropic Models
    "claude-sonnet-4.5": {
        "provider": ModelProvider.ANTHROPIC,
        "type": ModelType.FAST,
        "model_id": "us.anthropic.claude-sonnet-4-5-20251220-v1:0",
        "description": "Anthropic Claude Sonnet 4.5 - Balanced speed and capability",
        "max_tokens": 8192,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "latency_ms": 350,
        "use_cases": ["health_checks", "remediation", "dashboard_generation"],
    },
    "claude-opus-4.5": {
        "provider": ModelProvider.ANTHROPIC,
        "type": ModelType.REASONING,
        "model_id": "us.anthropic.claude-opus-4-5-20251220-v1:0",
        "description": "Anthropic Claude Opus 4.5 - Best-in-class reasoning",
        "max_tokens": 32768,
        "cost_per_1k_input": 0.015,
        "cost_per_1k_output": 0.075,
        "latency_ms": 1200,
        "use_cases": ["complex_diagnostics", "self_healing", "policy_decisions"],
    },
    # OpenAI Models
    "gpt-5-mini": {
        "provider": ModelProvider.OPENAI,
        "type": ModelType.FAST,
        "model_id": "gpt-5-mini",
        "description": "OpenAI GPT-5 Mini - Efficient and cost-effective",
        "max_tokens": 8192,
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "latency_ms": 180,
        "use_cases": ["telemetry_processing", "quick_alerts", "status_checks"],
    },
    "gpt-5.2": {
        "provider": ModelProvider.OPENAI,
        "type": ModelType.REASONING,
        "model_id": "gpt-5.2",
        "description": "OpenAI GPT-5.2 - Advanced multi-step reasoning",
        "max_tokens": 65536,
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.03,
        "latency_ms": 900,
        "use_cases": ["predictive_analytics", "capacity_planning", "anomaly_detection"],
    },
    # DeepSeek Models
    "deepseek-v3": {
        "provider": ModelProvider.DEEPSEEK,
        "type": ModelType.FAST,
        "model_id": "deepseek-chat",
        "description": "DeepSeek V3 - High-performance open model",
        "max_tokens": 8192,
        "cost_per_1k_input": 0.00014,
        "cost_per_1k_output": 0.00028,
        "latency_ms": 250,
        "use_cases": ["batch_processing", "data_analysis", "reporting"],
    },
    "deepseek-reasoning": {
        "provider": ModelProvider.DEEPSEEK,
        "type": ModelType.REASONING,
        "model_id": "deepseek-reasoner",
        "description": "DeepSeek Reasoning - Specialized chain-of-thought reasoning",
        "max_tokens": 65536,
        "cost_per_1k_input": 0.00055,
        "cost_per_1k_output": 0.00219,
        "latency_ms": 1500,
        "use_cases": [
            "mathematical_optimization",
            "complex_scheduling",
            "multi_agent_coordination",
        ],
    },
}

# Agent to Model Mapping (Default Configuration)
AGENT_MODEL_MAPPING = {
    # Principal Agent - Uses reasoning model for complex orchestration
    "principal_agent": {
        "primary": "claude-opus-4.5",
        "fallback": "gemini-1.5-pro",
        "fast_mode": "claude-sonnet-4.5",
    },
    # Regional Coordinator - Balanced between speed and reasoning
    "regional_coordinator": {
        "primary": "claude-sonnet-4.5",
        "fallback": "gemini-2.0-flash",
        "fast_mode": "gpt-5-mini",
    },
    # Edge Agents - Optimized for specific tasks
    "monitoring_agent": {
        "primary": "gemini-2.0-flash",  # Fast for real-time monitoring
        "fallback": "gpt-5-mini",
    },
    "prediction_agent": {
        "primary": "deepseek-reasoning",  # Complex forecasting
        "fallback": "gpt-5.2",
    },
    "decision_xapp_agent": {
        "primary": "claude-sonnet-4.5",  # Policy decisions
        "fallback": "gemini-1.5-pro",
    },
    "action_agent": {
        "primary": "gpt-5-mini",  # Quick action execution
        "fallback": "gemini-2.0-flash",
    },
    "learning_agent": {
        "primary": "deepseek-reasoning",  # Model training analysis
        "fallback": "claude-opus-4.5",
    },
}


def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model."""
    if model_name not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model: {model_name}. Available: {list(MODEL_REGISTRY.keys())}"
        )
    return MODEL_REGISTRY[model_name]


def get_agent_model(agent_name: str, mode: str = "primary") -> str:
    """Get the model ID for a specific agent."""
    if agent_name not in AGENT_MODEL_MAPPING:
        # Default to gemini-3-flash for unknown agents
        return "gemini-3-flash"

    mapping = AGENT_MODEL_MAPPING[agent_name]
    model_key = mapping.get(mode, mapping.get("primary", "gemini-3-flash"))
    return MODEL_REGISTRY[model_key]["model_id"]


def get_fast_model(provider: ModelProvider = ModelProvider.GOOGLE) -> str:
    """Get the fast model for a specific provider."""
    fast_models = {
        ModelProvider.GOOGLE: "gemini-3-flash",
        ModelProvider.ANTHROPIC: "claude-sonnet-4.5",
        ModelProvider.OPENAI: "gpt-5-mini",
        ModelProvider.DEEPSEEK: "deepseek-v3",
    }
    return fast_models.get(provider, "gemini-3-flash")


def get_reasoning_model(provider: ModelProvider = ModelProvider.ANTHROPIC) -> str:
    """Get the reasoning model for a specific provider."""
    reasoning_models = {
        ModelProvider.GOOGLE: "gemini-3-pro",
        ModelProvider.ANTHROPIC: "claude-opus-4.5",
        ModelProvider.OPENAI: "gpt-5.2",
        ModelProvider.DEEPSEEK: "deepseek-reasoning",
    }
    return reasoning_models.get(provider, "claude-opus-4.5")


def get_all_models() -> Dict[str, Dict[str, Any]]:
    """Get all available models."""
    return MODEL_REGISTRY


def print_model_summary():
    """Print a summary of all available models."""
    print("\n" + "=" * 80)
    print("TRACE Multi-Model Configuration")
    print("=" * 80)

    for provider in ModelProvider:
        print(f"\n📦 {provider.value.upper()}")
        print("-" * 40)
        for name, config in MODEL_REGISTRY.items():
            if config["provider"] == provider:
                model_type = (
                    "⚡ FAST" if config["type"] == ModelType.FAST else "🧠 REASONING"
                )
                print(f"  {model_type} {name}")
                print(f"      {config['description']}")
                print(
                    f"      Latency: ~{config['latency_ms']}ms | Max Tokens: {config['max_tokens']}"
                )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_model_summary()
