"""LangChain vector store for incident history."""

import os
from typing import List, Optional

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Pinecone as PineconeVectorStore

from app.core.logging import get_logger
from app.knowledge.embeddings import EmbeddingService
from app.knowledge.models import IncidentSummary, SimilarIncident

logger = get_logger(__name__)


class IncidentMemory:
    """Vector store for incident history using LangChain.

    Stores past incident summaries as embeddings for similarity search.
    Supports FAISS (local) or Pinecone (production) backends.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        backend: str = "faiss",
        index_path: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_environment: Optional[str] = None,
        pinecone_index_name: str = "sre-incidents",
    ) -> None:
        """Initialize incident memory.

        Args:
            embedding_service: Embedding service for generating vectors
            backend: Vector store backend ("faiss" or "pinecone")
            index_path: Path to FAISS index (for FAISS backend)
            pinecone_api_key: Pinecone API key (for Pinecone backend)
            pinecone_environment: Pinecone environment (for Pinecone backend)
            pinecone_index_name: Pinecone index name
        """
        self.embedding_service = embedding_service
        self.backend = backend
        self.index_path = index_path or "./data/faiss_index"
        self.pinecone_api_key = pinecone_api_key
        self.pinecone_environment = pinecone_environment
        self.pinecone_index_name = pinecone_index_name

        self._vectorstore = None

        logger.info(
            "incident_memory_initialized",
            backend=backend,
            index_path=self.index_path if backend == "faiss" else None,
        )

    async def initialize(self) -> None:
        """Initialize the vector store."""
        if self.backend == "faiss":
            await self._initialize_faiss()
        elif self.backend == "pinecone":
            await self._initialize_pinecone()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    async def _initialize_faiss(self) -> None:
        """Initialize FAISS vector store."""
        try:
            # Check if index exists
            if os.path.exists(self.index_path):
                # Load existing index
                self._vectorstore = FAISS.load_local(
                    self.index_path,
                    self.embedding_service.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("faiss_index_loaded", path=self.index_path)
            else:
                # Create new index with empty documents
                # We'll add documents later
                self._vectorstore = None
                logger.info("faiss_index_will_be_created_on_first_store")

        except Exception as e:
            logger.error("faiss_initialization_failed", error=str(e))
            raise

    async def _initialize_pinecone(self) -> None:
        """Initialize Pinecone vector store."""
        try:
            import pinecone

            # Initialize Pinecone
            pinecone.init(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_environment,
            )

            # Check if index exists
            if self.pinecone_index_name not in pinecone.list_indexes():
                # Create index
                pinecone.create_index(
                    name=self.pinecone_index_name,
                    dimension=self.embedding_service.get_embedding_dimension(),
                    metric="cosine",
                )
                logger.info("pinecone_index_created", name=self.pinecone_index_name)

            # Initialize vector store
            self._vectorstore = PineconeVectorStore.from_existing_index(
                index_name=self.pinecone_index_name,
                embedding=self.embedding_service.embeddings,
            )

            logger.info("pinecone_initialized", index=self.pinecone_index_name)

        except Exception as e:
            logger.error("pinecone_initialization_failed", error=str(e))
            raise

    async def store_incident(
        self,
        tenant_id: str,
        incident_summary: IncidentSummary,
    ) -> None:
        """Store incident summary in vector store.

        Args:
            tenant_id: Tenant UUID
            incident_summary: Incident summary to store
        """
        try:
            # Create document text
            text = self._create_document_text(incident_summary)

            # Create metadata
            metadata = {
                "tenant_id": tenant_id,
                "incident_number": incident_summary.incident_number,
                "service_name": incident_summary.service_name,
                "resolved_at": incident_summary.resolved_at.isoformat(),
                "root_cause": incident_summary.root_cause or "",
                "fix_applied": incident_summary.fix_applied or "",
                "tags": ",".join(incident_summary.tags),
            }

            # Create document
            document = Document(
                page_content=text,
                metadata=metadata,
            )

            # Add to vector store
            if self.backend == "faiss":
                if self._vectorstore is None:
                    # Create new FAISS index
                    self._vectorstore = FAISS.from_documents(
                        [document],
                        self.embedding_service.embeddings,
                    )
                else:
                    # Add to existing index
                    self._vectorstore.add_documents([document])

                # Save index
                os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
                self._vectorstore.save_local(self.index_path)

            elif self.backend == "pinecone":
                self._vectorstore.add_documents([document])

            logger.info(
                "incident_stored",
                tenant_id=tenant_id,
                incident_number=incident_summary.incident_number,
            )

        except Exception as e:
            logger.error(
                "incident_store_failed",
                tenant_id=tenant_id,
                incident_number=incident_summary.incident_number,
                error=str(e),
            )
            raise

    async def find_similar_incidents(
        self,
        tenant_id: str,
        query: str,
        k: int = 3,
    ) -> List[SimilarIncident]:
        """Find similar past incidents.

        Args:
            tenant_id: Tenant UUID
            query: Query text (incident description)
            k: Number of similar incidents to return

        Returns:
            List of similar incidents with similarity scores
        """
        try:
            if self._vectorstore is None:
                logger.warning("vectorstore_not_initialized")
                return []

            # Search for similar documents
            # Filter by tenant_id
            filter_dict = {"tenant_id": tenant_id}

            results = self._vectorstore.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict,
            )

            # Convert to SimilarIncident objects
            similar_incidents = []
            for doc, score in results:
                # Convert distance to similarity (0-1, higher is more similar)
                # For cosine distance, similarity = 1 - distance
                similarity = 1.0 - score if score < 1.0 else 0.0

                similar_incidents.append(
                    SimilarIncident(
                        incident_number=doc.metadata["incident_number"],
                        summary=doc.page_content,
                        root_cause=doc.metadata.get("root_cause"),
                        fix_applied=doc.metadata.get("fix_applied"),
                        service_name=doc.metadata["service_name"],
                        resolved_at=doc.metadata.get("resolved_at"),
                        similarity_score=similarity,
                    )
                )

            logger.info(
                "similar_incidents_found",
                tenant_id=tenant_id,
                query_length=len(query),
                count=len(similar_incidents),
            )

            return similar_incidents

        except Exception as e:
            logger.error(
                "similar_incidents_search_failed",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def get_runbook(
        self,
        tenant_id: str,
        service_name: str,
    ) -> Optional[str]:
        """Get most relevant runbook content for a service.

        Args:
            tenant_id: Tenant UUID
            service_name: Service name

        Returns:
            Runbook content or None
        """
        try:
            if self._vectorstore is None:
                return None

            # Search for runbook documents
            # Runbooks are stored with special tag "runbook"
            filter_dict = {
                "tenant_id": tenant_id,
                "service_name": service_name,
                "tags": "runbook",
            }

            results = self._vectorstore.similarity_search(
                f"runbook for {service_name}",
                k=1,
                filter=filter_dict,
            )

            if results:
                logger.info(
                    "runbook_found",
                    tenant_id=tenant_id,
                    service_name=service_name,
                )
                return results[0].page_content

            logger.info(
                "runbook_not_found",
                tenant_id=tenant_id,
                service_name=service_name,
            )
            return None

        except Exception as e:
            logger.error(
                "runbook_retrieval_failed",
                tenant_id=tenant_id,
                service_name=service_name,
                error=str(e),
            )
            return None

    async def store_runbook(
        self,
        tenant_id: str,
        service_name: str,
        runbook_content: str,
    ) -> None:
        """Store runbook content for a service.

        Args:
            tenant_id: Tenant UUID
            service_name: Service name
            runbook_content: Runbook content
        """
        try:
            metadata = {
                "tenant_id": tenant_id,
                "service_name": service_name,
                "tags": "runbook",
                "incident_number": f"runbook-{service_name}",
            }

            document = Document(
                page_content=runbook_content,
                metadata=metadata,
            )

            if self.backend == "faiss":
                if self._vectorstore is None:
                    self._vectorstore = FAISS.from_documents(
                        [document],
                        self.embedding_service.embeddings,
                    )
                else:
                    self._vectorstore.add_documents([document])

                os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
                self._vectorstore.save_local(self.index_path)

            elif self.backend == "pinecone":
                self._vectorstore.add_documents([document])

            logger.info(
                "runbook_stored",
                tenant_id=tenant_id,
                service_name=service_name,
            )

        except Exception as e:
            logger.error(
                "runbook_store_failed",
                tenant_id=tenant_id,
                service_name=service_name,
                error=str(e),
            )
            raise

    def _create_document_text(self, incident: IncidentSummary) -> str:
        """Create document text from incident summary.

        Args:
            incident: Incident summary

        Returns:
            Formatted text for embedding
        """
        parts = [
            f"Service: {incident.service_name}",
            f"Summary: {incident.summary}",
        ]

        if incident.root_cause:
            parts.append(f"Root Cause: {incident.root_cause}")

        if incident.fix_applied:
            parts.append(f"Fix Applied: {incident.fix_applied}")

        if incident.tags:
            parts.append(f"Tags: {', '.join(incident.tags)}")

        return "\n".join(parts)
