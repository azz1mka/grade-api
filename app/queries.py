FIND_OR_CREATE_STUDENT = """
                    INSERT INTO students (full_name, group_name) VALUES ($1, $2)
                    ON CONFLICT (full_name, group_name) 
                    DO NOTHING
                    RETURNING id
                """

FIND_STUDENT_ID = """
                        SELECT id FROM students
                        WHERE full_name = $1 AND group_name = $2
                """

INSERT_GRADE = """
                    INSERT INTO grades (student_id, grade) VALUES ($1, $2)
                """

STUDENTS_MORE_THAN_3_TWOS = """
            SELECT 
                s.full_name,
                COUNT(g.id) FILTER (WHERE g.grade = 2) as count_twos
            FROM students s 
            JOIN grades g ON s.id = g.student_id
            GROUP BY s.id, s.full_name
            HAVING COUNT(g.id) FILTER (WHERE g.grade = 2) > 3
            ORDER BY count_twos DESC
        """

STUDENTS_LESS_THAN_5_TWOS = """
            SELECT 
                s.full_name,
                COUNT(g.id) FILTER (WHERE g.grade = 2) as count_twos
            FROM students s 
            JOIN grades g ON s.id = g.student_id
            GROUP BY s.id, s.full_name
            HAVING COUNT(g.id) FILTER (WHERE g.grade = 2) < 5
            ORDER BY count_twos DESC
        """