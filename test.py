import sqlite3

conection = sqlite3.connect('db/data.db',  check_same_thread=False)
cursor = conection.cursor()

all_ids = (cursor.execute('SELECT TeacherID FROM User')).fetchall()
all_ids = [list(row) for row in all_ids]
all_ids = [x for i in all_ids for x in i]
print(all_ids)
