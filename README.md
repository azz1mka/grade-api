# Анализ оценок студентов
Приложение для загрузки и анализа оценок студентов из .csv файлов. 
## Описание
Функционал:
- Загрузка .csv файлов
- Валидация данных
- Поиск студентов с более чем 3 двойками и менее чем 5 двойками
## Требования
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
## Возможные проблемы
По умолчанию Docker требует использование sudo. В связи с этим install.sh может быть недоступен, а команда `./deploy.sh` не может быть использована без sudo.
Чтобы это исправить выполните:
```
newgrp docker
sudo usermod -aG docker $USER
```

## Установка
Для установки можно воспользоваться одним из вариантов:
### Вариант 1

```
curl -sSL https://raw.githubusercontent.com/azz1mka/grade-api/main/install.sh | bash
```
Или через wget
```
sh <(wget -O - https://raw.githubusercontent.com/azz1mka/grade-api/main/install.sh)
```
### Вариант 2 (Вручную)

#### Клонируйте репозиторий
```
git clone https://github.com/azz1mka/grade-api.git
cd grade-api
```
### Запуск, если скрипты не работают
Если `instal.sh` или `deploy.sh` не сработали, можно запустить проект вручную
#### Клонируйте репозиторий
```
git clone https://github.com/azz1mka/grade-api.git
cd grade-api
```
#### Создайте файл `.env` и вставьте содержимое `.env.example` (можно воспользоваться тем, что представлен ниже)
```
cp .env.example .env
nano .env #для редактирования
```
#### Запуск тестов (опционально)
```
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
docker-compose -f docker-compose.test.yml down -v
```
#### Запуск проекта
```
docker-compose -f docker-compose up --build -d
```

Конфигурация с данными для доступа к БД создается автоматически (.env файл), можно отредактировать:
```
DATABASE_URL=postgresql://postgres:secret@localhost:5432/grades_db

TEST_DATABASE_URL=postgresql://postgres:secret@localhost:5432/grades_db_test

DEBUG=True
UPLOAD_FOLDER=uploads
DB_USER=postgres
DB_PASSWORD=secret
```
#### Запустите проект 
```
chmod +x deploy.sh
./deploy.sh
```
Сервис будет доступен по адресу 
```
http://localhost:8000
```
Документация API:
```
http://localhost:8000/docs

```
## Загрузка данных

Производится в формате:
```
Дата;Номер группы;ФИО;Оценка
01.02.03;ФФ105;Иванов Иван;5
```
- Дата: в формате: ДД.ММ.ГГГГ
- Оценка: целое число от 1 до 5
## Тесты
Запускаются автоматически, при запуске файла ./deploy.sh, в Docker, после этого контейнер удаляется.
Тесты покрывают:
- Валидацию формата файла
- Проверку обязательных колонок
- Валидацию оценок и дат
- Пустые файлы
- Эндпоинты для анализа студентов
- Граничные условия
## Управление
Если находитесь в директории проекта
- Остановить проект:
```
docker-compose -f docker-compose.yml down
```
- Логи:
```
docker-compose -f docker-compose.yml logs -f
```




