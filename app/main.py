from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, status
import uvicorn
import io
import csv
import os
import uuid
from datetime import datetime
from app.db import get_pool, close_pool
from app.queries import (
    FIND_OR_CREATE_STUDENT,
    INSERT_GRADE,
    STUDENTS_MORE_THAN_3_TWOS,
    STUDENTS_LESS_THAN_5_TWOS
)
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_role
)
from app.schemas import UserCreate, UserResponse, Token
from contextlib import asynccontextmanager

UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_pool()


app = FastAPI(title="Анализ оценок", lifespan=lifespan)


# ============ АУТЕНТИФИКАЦИЯ ============

@app.post("/auth/register", response_model=UserResponse, summary="Регистрация нового пользователя")
async def register(user: UserCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Проверка существующего пользователя
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE username = $1 OR email = $2",
            user.username, user.email
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким username или email уже существует"
            )

        # Создание пользователя — ВСЕГДА role = 'user'
        hashed_password = get_password_hash(user.password)
        user_id = await conn.fetchval(
            """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES ($1, $2, $3, 'user')
            RETURNING id
            """,
            user.username, user.email, hashed_password
        )

        return {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "role": "user",
            "is_active": True
        }


@app.post("/auth/login", response_model=Token, summary="Получение JWT токена")
async def login(username: str, password: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, username, hashed_password, is_active FROM users WHERE username = $1",
            username
        )

        if not user or not verify_password(password, user['hashed_password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный username или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь деактивирован"
            )

        access_token = create_access_token(data={"sub": user['username']})
        return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse, summary="Получить информацию о текущем пользователе")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ============ ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ ============

@app.get("/", summary="Проверка доступности")
async def root(current_user: dict = Depends(get_current_user)):
    return {"message": f"Service is running. Welcome, {current_user['username']}!"}


@app.post(
    "/upload-grades",
    summary="Загрузка CSV-файла с успеваемостью студентов (только для admin)"
)
async def upload_grades(
        file: UploadFile = File(...),
        current_user: dict = Depends(require_role("admin"))  # Только admin!
):
    # Проверка размера файла
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимум: {MAX_FILE_SIZE // (1024 * 1024)} МБ"
        )

    # Проверка расширения
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый формат файла. Отправьте .csv"
        )

    text_content = content.decode("utf-8-sig")
    csv_file = io.StringIO(text_content)
    reader = csv.DictReader(csv_file, delimiter=';')

    # Проверка заголовков
    req_columns = {'Дата', 'Номер группы', 'ФИО', 'Оценка'}
    actual_columns = set(reader.fieldnames or [])

    if not req_columns.issubset(actual_columns):
        missing_columns = req_columns - actual_columns
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Отсутствуют колонки: {missing_columns}. Ожидаемые: {req_columns}"
        )

    # Валидация данных
    validated_data = []
    skipped_rows = []

    for row_num, row in enumerate(reader, start=2):
        full_name = row.get('ФИО', '').strip()
        group_name = row.get('Номер группы', '').strip()
        date_str = row.get('Дата', '').strip()
        grade_str = row.get('Оценка', '').strip()

        if not full_name or not group_name or not date_str:
            skipped_rows.append(f"Строка {row_num}: пустые поля")
            continue

        try:
            datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            skipped_rows.append(f"Строка {row_num}: неверный формат даты {date_str}")
            continue

        try:
            grade = int(grade_str)
            if not (1 <= grade <= 5):
                skipped_rows.append(f"Строка {row_num}: оценка {grade_str} вне диапазона")
                continue
        except ValueError:
            skipped_rows.append(f"Строка {row_num}: оценка {grade_str} не является числом")
            continue

        validated_data.append({
            "full_name": full_name,
            "group_name": group_name,
            "date_str": date_str,
            "grade": grade
        })

    if not validated_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет валидных данных для загрузки"
        )

    # Сохранение файла
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:6]

    if not skipped_rows:
        saved_filename = f"original_{timestamp}_{unique_id}.csv"
        file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
        with open(file_path, 'wb') as buffer:
            buffer.write(content)
    else:
        saved_filename = f"validated_{timestamp}_{unique_id}.csv"
        file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Дата', 'Номер группы', 'ФИО', 'Оценка'], delimiter=';')
            writer.writeheader()
            for data in validated_data:
                writer.writerow({
                    'Дата': data['date_str'],
                    'Номер группы': data['group_name'],
                    'ФИО': data['full_name'],
                    'Оценка': data['grade']
                })

    # Запись в БД
    unique_students = set()
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            for data in validated_data:
                unique_students.add(f"{data['full_name']}:{data['group_name']}")
                student_id = await conn.fetchval(FIND_OR_CREATE_STUDENT, data['full_name'], data['group_name'])
                await conn.execute(INSERT_GRADE, student_id, data['grade'])

    response = {
        "status": "ok",
        "records_loaded": len(validated_data),
        "students": len(unique_students),
        "uploaded_by": current_user['username']
    }

    if skipped_rows:
        response["warnings"] = skipped_rows
        response["skipped_count"] = len(skipped_rows)

    return response


@app.get(
    "/students/more-than-3-twos",
    summary="Студенты с >3 двоек (доступно всем авторизованным)"
)
async def more_than_3_twos(current_user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(STUDENTS_MORE_THAN_3_TWOS)
    return [{"full_name": row['full_name'], "count_twos": row['count_twos']} for row in rows]


@app.get(
    "/students/less-than-5-twos",
    summary="Студенты с <5 двоек (доступно всем авторизованным)"
)
async def less_than_5_twos(current_user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(STUDENTS_LESS_THAN_5_TWOS)
    return [{"full_name": row['full_name'], "count_twos": row['count_twos']} for row in rows]


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)