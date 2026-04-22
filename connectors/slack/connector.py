"""Slack Connector implementation."""

import httpx
from typing import Any, Optional

from connectors.sdk import BaseConnector, retry
from shared.logging import get_logger

logger = get_logger(__name__)


class SlackConnector(BaseConnector):
    """Slack connector for sending messages and notifications."""
    
    def __init__(self, config: dict):
        """Initialize Slack connector.
        
        Args:
            config: Configuration with bot_token and optionally webhook_url
        """
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = "https://slack.com/api"
    
    async def connect(self) -> bool:
        """Establish Slack connection."""
        try:
            if not self.validate_config(["bot_token"]):
                return False
            
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.get_config('bot_token')}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Test connection
            response = await self.client.post(f"{self.base_url}/auth.test")
            data = response.json()
            
            if data.get("ok"):
                self.connected = True
                logger.info("slack_connected", team=data.get("team"))
                return True
            else:
                logger.error("slack_connection_failed", error=data.get("error"))
                return False
                
        except Exception as e:
            logger.error("slack_connection_failed", error=str(e))
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close Slack connection."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info("slack_disconnected")
        return True
    
    async def health_check(self) -> dict:
        """Check Slack connection health."""
        try:
            if not self.client:
                return {"status": "disconnected", "healthy": False}
            
            response = await self.client.post(f"{self.base_url}/auth.test")
            data = response.json()
            
            if data.get("ok"):
                self.health_status = "healthy"
                return {
                    "status": "healthy",
                    "healthy": True,
                    "team": data.get("team"),
                    "user": data.get("user")
                }
            else:
                self.health_status = "unhealthy"
                return {
                    "status": "unhealthy",
                    "healthy": False,
                    "error": data.get("error")
                }
                
        except Exception as e:
            self.health_status = "unhealthy"
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    @retry(max_attempts=3)
    async def execute(self, method: str, **kwargs) -> Any:
        """Execute Slack connector method.
        
        Args:
            method: Method name (send_message, list_channels, etc.)
            **kwargs: Method parameters
            
        Returns:
            Method execution result
        """
        if not self.connected:
            await self.connect()
        
        method_map = {
            "send_message": self.send_message,
            "send_webhook": self.send_webhook,
            "list_channels": self.list_channels,
            "create_channel": self.create_channel,
            "add_reaction": self.add_reaction,
            "upload_file": self.upload_file,
        }
        
        if method not in method_map:
            raise ValueError(f"Unknown method: {method}")
        
        return await method_map[method](**kwargs)
    
    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[list] = None,
        thread_ts: Optional[str] = None
    ) -> dict:
        """Send message to Slack channel.
        
        Args:
            channel: Channel ID or name
            text: Message text
            blocks: Message blocks (optional)
            thread_ts: Thread timestamp for replies (optional)
            
        Returns:
            API response
        """
        payload = {
            "channel": channel,
            "text": text
        }
        
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        response = await self.client.post(
            f"{self.base_url}/chat.postMessage",
            json=payload
        )
        
        data = response.json()
        
        if data.get("ok"):
            logger.info("slack_message_sent", channel=channel)
            return {"success": True, "ts": data.get("ts")}
        else:
            logger.error("slack_message_failed", error=data.get("error"))
            return {"success": False, "error": data.get("error")}
    
    async def send_webhook(self, text: str, blocks: Optional[list] = None) -> dict:
        """Send message via webhook.
        
        Args:
            text: Message text
            blocks: Message blocks (optional)
            
        Returns:
            API response
        """
        webhook_url = self.get_config("webhook_url")
        if not webhook_url:
            return {"success": False, "error": "webhook_url not configured"}
        
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info("slack_webhook_sent")
                return {"success": True}
            else:
                logger.error("slack_webhook_failed", status=response.status_code)
                return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def list_channels(self, types: str = "public_channel,private_channel") -> list:
        """List Slack channels.
        
        Args:
            types: Channel types to list
            
        Returns:
            List of channels
        """
        response = await self.client.post(
            f"{self.base_url}/conversations.list",
            json={"types": types}
        )
        
        data = response.json()
        
        if data.get("ok"):
            return [
                {
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel.get("is_private", False),
                    "num_members": channel.get("num_members", 0)
                }
                for channel in data.get("channels", [])
            ]
        else:
            return []
    
    async def create_channel(self, name: str, is_private: bool = False) -> dict:
        """Create Slack channel.
        
        Args:
            name: Channel name
            is_private: Whether channel is private
            
        Returns:
            Channel details
        """
        response = await self.client.post(
            f"{self.base_url}/conversations.create",
            json={
                "name": name,
                "is_private": is_private
            }
        )
        
        data = response.json()
        
        if data.get("ok"):
            channel = data["channel"]
            return {
                "success": True,
                "channel_id": channel["id"],
                "channel_name": channel["name"]
            }
        else:
            return {"success": False, "error": data.get("error")}
    
    async def add_reaction(self, channel: str, timestamp: str, emoji: str) -> dict:
        """Add reaction to message.
        
        Args:
            channel: Channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)
            
        Returns:
            API response
        """
        response = await self.client.post(
            f"{self.base_url}/reactions.add",
            json={
                "channel": channel,
                "timestamp": timestamp,
                "name": emoji
            }
        )
        
        data = response.json()
        return {"success": data.get("ok", False)}
    
    async def upload_file(
        self,
        channels: str,
        content: str,
        filename: str,
        title: Optional[str] = None
    ) -> dict:
        """Upload file to Slack.
        
        Args:
            channels: Comma-separated channel IDs
            content: File content
            filename: File name
            title: File title (optional)
            
        Returns:
            API response
        """
        payload = {
            "channels": channels,
            "content": content,
            "filename": filename
        }
        
        if title:
            payload["title"] = title
        
        response = await self.client.post(
            f"{self.base_url}/files.upload",
            json=payload
        )
        
        data = response.json()
        
        if data.get("ok"):
            return {
                "success": True,
                "file_id": data["file"]["id"],
                "url": data["file"].get("permalink")
            }
        else:
            return {"success": False, "error": data.get("error")}
