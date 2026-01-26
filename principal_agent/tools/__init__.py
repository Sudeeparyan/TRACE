"""
TRACE Principal Agent Tools Package
"""

# Export RAG tools for file uploads
from .rag_file_processor import (
    process_uploaded_json,
    query_rag_data,
    get_rag_summary,
)

# Export legacy JSON tools for backward compatibility
from .json_data_processor import (
    add_json_data,
    analyze_json_data_with_llm,
    get_recommendations_from_json,
    compare_json_datasets,
)

__all__ = [
    # RAG tools (recommended for file uploads)
    "process_uploaded_json",
    "query_rag_data",
    "get_rag_summary",
    # Legacy tools (for file paths)
    "add_json_data",
    "analyze_json_data_with_llm",
    "get_recommendations_from_json",
    "compare_json_datasets",
]
