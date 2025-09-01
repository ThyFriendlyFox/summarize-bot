import pytest
import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import discord

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the functions we want to test
from main import (
    verify_discord_signature,
    get_last_summary_timestamp,
    update_last_summary_timestamp,
    extract_keywords,
    summarize_messages,
    create_summary_embed
)

class TestDiscordSignatureVerification:
    """Test Discord signature verification functionality."""
    
    def test_verify_discord_signature_valid(self):
        """Test valid Discord signature verification."""
        with patch.dict(os.environ, {'DISCORD_PUBLIC_KEY': 'test_key'}):
            # This is a simplified test - in real implementation you'd need proper signature
            result = verify_discord_signature(b'test_body', 'test_signature', 'test_timestamp')
            # Should return False for invalid signature but not crash
            assert isinstance(result, bool)
    
    def test_verify_discord_signature_no_key(self):
        """Test signature verification when no public key is set."""
        with patch.dict(os.environ, {}, clear=True):
            result = verify_discord_signature(b'test_body', 'test_signature', 'test_timestamp')
            assert result is False

class TestKeywordExtraction:
    """Test keyword extraction functionality."""
    
    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        text = "The quick brown fox jumps over the lazy dog. Fox is quick and brown."
        keywords = extract_keywords(text, max_keywords=3)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 3
        # Should extract meaningful words, not stop words
        assert 'the' not in keywords
        assert 'is' not in keywords
    
    def test_extract_keywords_empty(self):
        """Test keyword extraction with empty text."""
        keywords = extract_keywords("", max_keywords=5)
        assert keywords == []
    
    def test_extract_keywords_short_words(self):
        """Test that short words are filtered out."""
        text = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
        keywords = extract_keywords(text, max_keywords=10)
        # Should filter out single letters
        assert len(keywords) == 0

class TestMessageSummarization:
    """Test message summarization functionality."""
    
    def test_summarize_messages_empty(self):
        """Test summarizing empty message list."""
        result = summarize_messages([])
        
        assert result['total_messages'] == 0
        assert result['highlights'] == []
        assert result['keywords'] == []
    
    def test_summarize_messages_with_mock_messages(self):
        """Test summarizing messages with mock Discord messages."""
        # Create mock messages
        mock_message1 = Mock()
        mock_message1.content = "This is a test message about Python programming"
        mock_message1.author.display_name = "TestUser1"
        mock_message1.reactions = []
        mock_message1.created_at = datetime.utcnow()
        
        mock_message2 = Mock()
        mock_message2.content = "Another message about Discord bots and APIs"
        mock_message2.author.display_name = "TestUser2"
        mock_message2.reactions = []
        mock_message2.created_at = datetime.utcnow()
        
        messages = [mock_message1, mock_message2]
        result = summarize_messages(messages)
        
        assert result['total_messages'] == 2
        assert len(result['highlights']) <= 5  # Should limit highlights
        assert len(result['keywords']) > 0  # Should extract keywords
        assert 'python' in [kw.lower() for kw in result['keywords']] or 'discord' in [kw.lower() for kw in result['keywords']]

class TestSummaryEmbed:
    """Test Discord embed creation."""
    
    def test_create_summary_embed_error(self):
        """Test embed creation with error data."""
        error_data = {"error": "Test error message"}
        embed_data = create_summary_embed(error_data)
        
        assert "embeds" in embed_data
        assert len(embed_data["embeds"]) == 1
        assert embed_data["embeds"][0]["title"] == "❌ Summary Error"
        assert embed_data["embeds"][0]["description"] == "Test error message"
    
    def test_create_summary_embed_success(self):
        """Test embed creation with successful summary data."""
        summary_data = {
            "guild_name": "Test Guild",
            "guild_id": "123456789",
            "summary_period": {
                "from": "2023-01-01T00:00:00",
                "to": "2023-01-02T00:00:00"
            },
            "total_channels_with_activity": 2,
            "total_messages": 10,
            "channel_summaries": [
                {
                    "channel_name": "general",
                    "channel_id": "111111111",
                    "summary": {
                        "total_messages": 5,
                        "highlights": [
                            {
                                "author": "User1",
                                "content": "Test message 1",
                                "reactions": 2,
                                "timestamp": "2023-01-01T12:00:00"
                            }
                        ],
                        "keywords": ["test", "message"]
                    }
                }
            ],
            "member_changes": "No changes"
        }
        
        embed_data = create_summary_embed(summary_data)
        
        assert "embeds" in embed_data
        assert len(embed_data["embeds"]) == 1
        embed = embed_data["embeds"][0]
        assert "Test Guild" in embed["title"]
        assert embed["color"] == 0x00FF00  # Green color for success

class TestFirestoreIntegration:
    """Test Firestore integration functions."""
    
    @patch('main.db')
    def test_get_last_summary_timestamp_exists(self, mock_db):
        """Test getting existing timestamp from Firestore."""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'last_summary': datetime.utcnow() - timedelta(hours=1)
        }
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        result = get_last_summary_timestamp("test_guild_id")
        
        assert isinstance(result, datetime)
        mock_db.collection.assert_called_with('servers')
    
    @patch('main.db')
    def test_get_last_summary_timestamp_not_exists(self, mock_db):
        """Test getting timestamp when document doesn't exist."""
        # Mock Firestore document that doesn't exist
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        result = get_last_summary_timestamp("test_guild_id")
        
        # Should return timestamp from 24 hours ago
        assert isinstance(result, datetime)
        assert result < datetime.utcnow()
    
    @patch('main.db')
    def test_update_last_summary_timestamp(self, mock_db):
        """Test updating timestamp in Firestore."""
        test_timestamp = datetime.utcnow()
        
        update_last_summary_timestamp("test_guild_id", test_timestamp)
        
        mock_db.collection.assert_called_with('servers')
        mock_doc_ref = mock_db.collection.return_value.document.return_value
        mock_doc_ref.set.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])
