# GitHub Actions Secrets Configuration

This document describes the required GitHub secrets for the Discord Summarize Bot CI/CD pipeline.

## Required Secrets

Add these secrets in your GitHub repository settings under **Settings > Secrets and variables > Actions**.

### Discord Bot Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DISCORD_PUBLIC_KEY` | Discord application public key | `abc123def456...` |
| `DISCORD_APPLICATION_ID` | Discord application ID | `123456789012345678` |
| `DISCORD_BOT_TOKEN` | Discord bot token | `YOUR_BOT_TOKEN_HERE` |

### Google Cloud Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud project ID | `my-discord-bot-project` |
| `GOOGLE_CLOUD_SA_KEY` | Google Cloud service account JSON key | `{"type": "service_account", ...}` |

## How to Set Up Secrets

### 1. Discord Secrets

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Copy the values from:
   - **General Information** → **Application ID**
   - **General Information** → **Public Key**
   - **Bot** → **Token**

### 2. Google Cloud Secrets

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **IAM & Admin** → **Service Accounts**
4. Create or select the service account for your bot
5. Create a new key (JSON format)
6. Copy the entire JSON content

## Security Best Practices

- ✅ Never commit secrets to your repository
- ✅ Use environment-specific secrets
- ✅ Rotate secrets regularly
- ✅ Use least-privilege service accounts
- ✅ Monitor secret usage

## Testing Secrets Locally

For local development, you can use a `.env` file:

```bash
# Copy the template
cp env.template .env

# Edit with your actual values
DISCORD_PUBLIC_KEY=your_public_key
DISCORD_APPLICATION_ID=your_application_id
DISCORD_BOT_TOKEN=your_bot_token
GOOGLE_CLOUD_PROJECT_ID=your_project_id
```

## Troubleshooting

### Common Issues

1. **"Invalid signature" errors**: Check that `DISCORD_PUBLIC_KEY` is correct
2. **"Bot token invalid"**: Verify `DISCORD_BOT_TOKEN` is current
3. **"Permission denied"**: Ensure service account has proper IAM roles
4. **"Project not found"**: Verify `GOOGLE_CLOUD_PROJECT_ID` is correct

### Verification Commands

```bash
# Test Discord bot token
curl -H "Authorization: Bot YOUR_BOT_TOKEN" https://discord.com/api/v10/users/@me

# Test Google Cloud authentication
gcloud auth list

# Test service account permissions
gcloud projects describe YOUR_PROJECT_ID
```
