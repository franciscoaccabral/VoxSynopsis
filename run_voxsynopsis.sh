#!/bin/bash

# VoxSynopsis Runner Script
# This script uses uv to run the application with proper dependency management

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎤 VoxSynopsis - FastWhisper Audio Transcription${NC}"
echo -e "${YELLOW}Starting application with uv...${NC}"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv not found. Please install uv first.${NC}"
    exit 1
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ pyproject.toml not found. Please ensure project is properly configured.${NC}"
    exit 1
fi

# Run application with uv
echo -e "${GREEN}✅ Starting VoxSynopsis with uv...${NC}"
uv run python3 vox_synopsis_fast_whisper.py "$@"