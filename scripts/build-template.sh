#!/bin/bash
# Local build script for MCP server templates

set -e

# Configuration
REGISTRY="ghcr.io/data-everything"
TEMPLATE_NAME="file-server"
TEMPLATE_DIR="templates/$TEMPLATE_NAME"
IMAGE_NAME="mcp-$TEMPLATE_NAME"
FULL_IMAGE="$REGISTRY/$IMAGE_NAME:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building MCP Template: $TEMPLATE_NAME${NC}"

# Check if template directory exists
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo -e "${RED}❌ Template directory not found: $TEMPLATE_DIR${NC}"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$TEMPLATE_DIR/Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found in: $TEMPLATE_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Template directory: $TEMPLATE_DIR${NC}"
echo -e "${YELLOW}🏷️  Image name: $FULL_IMAGE${NC}"

# Build the image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -t "$FULL_IMAGE" "$TEMPLATE_DIR"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    
    # Show image info
    echo -e "${BLUE}📊 Image information:${NC}"
    docker images "$FULL_IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Test the image
    echo -e "${BLUE}🧪 Testing image...${NC}"
    docker run --rm --name "test-$IMAGE_NAME" "$FULL_IMAGE" --help || true
    
    echo -e "${GREEN}🎉 Image built and tested successfully!${NC}"
    echo -e "${YELLOW}💡 To push to registry: docker push $FULL_IMAGE${NC}"
    echo -e "${YELLOW}💡 To run locally: docker run --rm -p 8000:8000 -v \$(pwd)/data:/data $FULL_IMAGE${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
