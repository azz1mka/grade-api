#!/bin/bash
set -e  # Выход при ошибке

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Файл .env не найден. Создаём из .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}.env создан${NC}"
        echo -e "${YELLOW}При необходимости отредактируйте пароли в .env${NC}"
    else
        echo -e "${RED}.env.example не найден!${NC}"
        echo " Используется .env.example"
        exit 1
    fi
else
    echo -e "${GREEN}.env найден${NC}"
fi

echo ""
echo -e "${YELLOW}Запуск деплоя...${NC}"
echo "════════════════════════════════════"

echo -e "\n${YELLOW}Этап 1: Запуск тестов${NC}"
echo "────────────────────────────────────"

if docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test; then
    echo -e "${GREEN}Все тесты прошли успешно!${NC}"
else
    echo -e "${RED}Тесты не прошли! Деплой отменён.${NC}"
    echo -e "${YELLOW}Очистка тестовых контейнеров...${NC}"
    docker-compose -f docker-compose.test.yml down -v
    exit 1
fi

echo -e "\n${YELLOW}Этап 2: Очистка тестового окружения${NC}"
echo "────────────────────────────────────"
docker-compose -f docker-compose.test.yml down -v
echo -e "${GREEN}Тестовые контейнеры удалены${NC}"

echo -e "\n${YELLOW}Этап 3: Запуск${NC}"
echo "────────────────────────────────────"


if docker-compose -f docker-compose.yml ps -q | grep -q .; then
    echo -e "${YELLOW}Уже запущено. Перезапускаем...${NC}"
    docker-compose -f docker-compose.yml down
fi

docker-compose -f docker-compose.yml up --build -d

echo -e "\n${YELLOW}Этап 4: Проверка здоровья сервисов${NC}"
echo "────────────────────────────────────"

echo "Ожидание готовности БД..."
for i in {1..30}; do
    if docker-compose -f docker-compose.yml ps db | grep -q "healthy"; then
        echo -e "${GREEN}БД готова${NC}"
        break
    fi
    sleep 2
done

echo "Ожидание готовности API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}API отвечает${NC}"
        break
    fi
    sleep 2
done

echo -e "\n${GREEN}════════════════════════════════════${NC}"
echo -e "${GREEN}Деплой завершён успешно!${NC}"
echo -e "${GREEN}════════════════════════════════════${NC}"
echo ""
echo "Статус сервисов:"
docker-compose -f docker-compose.yml ps
echo ""
echo "Приложение доступно: http://localhost:8000"
echo "Документация API: http://localhost:8000/docs"
echo ""
echo "Логи: docker-compose -f docker-compose.yml logs -f"
echo "Остановка: docker-compose -f docker-compose.yml down"