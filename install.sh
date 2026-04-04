#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Установка...${NC}"
echo "════════════════════════════════════"

echo "Проверка зависимостей..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не установлен!${NC}"
    echo "   Установите: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose не установлен!${NC}"
    echo "   Установите: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}Зависимости установлены${NC}"

if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

REPO_URL = "https://raw.githubusercontent.com/azz1mka/grade-api/refs/heads/main/install.sh"
PROJECT_DIR = "grade_api"

if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Клонирование репозитория..."

    if [ -d "$PROJECT_DIR" ]; then
        echo "Папка $PROJECT_DIR уже существует. Удаляем..."
        rm -rf "$PROJECT_DIR"
    fi

    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    echo -e "${GREEN}Репозиторий клонирован${NC}"
else
    echo -e "${GREEN}Файлы проекта уже на месте${NC}"
fi

if [ ! -f ".env" ]; then
    echo "Создание конфигурации..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Файл .env создан из .env.example${NC}"
        echo -e "${YELLOW}   При необходимости отредактируйте пароли:${NC}"
        echo "   nano .env"
        echo ""
        read -p "Продолжить установку? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Установка отменена"
            exit 0
        fi
    else
        echo -e "${RED}.env.example не найден!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}.env уже существует${NC}"
fi

echo -e "\n${YELLOW}Запуск тестов и продакшена...${NC}"
chmod +x deploy.sh
./deploy.sh
