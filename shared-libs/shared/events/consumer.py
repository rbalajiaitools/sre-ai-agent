"""Kafka event consumer."""

import json
import logging
from typing import Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from shared.config import KafkaSettings

logger = logging.getLogger(__name__)


class EventConsumer:
    """Kafka event consumer."""
    
    def __init__(self, settings: KafkaSettings, topics: list[str], group_id: Optional[str] = None):
        """Initialize event consumer.
        
        Args:
            settings: Kafka settings
            topics: List of topics to subscribe to
            group_id: Consumer group ID (defaults to settings.group_id)
        """
        self.settings = settings
        self.topics = topics
        self.group_id = group_id or settings.group_id
        self._consumer: Optional[KafkaConsumer] = None
    
    def connect(self):
        """Connect to Kafka."""
        if self._consumer is None:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.settings.bootstrap_servers.split(","),
                client_id=self.settings.client_id,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset=self.settings.auto_offset_reset,
                enable_auto_commit=self.settings.enable_auto_commit,
            )
            logger.info(
                "Kafka consumer connected",
                bootstrap_servers=self.settings.bootstrap_servers,
                topics=self.topics,
                group_id=self.group_id
            )
    
    def disconnect(self):
        """Disconnect from Kafka."""
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
            logger.info("Kafka consumer disconnected")
    
    def consume(self, handler: Callable[[dict], None], max_messages: Optional[int] = None):
        """Consume messages from Kafka.
        
        Args:
            handler: Message handler function
            max_messages: Maximum number of messages to consume (None for infinite)
        """
        if self._consumer is None:
            self.connect()
        
        message_count = 0
        
        try:
            for message in self._consumer:
                try:
                    logger.debug(
                        "Message received",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        key=message.key
                    )
                    
                    handler(message.value)
                    message_count += 1
                    
                    if max_messages and message_count >= max_messages:
                        break
                        
                except Exception as e:
                    logger.error(
                        "Error processing message",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        error=str(e),
                        exc_info=True
                    )
                    
        except KafkaError as e:
            logger.error("Kafka consumer error", error=str(e))
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
