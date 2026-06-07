-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица студентов
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    UNIQUE (full_name, group_name)
);

-- Таблица оценок
CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 5)
);

-- Индексы
CREATE UNIQUE INDEX IF NOT EXISTS idx_students_name_group
ON students(full_name, group_name);

CREATE INDEX IF NOT EXISTS idx_grades_student_grade
ON grades(student_id, grade);

CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);

CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);

