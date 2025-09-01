# Discord Summarize Bot

A Discord bot that provides server activity summaries using slash commands. Built with FastAPI, discord.py, and Google Cloud Firestore, designed for deployment on Google Cloud Run.

## Features

- **Slash Command**: `/summarize` - Generates comprehensive server activity summaries
- **Smart Summarization**: Extracts key highlights, keywords, and message statistics
- **State Management**: Tracks last summary timestamp per server using Firestore
- **Serverless**: Designed for Google Cloud Run with event-driven architecture
- **Security**: Discord signature verification for webhook security

## Architecture

- **FastAPI**: HTTP server for handling Discord webhooks
- **discord.py**: Discord API interactions
- **Google Cloud Firestore**: Persistent state storage
- **Docker**: Containerization for Cloud Run deployment

## Setup Instructions

### 1. Discord Bot Setup

1. **Create Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Go to "Bot" section and create a bot
   - Copy the **Bot Token** and **Public Key**

2. **Configure Slash Commands**:
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Read Messages/View Channels`, `Send Messages`, `Use Slash Commands`
   - Use the generated URL to invite the bot to your server

3. **Set Interaction Endpoint**:
   - Go to "General Information"
   - Set "Interactions Endpoint URL" to: `https://your-cloud-run-url/discord/interactions`
   - Save changes

### 2. Google Cloud Setup

1. **Create Project**:
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable APIs**:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable firestore.googleapis.com
   ```

3. **Create Firestore Database**:
   - Go to [Firestore Console](https://console.cloud.google.com/firestore)
   - Create database in "Native mode"
   - Collection: `servers` (will be created automatically)

4. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create discord-bot-sa \
     --display-name="Discord Bot Service Account"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:discord-bot-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

### 3. Local Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export DISCORD_PUBLIC_KEY="your_discord_public_key"
   export DISCORD_APPLICATION_ID="your_discord_application_id"
   export DISCORD_BOT_TOKEN="your_discord_bot_token"
   export GOOGLE_CLOUD_PROJECT_ID="your_project_id"
   ```

3. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth application-default login
   ```

4. **Test Locally** (using ngrok for webhook testing):
   ```bash
   # Install ngrok
   brew install ngrok  # macOS
   
   # Start the bot
   python main.py
   
   # In another terminal, expose local server
   ngrok http 8080
   
   # Update Discord interaction endpoint with ngrok URL
   # https://your-ngrok-url.ngrok.io/discord/interactions
   ```

### 4. Deployment to Google Cloud Run

1. **Build and Deploy**:
   ```bash
   # Build Docker image
   gcloud builds submit --tag gcr.io/your-project-id/discord-summarize-bot
   
   # Deploy to Cloud Run
   gcloud run deploy discord-summarize-bot \
     --image gcr.io/your-project-id/discord-summarize-bot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="DISCORD_PUBLIC_KEY=your_discord_public_key" \
     --set-env-vars="DISCORD_APPLICATION_ID=your_discord_application_id" \
     --set-env-vars="DISCORD_BOT_TOKEN=your_discord_bot_token" \
     --set-env-vars="GOOGLE_CLOUD_PROJECT_ID=your_project_id" \
     --service-account=discord-bot-sa@your-project-id.iam.gserviceaccount.com
   ```

2. **Update Discord Interaction Endpoint**:
   - Copy the Cloud Run URL from deployment output
   - Update Discord Developer Portal with: `https://your-cloud-run-url/discord/interactions`

## Usage

1. **Invite bot to your Discord server** using the OAuth2 URL
2. **Use the slash command**: `/summarize`
3. **Bot will respond** with a comprehensive summary including:
   - Total messages and active channels
   - Channel-by-channel breakdown
   - Key highlights and topics
   - Activity period information

## Testing Framework

The project includes a comprehensive testing framework to ensure code quality and reliability.

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type coverage
python run_tests.py --type lint
python run_tests.py --type security
python run_tests.py --type docker
```

### Test Types

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test API endpoints and Discord interactions
- **Coverage**: Generate code coverage reports
- **Linting**: Check code style and quality
- **Security**: Run security vulnerability scans
- **Docker**: Test Docker image builds

### GitHub Actions CI/CD

The project includes automated CI/CD pipelines:

1. **Test Workflow** (`test.yml`): Runs on every push and PR
   - Unit tests across multiple Python versions
   - Integration tests
   - Docker build tests
   - Security scans
   - Code quality checks

2. **Deploy Workflow** (`deploy.yml`): Runs on main branch pushes
   - Automatic deployment to Google Cloud Run
   - Post-deployment verification
   - Service health checks

### Setting Up GitHub Actions

1. **Add Required Secrets** (see `docs/GITHUB_SECRETS.md`):
   - `DISCORD_PUBLIC_KEY`
   - `DISCORD_APPLICATION_ID`
   - `DISCORD_BOT_TOKEN`
   - `GOOGLE_CLOUD_PROJECT_ID`
   - `GOOGLE_CLOUD_SA_KEY`

2. **Enable Actions**: Go to repository Settings → Actions → General

3. **Monitor Workflows**: Check the Actions tab for test and deployment status

### Local Development Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests with pytest
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=main --cov-report=html

# Test local server
python test_local.py
```

### Test Coverage

The testing framework aims for:
- **Unit Test Coverage**: >80%
- **Integration Test Coverage**: All critical paths
- **Security Scan**: No high-severity vulnerabilities
- **Code Quality**: Passes all linting checks

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_PUBLIC_KEY` | Discord application public key | Yes |
| `DISCORD_APPLICATION_ID` | Discord application ID | Yes |
| `DISCORD_BOT_TOKEN` | Discord bot token | Yes |
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud project ID | Yes |

### Firestore Schema

```
Collection: servers
Document ID: guild_id
Fields:
  - last_summary: timestamp
  - updated_at: timestamp
```

## Security Features

- **Discord Signature Verification**: All webhooks are verified using Discord's public key
- **Non-root Container**: Docker container runs as non-root user
- **Environment Variables**: Sensitive data stored as environment variables
- **Service Account**: Minimal permissions for Google Cloud access

## Error Handling

The bot gracefully handles:
- Missing Discord permissions
- Rate limiting
- Database connection issues
- Invalid webhook signatures
- Cold starts on Cloud Run

## Monitoring

- **Health Check**: `/health` endpoint for monitoring
- **Logging**: Structured logging for debugging
- **Cloud Run Metrics**: Built-in monitoring and scaling

## Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check Cloud Run logs: `gcloud logs tail --service=discord-summarize-bot`
   - Verify Discord interaction endpoint URL
   - Ensure bot has proper permissions

2. **Database errors**:
   - Verify service account permissions
   - Check Firestore database exists
   - Ensure project ID is correct

3. **Signature verification fails**:
   - Verify `DISCORD_PUBLIC_KEY` environment variable
   - Check Discord application public key

### Local Testing

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test with Discord webhook (using ngrok)
curl -X POST https://your-ngrok-url.ngrok.io/discord/interactions \
  -H "Content-Type: application/json" \
  -H "x-signature-ed25519: test" \
  -H "x-signature-timestamp: $(date +%s)" \
  -d '{"type":1}'
```

## Development

### Project Structure

```
summarize-bot/
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md           # This file
```

### Adding Features

1. **New Commands**: Add to the interaction handler in `main.py`
2. **Enhanced Summarization**: Modify `summarize_messages()` function
3. **Additional Data**: Extend Firestore schema and update functions

## License

MIT License - feel free to modify and distribute.
