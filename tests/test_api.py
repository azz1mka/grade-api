import pytest


async def upload_csv(client, csv_content: str, token: str = None):
    files = {"file": ("test.csv", csv_content, "text/csv")}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = await client.post("/upload-grades", files=files, headers=headers)
    return response


# ============ ТЕСТЫ АУТЕНТИФИКАЦИИ ============

@pytest.mark.asyncio
async def test_upload_without_auth(client):
    """Тест: загрузка без токена должна быть отклонена"""
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3"""
    response = await upload_csv(client, csv_content)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_as_user_forbidden(client, user_token):
    """Тест: обычный user не может загружать файлы"""
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3"""
    response = await upload_csv(client, csv_content, user_token)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_as_admin_success(client, admin_token):
    """Тест: admin может загружать файлы"""
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3"""
    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_students_with_auth(client, admin_token):
    """Тест: авторизованный пользователь может получать студентов"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/more-than-3-twos", headers=headers)
    assert response.status_code == 200


# ============ СТАРЫЕ ТЕСТЫ (с авторизацией) ============

@pytest.mark.asyncio
async def test_run(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/health", headers=headers)  # ← Изменено с / на /health
    assert response.status_code == 200
    data = response.json()
    assert "Service is running" in data["message"]
    assert data["status"] == "ok"
    print("test_run passed")


@pytest.mark.asyncio
async def test_valid_csv(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3
02.04.2025;ПГ206;Калмыкова Полина Александровна;5
03.04.2025;ПГ206;Калмыкова Полина Александровна;5
03.04.2026;ЮЯ308;Фройлина Нина Ивановна;4
28.02.2026;ОА207;Устинов Александр Валерьевич;2"""

    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["records_loaded"] == 5
    assert data["students"] == 4
    print(f"test_upload_valid_csv passed: {data}")


@pytest.mark.asyncio
async def test_invalid_csv(client, admin_token):
    files = {"file": ("test.txt", "test", "text/plain")}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.post("/upload-grades", files=files, headers=headers)
    assert response.status_code == 400
    assert "Неподдерживаемый формат файла. Отправьте .csv" in response.json()["detail"]
    print("test_nonvalid_csv passed")


@pytest.mark.asyncio
async def test_miss_columns(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;
12.03.2015;103В;Петров Петр"""
    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Отсутствуют колонки" in detail
    assert "Оценка" in detail
    print(f"test_miss_columns passed: {detail}")


@pytest.mark.asyncio
async def test_invalid_grade(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
23.02.2025;ФФ105;Иванов Иван;4
01.04.2025;ФФ105;Семен Крутой;6
02.04.2025;ФФ105;Семен Крутой;-3
03.04.2025;ФФ105;Семен Крутой;4.4"""
    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 200
    data = response.json()
    assert data["records_loaded"] == 1
    assert data["skipped_count"] == 3
    assert any("оценка" in w.lower() for w in data["warnings"])
    print(f"test_nonvalid_grade passed: {data['warnings']}")


@pytest.mark.asyncio
async def test_invalid_date(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
23.02.2025;ФФ105;Иванов Иван;4
2025.03.16;ФФ105;Семен Крутой;3"""
    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 200
    data = response.json()
    assert data["records_loaded"] == 1
    assert data["skipped_count"] == 1
    assert any("дат" in w.lower() for w in data["warnings"])
    print(f"test_invalid_date passed: {data['warnings']}")


@pytest.mark.asyncio
async def test_empty_csv(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка"""
    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 400
    assert "Нет валидных данных" in response.json()["detail"]
    print(f"test_empty_csv passed:")


# ============ ТЕСТЫ ДЛЯ /students/more-than-3-twos ============

@pytest.mark.asyncio
async def test_get_mt3t_empty(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/more-than-3-twos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data == [], f"Ожидали пустой список, получили: {data}"
    print(f"test_get_mt3t passed: {data}")


@pytest.mark.asyncio
async def test_get_mt3t_data(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3
02.04.2025;ВФ203;Владмир Фрунзин;5
03.04.2025;ПГ206;Калмыкова Полина Александровна;2
04.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.02.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.03.2026;ЮЯ308;Фройлина Нина Ивановна;2
28.02.2026;ОА207;Устинов Александр Валерьевич;2"""

    await upload_csv(client, csv_content, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/more-than-3-twos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1, f"Ожидали 1 студента, получили {len(data)}: {data}"
    assert data[0]["full_name"] == "Фройлина Нина Ивановна"
    assert data[0]["count_twos"] == 4
    print(f"test_get_mt3t_data passed: {data}")


@pytest.mark.asyncio
async def test_get_mt3t_border(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3
02.04.2025;ВФ203;Владмир Фрунзин;5
03.04.2025;ПГ206;Калмыкова Полина Александровна;2
04.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.02.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.03.2026;ЮЯ308;Фройлина Нина Ивановна;3
28.02.2026;ОА207;Устинов Александр Валерьевич;2"""

    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 200
    data = response.json()
    assert data["records_loaded"] == 8, f"Ожидали 8 записей, получили {data['records_loaded']}"

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/more-than-3-twos", headers=headers)
    assert response.status_code == 200
    result = response.json()
    name = [s["full_name"] for s in result]
    assert "Фройлина Нина Ивановна" not in name, f"Студент с 3 двойками не должен быть в ответе: {result}"
    print(f"test_get_mt3t_border passed: {result}")


# ============ ТЕСТЫ ДЛЯ /students/less-than-5-twos ============

@pytest.mark.asyncio
async def test_get_lt5t_empty(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/less-than-5-twos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data == [], f"Ожидали пустой список, получили: {data}"
    print(f"test_get_lt5t passed: {data}")


@pytest.mark.asyncio
async def test_get_lt5t_data(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
01.04.2025;ФФ105;Семен Крутой;3
02.04.2025;ВФ203;Владмир Фрунзин;4
03.04.2025;ПГ206;Калмыкова Полина Александровна;5
04.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.02.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.03.2026;ЮЯ308;Фройлина Нина Ивановна;2
04.03.2026;ЮЯ308;Фройлина Нина Ивановна;2
28.02.2026;ОА207;Устинов Александр Валерьевич;2"""

    await upload_csv(client, csv_content, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/less-than-5-twos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4, f"Ожидали 4 студента, получили {len(data)}: {data}"

    name = [s["full_name"] for s in data]
    assert "Семен Крутой" in name
    assert "Владмир Фрунзин" in name
    assert "Калмыкова Полина Александровна" in name
    assert "Устинов Александр Валерьевич" in name

    print(f"test_get_lt5t_data passed: {data}")


@pytest.mark.asyncio
async def test_get_lt5t_border(client, admin_token):
    csv_content = """Дата;Номер группы;ФИО;Оценка
04.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.01.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.02.2026;ЮЯ308;Фройлина Нина Ивановна;2
03.03.2026;ЮЯ308;Фройлина Нина Ивановна;2
04.01.2026;ЮЯ308;Фройлина Нина Ивановна;2"""

    response = await upload_csv(client, csv_content, admin_token)
    assert response.status_code == 200
    data = response.json()
    assert data["records_loaded"] == 5, f"Ожидали 5 записей, получили {data['records_loaded']}"

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/students/less-than-5-twos", headers=headers)
    assert response.status_code == 200
    result = response.json()
    name = [s["full_name"] for s in result]
    assert "Фройлина Нина Ивановна" not in name, f"Студент c 5 двойками не должен быть в ответе: {result}"
    print("test_get_lt5t_border passed")