import os
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
import discord
from discord.ext import commands
from google.cloud import firestore
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Discord Summarize Bot")

# Environment variables
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
DISCORD_APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Firestore
db = firestore.Client(project=GOOGLE_CLOUD_PROJECT_ID)

class DiscordInteraction(BaseModel):
    type: int
    data: Optional[Dict[str, Any]] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    member: Optional[Dict[str, Any]] = None

def verify_discord_signature(request_body: bytes, signature: str, timestamp: str) -> bool:
    """Verify Discord webhook signature for security."""
    if not DISCORD_PUBLIC_KEY:
        logger.error("DISCORD_PUBLIC_KEY not set")
        return False
    
    try:
        # Discord signature verification
        message = timestamp + "." + request_body.decode('utf-8')
        expected_signature = hmac.new(
            DISCORD_PUBLIC_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"v0={expected_signature}", signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False

def get_last_summary_timestamp(guild_id: str) -> datetime:
    """Get the last summary timestamp for a guild from Firestore."""
    try:
        doc_ref = db.collection('servers').document(guild_id)
        doc = doc_ref.get()
        
        if doc.exists:
            last_summary = doc.to_dict().get('last_summary')
            if last_summary:
                return last_summary
    except Exception as e:
        logger.error(f"Error getting last summary timestamp: {e}")
    
    # Default to 24 hours ago if no previous summary
    return datetime.utcnow() - timedelta(hours=24)

def update_last_summary_timestamp(guild_id: str, timestamp: datetime):
    """Update the last summary timestamp for a guild in Firestore."""
    try:
        doc_ref = db.collection('servers').document(guild_id)
        doc_ref.set({
            'last_summary': timestamp,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        logger.error(f"Error updating last summary timestamp: {e}")

def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract keywords from text using simple frequency analysis."""
    # Simple keyword extraction - in production you might want more sophisticated NLP
    words = text.lower().split()
    word_freq = {}
    
    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    for word in words:
        # Remove punctuation and filter short words
        word = ''.join(c for c in word if c.isalnum())
        if len(word) > 2 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]

def summarize_messages(messages: List[discord.Message]) -> Dict[str, Any]:
    """Summarize a list of messages."""
    if not messages:
        return {
            "total_messages": 0,
            "highlights": [],
            "keywords": []
        }
    
    # Sort messages by reactions (if any) and length
    messages_with_score = []
    for msg in messages:
        score = len(msg.content) + (len(msg.reactions) * 10)  # Simple scoring
        messages_with_score.append((msg, score))
    
    # Get top messages by score
    top_messages = sorted(messages_with_score, key=lambda x: x[1], reverse=True)[:5]
    
    # Extract highlights
    highlights = []
    for msg, score in top_messages:
        content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
        highlights.append({
            "author": msg.author.display_name,
            "content": content,
            "reactions": len(msg.reactions),
            "timestamp": msg.created_at.isoformat()
        })
    
    # Extract keywords from all messages
    all_text = " ".join([msg.content for msg in messages])
    keywords = extract_keywords(all_text)
    
    return {
        "total_messages": len(messages),
        "highlights": highlights,
        "keywords": keywords
    }

async def get_guild_summary(guild_id: str) -> Dict[str, Any]:
    """Get summary of guild activity since last summary."""
    try:
        guild = bot.get_guild(int(guild_id))
        if not guild:
            return {"error": "Guild not found"}
        
        last_timestamp = get_last_summary_timestamp(guild_id)
        current_time = datetime.utcnow()
        
        # Get all text channels
        text_channels = [channel for channel in guild.channels if isinstance(channel, discord.TextChannel)]
        
        channel_summaries = []
        total_messages = 0
        total_channels_with_activity = 0
        
        for channel in text_channels:
            try:
                # Fetch messages since last summary (limit to 500 to avoid rate limits)
                messages = []
                async for message in channel.history(limit=500, after=last_timestamp):
                    messages.append(message)
                
                if messages:
                    summary = summarize_messages(messages)
                    channel_summaries.append({
                        "channel_name": channel.name,
                        "channel_id": str(channel.id),
                        "summary": summary
                    })
                    total_messages += summary["total_messages"]
                    total_channels_with_activity += 1
                    
            except discord.Forbidden:
                logger.warning(f"No permission to read channel {channel.name}")
            except Exception as e:
                logger.error(f"Error processing channel {channel.name}: {e}")
        
        # Get member changes (if possible)
        member_changes = "Member changes not tracked in this version"
        
        # Update timestamp
        update_last_summary_timestamp(guild_id, current_time)
        
        return {
            "guild_name": guild.name,
            "guild_id": guild_id,
            "summary_period": {
                "from": last_timestamp.isoformat(),
                "to": current_time.isoformat()
            },
            "total_channels_with_activity": total_channels_with_activity,
            "total_messages": total_messages,
            "channel_summaries": channel_summaries,
            "member_changes": member_changes
        }
        
    except Exception as e:
        logger.error(f"Error getting guild summary: {e}")
        return {"error": f"Failed to generate summary: {str(e)}"}

def create_summary_embed(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a Discord embed for the summary."""
    if "error" in summary_data:
        return {
            "embeds": [{
                "title": "❌ Summary Error",
                "description": summary_data["error"],
                "color": 0xFF0000
            }]
        }
    
    embed = {
        "title": f"📊 Server Summary: {summary_data['guild_name']}",
        "description": f"Activity summary from {summary_data['summary_period']['from'][:19]} to {summary_data['summary_period']['to'][:19]}",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "📈 Overview",
                "value": f"• **Total Messages:** {summary_data['total_messages']}\n• **Active Channels:** {summary_data['total_channels_with_activity']}",
                "inline": False
            }
        ]
    }
    
    # Add channel summaries
    for channel_summary in summary_data['channel_summaries'][:10]:  # Limit to 10 channels
        summary = channel_summary['summary']
        highlights_text = ""
        
        for highlight in summary['highlights'][:3]:  # Top 3 highlights
            highlights_text += f"• **{highlight['author']}:** {highlight['content'][:100]}...\n"
        
        if highlights_text:
            embed["fields"].append({
                "name": f"📝 #{channel_summary['channel_name']} ({summary['total_messages']} messages)",
                "value": highlights_text[:1024],  # Discord limit
                "inline": False
            })
    
    # Add keywords if available
    if summary_data['channel_summaries']:
        all_keywords = set()
        for channel_summary in summary_data['channel_summaries']:
            all_keywords.update(channel_summary['summary']['keywords'])
        
        if all_keywords:
            keywords_text = ", ".join(list(all_keywords)[:10])
            embed["fields"].append({
                "name": "🔑 Key Topics",
                "value": keywords_text,
                "inline": False
            })
    
    return {"embeds": [embed]}

@app.post("/discord/interactions")
async def handle_discord_interaction(request: Request):
    """Handle Discord interaction webhook."""
    try:
        # Get request data
        body = await request.body()
        signature = request.headers.get("x-signature-ed25519", "")
        timestamp = request.headers.get("x-signature-timestamp", "")
        
        # Verify signature
        if not verify_discord_signature(body, signature, timestamp):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse interaction
        interaction_data = json.loads(body)
        interaction = DiscordInteraction(**interaction_data)
        
        # Handle ping (Discord verification)
        if interaction.type == 1:
            return JSONResponse(content={"type": 1})
        
        # Handle slash command
        if interaction.type == 2:
            command_name = interaction.data.get("name", "")
            
            if command_name == "summarize":
                guild_id = interaction.guild_id
                if not guild_id:
                    return JSONResponse(content={
                        "type": 4,
                        "data": {
                            "content": "❌ This command can only be used in a server!"
                        }
                    })
                
                # Defer response for longer processing
                await request.app.state.bot.wait_until_ready()
                
                # Generate summary
                summary_data = await get_guild_summary(guild_id)
                response_data = create_summary_embed(summary_data)
                
                return JSONResponse(content={
                    "type": 4,
                    "data": response_data
                })
        
        return JSONResponse(content={"type": 4, "data": {"content": "Unknown command"}})
        
    except Exception as e:
        logger.error(f"Error handling Discord interaction: {e}")
        return JSONResponse(content={
            "type": 4,
            "data": {"content": f"❌ An error occurred: {str(e)}"}
        })

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup."""
    try:
        await bot.start(DISCORD_BOT_TOKEN)
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        await bot.close()
        logger.info("Bot stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
