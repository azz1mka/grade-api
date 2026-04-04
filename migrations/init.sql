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
