"""Knowledge graph and memory layer for SRE AI Agent platform.

This module provides:
- Neo4j-based service topology and relationship management
- Vector-based incident memory using LangChain
- Embedding service for semantic search
- Discovery indexer for automatic graph population

Architecture:
    - KnowledgeGraph: Neo4j service map and relationships
    - IncidentMemory: Vector store for incident history
    - EmbeddingService: Text embedding generation
    - DiscoveryIndexer: Automatic graph population from provider discovery
"""

from app.knowledge.embeddings import EmbeddingService
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.indexer import DiscoveryIndexer
from app.knowledge.memory import IncidentMemory
from app.knowledge.models import (
    IncidentNode,
    ResourceNode,
    ServiceNode,
    TeamNode,
    TopologyResult,
)

__all__ = [
    # Core services
    "KnowledgeGraph",
    "IncidentMemory",
    "EmbeddingService",
    "DiscoveryIndexer",
    # Models
    "ServiceNode",
    "ResourceNode",
    "IncidentNode",
    "TeamNode",
    "TopologyResult",
]
