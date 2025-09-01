#!/bin/bash

# Discord Summarize Bot Deployment Script
# This script automates the deployment process to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID:-"your-project-id"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
SERVICE_NAME="discord-summarize-bot"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}🚀 Discord Summarize Bot Deployment Script${NC}"
echo "=========================================="

# Check if required environment variables are set
check_env_vars() {
    echo -e "${YELLOW}Checking environment variables...${NC}"
    
    if [ -z "$DISCORD_PUBLIC_KEY" ]; then
        echo -e "${RED}❌ DISCORD_PUBLIC_KEY is not set${NC}"
        exit 1
    fi
    
    if [ -z "$DISCORD_APPLICATION_ID" ]; then
        echo -e "${RED}❌ DISCORD_APPLICATION_ID is not set${NC}"
        exit 1
    fi
    
    if [ -z "$DISCORD_BOT_TOKEN" ]; then
        echo -e "${RED}❌ DISCORD_BOT_TOKEN is not set${NC}"
        exit 1
    fi
    
    if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
        echo -e "${RED}❌ GOOGLE_CLOUD_PROJECT_ID is not set${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All environment variables are set${NC}"
}

# Check if gcloud is installed and authenticated
check_gcloud() {
    echo -e "${YELLOW}Checking Google Cloud CLI...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed${NC}"
        echo "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ Not authenticated with Google Cloud${NC}"
        echo "Please run: gcloud auth login"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Google Cloud CLI is ready${NC}"
}

# Build and deploy the application
deploy() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    gcloud builds submit --tag ${IMAGE_NAME}
    
    echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_NAME} \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --set-env-vars="DISCORD_PUBLIC_KEY=${DISCORD_PUBLIC_KEY}" \
        --set-env-vars="DISCORD_APPLICATION_ID=${DISCORD_APPLICATION_ID}" \
        --set-env-vars="DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}" \
        --set-env-vars="GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID}" \
        --service-account=discord-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com \
        --memory 512Mi \
        --cpu 1 \
        --max-instances 10
    
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
}

# Get the service URL
get_service_url() {
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
    echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
    echo -e "${YELLOW}📝 Discord Interaction Endpoint: ${SERVICE_URL}/discord/interactions${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update your Discord application's interaction endpoint URL"
    echo "2. Test the bot with /summarize command"
    echo "3. Monitor logs with: gcloud logs tail --service=${SERVICE_NAME}"
}

# Main execution
main() {
    check_env_vars
    check_gcloud
    deploy
    get_service_url
}

# Run main function
main "$@"
