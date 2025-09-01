import pytest
import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import app

class TestDiscordWebhookIntegration:
    """Integration tests for Discord webhook handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_discord_ping_interaction(self, client):
        """Test Discord ping interaction."""
        payload = {"type": 1}
        headers = {
            "Content-Type": "application/json",
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": "1234567890"
        }
        
        response = client.post("/discord/interactions", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == 1
    
    def test_discord_summarize_command_no_guild(self, client):
        """Test summarize command without guild context."""
        payload = {
            "type": 2,
            "data": {"name": "summarize"},
            "guild_id": None
        }
        headers = {
            "Content-Type": "application/json",
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": "1234567890"
        }
        
        response = client.post("/discord/interactions", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == 4
        assert "content" in data["data"]
        assert "server" in data["data"]["content"].lower()
    
    def test_discord_unknown_command(self, client):
        """Test unknown command handling."""
        payload = {
            "type": 2,
            "data": {"name": "unknown_command"},
            "guild_id": "123456789"
        }
        headers = {
            "Content-Type": "application/json",
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": "1234567890"
        }
        
        response = client.post("/discord/interactions", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == 4
        assert "Unknown command" in data["data"]["content"]

class TestDiscordBotIntegration:
    """Integration tests for Discord bot functionality."""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self):
        """Test bot initialization."""
        from main import bot
        
        # Test that bot has correct intents
        assert bot.intents.message_content is True
        assert bot.intents.guilds is True
    
    @pytest.mark.asyncio
    async def test_guild_summary_integration(self):
        """Test guild summary generation with mocked Discord API."""
        from main import get_guild_summary
        
        # Mock Discord guild and channels
        mock_guild = Mock()
        mock_guild.name = "Test Guild"
        mock_guild.id = 123456789
        
        # Mock text channel
        mock_channel = Mock()
        mock_channel.name = "general"
        mock_channel.id = 111111111
        
        # Mock messages
        mock_message1 = Mock()
        mock_message1.content = "Test message 1"
        mock_message1.author.display_name = "User1"
        mock_message1.reactions = []
        mock_message1.created_at = Mock()
        mock_message1.created_at.isoformat.return_value = "2023-01-01T12:00:00"
        
        mock_message2 = Mock()
        mock_message2.content = "Test message 2"
        mock_message2.author.display_name = "User2"
        mock_message2.reactions = []
        mock_message2.created_at = Mock()
        mock_message2.created_at.isoformat.return_value = "2023-01-01T13:00:00"
        
        # Mock channel history
        async def mock_history(*args, **kwargs):
            yield mock_message1
            yield mock_message2
        
        mock_channel.history = mock_history
        
        # Set up guild channels
        mock_guild.channels = [mock_channel]
        
        # Mock bot.get_guild
        with patch('main.bot') as mock_bot:
            mock_bot.get_guild.return_value = mock_guild
            
            # Mock Firestore functions
            with patch('main.get_last_summary_timestamp') as mock_get_timestamp, \
                 patch('main.update_last_summary_timestamp') as mock_update_timestamp:
                
                mock_get_timestamp.return_value = Mock()
                
                result = await get_guild_summary("123456789")
                
                assert "guild_name" in result
                assert result["guild_name"] == "Test Guild"
                assert "total_messages" in result
                assert result["total_messages"] >= 0
                assert "channel_summaries" in result
                assert len(result["channel_summaries"]) >= 0

class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)
    
    def test_invalid_signature(self, client):
        """Test handling of invalid Discord signature."""
        payload = {"type": 1}
        headers = {
            "Content-Type": "application/json",
            "x-signature-ed25519": "invalid_signature",
            "x-signature-timestamp": "1234567890"
        }
        
        # This should fail signature verification
        response = client.post("/discord/interactions", json=payload, headers=headers)
        assert response.status_code == 401
    
    def test_malformed_payload(self, client):
        """Test handling of malformed JSON payload."""
        headers = {
            "Content-Type": "application/json",
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": "1234567890"
        }
        
        # Send malformed JSON
        response = client.post("/discord/interactions", data="invalid json", headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_missing_headers(self, client):
        """Test handling of missing required headers."""
        payload = {"type": 1}
        
        # Missing Discord signature headers
        response = client.post("/discord/interactions", json=payload)
        assert response.status_code == 401

class TestEnvironmentIntegration:
    """Integration tests for environment variable handling."""
    
    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing."""
        from main import DISCORD_PUBLIC_KEY, DISCORD_APPLICATION_ID, DISCORD_BOT_TOKEN, GOOGLE_CLOUD_PROJECT_ID
        
        # These should be None when not set in test environment
        # In production, they should be set
        assert DISCORD_PUBLIC_KEY is None or isinstance(DISCORD_PUBLIC_KEY, str)
        assert DISCORD_APPLICATION_ID is None or isinstance(DISCORD_APPLICATION_ID, str)
        assert DISCORD_BOT_TOKEN is None or isinstance(DISCORD_BOT_TOKEN, str)
        assert GOOGLE_CLOUD_PROJECT_ID is None or isinstance(GOOGLE_CLOUD_PROJECT_ID, str)

if __name__ == "__main__":
    pytest.main([__file__])
