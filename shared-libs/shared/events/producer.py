"""Kafka event producer."""

import json
import logging
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from shared.config import KafkaSettings
from shared.events.schemas import BaseEvent

logger = logging.getLogger(__name__)


class EventProducer:
    """Kafka event producer."""
    
    def __init__(self, settings: KafkaSettings):
        """Initialize event producer.
        
        Args:
            settings: Kafka settings
        """
        self.settings = settings
        self._producer: Optional[KafkaProducer] = None
    
    def connect(self):
        """Connect to Kafka."""
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.settings.bootstrap_servers.split(","),
                client_id=self.settings.client_id,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
            )
            logger.info("Kafka producer connected", bootstrap_servers=self.settings.bootstrap_servers)
    
    def disconnect(self):
        """Disconnect from Kafka."""
        if self._producer is not None:
            self._producer.close()
            self._producer = None
            logger.info("Kafka producer disconnected")
    
    async def publish(self, topic: str, event: BaseEvent, key: Optional[str] = None):
        """Publish event to Kafka topic.
        
        Args:
            topic: Kafka topic
            event: Event to publish
            key: Optional partition key
        """
        if self._producer is None:
            self.connect()
        
        try:
            event_data = event.model_dump(mode="json")
            future = self._producer.send(
                topic,
                value=event_data,
                key=key or event.tenant_id
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                "Event published",
                topic=topic,
                event_type=event.event_type,
                event_id=event.event_id,
                partition=record_metadata.partition,
                offset=record_metadata.offset
            )
            
        except KafkaError as e:
            logger.error(
                "Failed to publish event",
                topic=topic,
                event_type=event.event_type,
                event_id=event.event_id,
                error=str(e)
            )
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
