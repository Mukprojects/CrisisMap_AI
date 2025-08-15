"""
CrisisMap AI - Advanced Crisis Monitoring and Detection Platform.

A comprehensive AI-powered platform for monitoring global crises and natural disasters,
providing real-time analysis, semantic search, and intelligent insights.
"""

__version__ = "1.0.0"
__author__ = "CrisisMap AI Team"
__email__ = "team@crisismap.ai"
__license__ = "MIT"
__url__ = "https://github.com/Mukprojects/CrisisMap_AI"

from crisismap_ai.config import (
    API_HOST,
    API_PORT,
    DB_NAME,
    MONGODB_URI,
    VECTOR_INDEX_NAME,
)

# Package metadata
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    "API_HOST",
    "API_PORT", 
    "DB_NAME",
    "MONGODB_URI",
    "VECTOR_INDEX_NAME",
] 