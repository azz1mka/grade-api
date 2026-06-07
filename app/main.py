
from fastapi import FastAPI, HTTPException, File, UploadFile
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
from contextlib import asynccontextmanager

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_pool()


app = FastAPI(title="Анализ оценок", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Service is running"}


@app.post("/upload-grades", summary="Загрузка CSV-файла с успеваемостью студентов.")
async def upload_grades(file: UploadFile = File(...)):
    # 1. Проверка расширения
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла. Отправьте .csv")

    content = await file.read()
    text_content = content.decode("utf-8-sig")
    csv_file = io.StringIO(text_content)
    reader = csv.DictReader(csv_file, delimiter=';')

    # 2. Проверка заголовков
    req_columns = {'Дата', 'Номер группы', 'ФИО', 'Оценка'}
    actual_columns = set(reader.fieldnames or [])

    if not req_columns.issubset(actual_columns):
        missing_columns = req_columns - actual_columns
        raise HTTPException(status_code=400, detail=f"Отсутствуют колонки: {missing_columns}. Ожидаемые: {req_columns}")

    # 3. Предварительная валидация
    validated_data = []
    skipped_rows = []

    for row_num, row in enumerate(reader, start=2):
        full_name = row.get('ФИО', '').strip()
        group_name = row.get('Номер группы', '').strip()
        date_str = row.get('Дата', '').strip()
        grade_str = row.get('Оценка', '').strip()

        # Проверка на пустые поля
        if not full_name or not group_name or not date_str:
            skipped_rows.append(f"Строка {row_num}: пустые поля")
            continue

        # Проверка даты
        try:
            datetime.strptime(date_str, '%d.%m.%Y')
        except ValueError:
            skipped_rows.append(f"Строка {row_num}: неверный формат даты {date_str}. Ожидался ДД.ММ.ГГГГ")
            continue

        # Проверка оценки
        try:
            grade = int(grade_str)
            if not (1 <= grade <= 5):
                skipped_rows.append(f"Строка {row_num}: оценка {grade_str} вне диапазона.")
                continue
        except ValueError:
            skipped_rows.append(f"Строка {row_num}: оценка {grade_str} не является числом")
            continue

        # Добавить в список для загрузки, если все проверки пройдены
        validated_data.append({
            "full_name": full_name,
            "group_name": group_name,
            "date_str": date_str,
            "grade": grade
        })

    if not validated_data:
        raise HTTPException(status_code=400, detail="Нет валидных данных для загрузки. Проверьте файл.")

    # 4. Сохранение файла
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:6]

    if not skipped_rows:
        saved_filename = f"original_{timestamp}_{unique_id}.csv"
        file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
        with open(file_path, 'wb') as buffer:
            buffer.write(content)
    else:
        saved_filename = f"validated_data_{timestamp}_{unique_id}.csv"
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

    # 5. Запись в базу данных
    unique_students = set()
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            for data in validated_data:
                unique_students.add(f"{data['full_name']}:{data['group_name']}")

                student_id = await conn.fetchval(FIND_OR_CREATE_STUDENT, data['full_name'], data['group_name'])

                await conn.execute(INSERT_GRADE, student_id, data['grade'])

    # 6. Формирование ответа
    response = {
        "status": "ok",
        "records_loaded": len(validated_data),  # Используем длину списка вместо ручного счетчика
        "students": len(unique_students),
    }

    if skipped_rows:
        response["warnings"] = skipped_rows
        response["skipped_count"] = len(skipped_rows)

    return response


@app.get("/students/more-than-3-twos", summary="Возвращает ФИО студентов, у которых оценка 2 встречается больше 3 раз.")
async def more_than_3_twos():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(STUDENTS_MORE_THAN_3_TWOS)

    return [
        {"full_name": row['full_name'], "count_twos": row['count_twos']}
        for row in rows
    ]


@app.get("/students/less-than-5-twos", summary="Возвращает ФИО студентов, у которых оценка 2 встречается меньше 5 раз.")
async def less_than_5_twos():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(STUDENTS_LESS_THAN_5_TWOS)

    return [
        {"full_name": row['full_name'], "count_twos": row['count_twos']}
        for row in rows
    ]


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)