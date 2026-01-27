#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting development environment...${NC}"

# Start Docker Compose
echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
docker compose up -d

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
sleep 3

# Check if PostgreSQL is healthy
until docker compose exec postgres pg_isready -U talentika_user -d talentika_dev > /dev/null 2>&1; do
  echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
  sleep 1
done

echo -e "${GREEN}PostgreSQL is ready!${NC}"

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
uv run python manage.py migrate

# Start Django development server
echo -e "${GREEN}Starting Django development server...${NC}"
uv run python manage.py runserver
