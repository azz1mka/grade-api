#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

printf "${YELLOW}Установка...${NC}\n"
printf "════════════════════════════════════\n"

printf "Проверка зависимостей...\n"

if ! command -v docker > /dev/null 2>&1; then
    printf "${RED}Docker не установлен!${NC}\n"
    printf "   Установите: https://docs.docker.com/get-docker/\n"
    exit 1
fi

if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    printf "${RED}Docker Compose не установлен!${NC}\n"
    printf "   Установите: https://docs.docker.com/compose/install/\n"
    exit 1
fi
printf "${GREEN}Зависимости установлены${NC}\n"

if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi


REPO_URL="https://github.com/azz1mka/grade-api.git"
PROJECT_DIR="grade-api"

if [ ! -f "docker-compose.prod.yml" ]; then
    printf "Клонирование репозитория...\n"

    if [ -d "$PROJECT_DIR" ]; then
        printf "Папка $PROJECT_DIR уже существует. Удаляем...\n"
        rm -rf "$PROJECT_DIR"
    fi

    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    printf "${GREEN}Репозиторий клонирован${NC}\n"
else
    printf "${GREEN}Файлы проекта уже на месте${NC}\n"
fi

if [ ! -f ".env" ]; then
    printf "  Создание конфигурации...\n"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        printf "${YELLOW}Файл .env создан из .env.example${NC}\n"
        printf "${YELLOW}При необходимости отредактируйте пароли:${NC}\n"
        fi
    else
        printf "${RED}.env.example не найден!${NC}\n"
        exit 1
    fi
else
    printf "${GREEN}.env уже существует${NC}\n"
fi

printf "\n${YELLOW}Запуск тестов и продакшена...${NC}\n"
chmod +x deploy.sh
./deploy.sh
