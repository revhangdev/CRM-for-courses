import sqlite3

# Підключення до бази даних (створює новий файл, якщо його не існує)
conn = sqlite3.connect('db/data.db')
cursor = conn.cursor()

# Створення таблиці для викладачів
cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        TeacherID INTEGER PRIMARY KEY,
        Login TEXT NOT NULL,
        Password TEXT NOT NULL,
        AdminStatus BOOL NOT NULL
    )
''')

# Створення таблиці для студентів
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Students (
        StudentID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Phone TEXT NOT NULL,
        GroupId TEXT NOT NULL
    )
''')

# Створення таблиці для груп
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Groups (
        GroupID INTEGER PRIMARY KEY,
        Language TEXT NOT NULL,
        ClassTime TEXT NOT NULL,
        NumStudents INTEGER NOT NULL,
        TeacherID INTEGER,
        GroupName TEXT NOT NULL,
        StudentIDs TEXT NOT NULL,
        ClassDay TEXT NOT NULL,
        FOREIGN KEY (TeacherID) REFERENCES User(TeacherID)
    )
''')

# Створення таблиці для студентів, які були відсутніми
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Absentees (
        AbsenteesID INTEGER PRIMARY KEY,
        GroupID INTEGER NOT NULL,
        StudentID INTEGER NOT NULL,
        Date TEXT NOT NULL,
        FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
        FOREIGN KEY (GroupID) REFERENCES Groups(GroupID)
    )
''')

# Створення таблиці для даних про оплату
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Payments (
        PaymentID INTEGER PRIMARY KEY,
        GroupID INTEGER NOT NULL,
        StudentID INTEGER NOT NULL,
        Date TEXT NOT NULL,
        Amount TEXT NOT NULL,
        FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
        FOREIGN KEY (GroupID) REFERENCES Groups(GroupID)
    )
''')

# Збереження змін та закриття підключення
conn.commit()
conn.close()
