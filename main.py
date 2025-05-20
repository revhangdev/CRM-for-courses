from flask import Flask, render_template, request, redirect, url_for
import sqlite3

conection = sqlite3.connect('db/data.db', check_same_thread=False)
cursor = conection.cursor()

app = Flask(__name__)

logAdm = False
logTchr = False

login = ""
password = ""
userId = 0


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    global login
    global password
    global logTchr
    global logAdm
    global userId
    if request.method == 'POST':
        user_type = request.form.get('userType')  # Отримуємо значення userType

        if user_type == 'adminLogin':
            login = request.form['adminLogin']
            password = request.form['adminPassword']

            cursor.execute('SELECT * FROM User WHERE Login = :us_login', {'us_login': login})
            if cursor.fetchall():
                login_exists_user = True
            else:
                login_exists_user = False

            if login_exists_user:
                cursor.execute('SELECT * FROM User WHERE Login = :us_login AND Password = :passw',
                               {'us_login': login, 'passw': password})
                if cursor.fetchall():
                    cursor.execute('SELECT AdminStatus FROM User WHERE Login = :us_login',
                                   {'us_login': login})
                    isAdmin = cursor.fetchall()[0][0]
                    if str(isAdmin) == "True":
                        logAdm = True
                        return redirect(url_for('admin'))
                    return render_template('index.html')
                return render_template('index.html')
            return render_template('index.html')

        elif user_type == 'teacherLogin':
            login = request.form['teacherLogin']
            password = request.form['teacherPassword']

            cursor.execute('SELECT * FROM User WHERE Login = :us_login', {'us_login': login})
            if cursor.fetchall():
                login_exists_user = True
            else:
                login_exists_user = False

            if login_exists_user:
                cursor.execute('SELECT * FROM User WHERE Login = :us_login AND Password = :passw',
                               {'us_login': login, 'passw': password})
                if cursor.fetchall():
                    cursor.execute('SELECT AdminStatus FROM User WHERE Login = :us_login',
                                   {'us_login': login})
                    isTeacher = cursor.fetchall()[0][0]
                    if str(isTeacher) == "False":
                        logTchr = True
                        cursor.execute('SELECT TeacherID FROM User WHERE Login = :us_login',
                                       {'us_login': login})
                        userId = cursor.fetchall()[0][0]
                        return redirect(url_for('teacher'))
                    return render_template('index.html')
                return render_template('index.html')
            return render_template('index.html')

    return render_template('index.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if logAdm:
        return render_template('AdminMain.html')
    elif not logAdm:
        return render_template('index.html')


@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if logTchr:
        teacher_id = userId

        # Отримайте групи, які веде конкретний викладач
        all_groups = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups WHERE TeacherId=?", (teacher_id,))).fetchall()]

        return render_template('TeacherMain.html', all_groups=all_groups)
    elif not logTchr:
        return render_template('index.html')


@app.route('/AdminTeachers', methods=['GET', 'POST'])
def AdminTeachers():
    list_with_teacher = [x for x in (
        cursor.execute('SELECT Login FROM User where AdminStatus = :admin', {'admin': 'False'}).fetchall())]
    return render_template('AdminTeachers.html', rows=list_with_teacher)


@app.route('/AdminAddGroup', methods=['GET', 'POST'])
def AdminAddGroup():
    if request.method == 'POST':
        group_info = [0, request.form['group'], request.form['classTime'], request.form['NumStudents'],
                      request.form['Teacher'], request.form['groupName'], request.form['studentNames'],
                      request.form['classDay']]

        groups_ids = [x[0] for x in (
            cursor.execute('SELECT GroupID FROM Groups').fetchall())]
        if groups_ids:
            group_info[0] = max(groups_ids) + 1
        else:
            group_info[0] = 1

        if group_info[6] != "none":
            group_info[6] = group_info[6].split(",")

        all_students = [[item[0], item[1], item[2], item[3]] for item in
                        ((cursor.execute("SELECT * FROM Students")).fetchall())]

        # Створюємо словник для швидкого доступу до айді студентів
        student_ids_by_name = {student[1]: student[0] for student in all_students}

        if group_info[6] != 'none':
            # Замінюємо імена студентів в group_info[6] на їх айді
            group_info[6] = [student_ids_by_name[name] if name in student_ids_by_name else name for name in
                             group_info[6]]
            group_info[3] = len(group_info[6])
            group_info[6] = ','.join(map(str, group_info[6]))
        else:
            group_info[3] = 0

        group_info = [int(group_info[0]), str(group_info[1]), str(group_info[2]), int(group_info[3]),
                      int(group_info[4]),
                      str(group_info[5]), str(group_info[6]), str(group_info[7])]

        sqlite_insert_with_param = """INSERT INTO Groups (GroupID, Language, ClassTime, NumStudents, TeacherID, 
                                                GroupName, StudentIDs, ClassDay) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, group_info)
        conection.commit()

        # Ваша функція для оновлення інформації в базі даних
        def update_student_groups(connection, students_to_update, new_group_id):
            all_students = [[item[0], item[1], item[2], item[3]] for item in
                            ((cursor.execute("SELECT * FROM Students")).fetchall())]
            students_to_update = students_to_update.split(",")

            for student in all_students:
                for updt_st in students_to_update:
                    if student[0] == int(updt_st):
                        inf_to_updt = student[3]
                        if inf_to_updt == "none":
                            inf_to_updt = f"{new_group_id}"
                            sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                            cursor.execute(sql_update_query, (inf_to_updt, int(updt_st)))
                        else:
                            inf_to_updt = f"{student[3]},{new_group_id}"
                            sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                            cursor.execute(sql_update_query, (inf_to_updt, int(updt_st)))
            connection.commit()

        if group_info[6] != "none":
            update_student_groups(conection, group_info[6], group_info[0])

        return redirect(url_for('AdminGroup'))

    list_with_teacher = [[str(item[0]), item[1], item[2], item[3]] for item in (
        cursor.execute('SELECT * FROM User').fetchall())]

    return render_template('AdminAddGroup.html', list_with_teacher=list_with_teacher)


#@app.route('/AdminVisits', methods=['GET', 'POST'])
#def AdminVisits():
#    return render_template('AdminVisits.html')


@app.route('/AdminGroup', methods=['GET', 'POST'])
def AdminGroup():
    all_groups = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
        cursor.execute("SELECT * FROM Groups").fetchall())]
    return render_template('AdminGroup.html', all_groups=all_groups)


@app.route('/AdminEditTeacher/<teacher_name>', methods=['GET', 'POST'])
def AdminEditTeacher(teacher_name):
    teacher_info = (cursor.execute('SELECT * FROM User WHERE Login = :us_login',
                                   {'us_login': teacher_name})).fetchone()
    if teacher_info:
        teacher_info = list(teacher_info)
        # if res:
        #    teacher_info = res[0]
        # print(teacher_info)

        if request.method == 'POST':
            login = request.form['login']
            password = request.form['password']
            # teacher_info = list(teacher_info[0])
            teacher_info[1] = login
            teacher_info[2] = password

            cursor.execute("DELETE FROM User WHERE Login = :us_login", {'us_login': teacher_name})
            conection.commit()

            sqlite_insert_with_param = """INSERT INTO User
                                                    (TeacherID, Login, Password, AdminStatus)
                                                    VALUES (?, ?, ?, ?);"""
            cursor.execute(sqlite_insert_with_param, teacher_info)
            conection.commit()

            return redirect(url_for('AdminTeachers'))

    return render_template('AdminEditTeacher.html', teacher_name=teacher_name, teacher_info=teacher_info)


@app.route('/deleteTeacher/<teacher_name>', methods=['GET', 'POST'])
def deleteTeacher(teacher_name):
    cursor.execute("DELETE FROM User WHERE Login = :us_login", {'us_login': teacher_name})
    conection.commit()

    return redirect(url_for('AdminTeachers'))


@app.route('/deleteGroup/<group_id>', methods=['GET', 'POST'])
def deleteGroup(group_id):
    # Отримати інформацію про студентів, які належать цій групі
    students_in_group = cursor.execute("SELECT * FROM Students WHERE GroupId LIKE ?",
                                       ('%' + group_id + '%',)).fetchall()

    # Видалити групу із таблиці груп
    cursor.execute("DELETE FROM Groups WHERE GroupID = :group_id", {'group_id': group_id})

    # Оновити GroupId для студентів, які належать цій групі
    for student in students_in_group:
        updated_group_ids = [group_id for group_id in student[3].split(',') if group_id != group_id]
        updated_group_ids = ','.join(updated_group_ids) if updated_group_ids else 'none'

        # Оновити запис студента
        cursor.execute("UPDATE Students SET GroupId = :updated_group_ids WHERE StudentId = :student_id",
                       {'updated_group_ids': updated_group_ids, 'student_id': student[0]})

    conection.commit()

    return redirect(url_for('AdminGroup'))


@app.route('/deleteStudent/<student_id>', methods=['GET', 'POST'])
def deleteStudent(student_id):
    cursor.execute("DELETE FROM Students WHERE StudentID = :student_id", {'student_id': student_id})
    conection.commit()

    all_groups = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in
                  ((cursor.execute("SELECT * FROM Groups")).fetchall())]

    id_to_updt = ''

    for group in all_groups:
        group_stdnt = group[6].split(",")
        if len(group_stdnt) > 1:
            for elem in group_stdnt:
                if int(elem) != int(student_id):
                    if id_to_updt != '':
                        id_to_updt = f"{id_to_updt},{int(elem)}"
                    else:
                        id_to_updt = f"{int(elem)}"
        else:
            id_to_updt = "none"
        sql_update_query = "UPDATE Groups SET StudentIDs = ? WHERE GroupID = ?"
        cursor.execute(sql_update_query, (id_to_updt, group[0]))
        conection.commit()

        if id_to_updt != "none":
            id_to_updt = id_to_updt.split(",")
            num_stdnt = len(id_to_updt)
        else:
            num_stdnt = 0
        sql_update_query = "UPDATE Groups SET NumStudents = ? WHERE GroupID = ?"
        cursor.execute(sql_update_query, (num_stdnt, group[0]))
        conection.commit()

        id_to_updt = ''

    return redirect(url_for('AdminAddStudent'))


@app.route('/AdminAddTeacher', methods=['GET', 'POST'])
def AdminAddTeacher():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        adminStatus = request.form.get('status')

        all_ids = (cursor.execute('SELECT TeacherID FROM User')).fetchall()
        all_ids = [list(row) for row in all_ids]
        all_ids = [x for i in all_ids for x in i]

        id = max(all_ids) + 1

        new_user_info = [id, login, password, adminStatus]

        sqlite_insert_with_param = """INSERT INTO User
                                            (TeacherID, Login, Password, AdminStatus)
                                           VALUES (?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, new_user_info)
        conection.commit()

        return redirect(url_for('AdminTeachers'))

    return render_template('AdminAddTeacher.html')


@app.route('/AdminEditGroup/<group_id>', methods=['GET', 'POST'])
def AdminEditGroup(group_id):
    if request.method == 'POST':
        old_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups WHERE GroupID = :id",
                           {"id": int(group_id)}).fetchall())]

        group_info = [0, request.form['group'], request.form['classTime'], request.form['NumStudents'],
                      request.form['Teacher'], request.form['groupName'], request.form['studentNames'],
                      request.form['classDay']]
        group_info[0] = group_id
        print(group_info[6])
        group_info[6] = group_info[6].split(",")

        all_students = [[item[0], item[1], item[2], item[3]] for item in
                        ((cursor.execute("SELECT * FROM Students")).fetchall())]
        student_ids_by_name = {student[1]: student[0] for student in all_students}

        # Замінюємо імена студентів в group_info[6] на їх айді
        group_info[6] = [student_ids_by_name[name] if name in student_ids_by_name else name for name in group_info[6]]
        group_info[6] = ','.join(map(str, group_info[6]))
        if group_info[6] != "none":
            ids = group_info[6].split(",")
            group_info[3] = len(ids)
        else:
            group_info[3] = 0

        group_info = [int(group_info[0]), str(group_info[1]), str(group_info[2]), int(group_info[3]),
                      int(group_info[4]),
                      str(group_info[5]), str(group_info[6]), str(group_info[7])]

        cursor.execute('DELETE FROM Groups WHERE GroupID = :id', {'id': int(group_id)})
        conection.commit()

        sqlite_insert_with_param = """INSERT INTO Groups (GroupID, Language, ClassTime, NumStudents, 
                                                TeacherID, GroupName, StudentIDs, ClassDay) 
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, group_info)
        conection.commit()

        # зробити з old_info[6] та group_info[6] масиви через спліт
        group_info[6] = group_info[6].split(",") if group_info[6] != "none" else "none"
        old_info[0][6] = old_info[0][6].split(",") if old_info[0][6] != "none" else "none"
        if old_info[0][6] == "none" and group_info[6] != "none":
            # пройтися по студентам які мають айді з group_info[6] і додати в їх інфо про групи group_info[0]
            for student in all_students:
                for new_id in group_info[6]:
                    if student[0] == int(new_id):
                        info_to_updt = student[3]
                        if info_to_updt != "none":
                            info_to_updt = f"{info_to_updt},{group_info[0]}"
                        else:
                            info_to_updt = f"{group_info[0]}"
                        sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                        cursor.execute(sql_update_query, (info_to_updt, student[0]))
                        conection.commit()
        elif group_info[6] == "none" and old_info[0][6] != "none":
            # пройтися по студентам з айді з old_info[0][6] і видалити з їх інфо про групи group_info[0]
            for student in all_students:
                for old_id in old_info[0][6]:
                    if student[0] == int(old_id):
                        inf_to_updt = student[3].split(",")
                        cor_inf_to_updt = ""
                        if len(inf_to_updt) > 1:
                            for inf in inf_to_updt:
                                if inf != group_info[0]:
                                    if cor_inf_to_updt != "":
                                        cor_inf_to_updt = f"{cor_inf_to_updt},{inf}"
                                    else:
                                        cor_inf_to_updt = f"{inf}"
                        else:
                            cor_inf_to_updt = "none"
                        sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                        cursor.execute(sql_update_query, (cor_inf_to_updt, student[0]))
                        conection.commit()
        elif group_info[6] == "none" and old_info[0][6] == "none":
            pass
        else:
            print(group_info[6])
            print(old_info[0][6])
            # new_inf = sorted(map(int, group_info[6].split(",")))
            # old_inf = sorted(map(int, old_info[0][6].split(",")))
            new_inf = sorted(map(int, group_info[6]))
            old_inf = sorted(map(int, old_info[0][6]))
            if new_inf == old_inf:
                # перед перевіркою ймовірно зробити окремі змінні де відсортувати за зростанням і звірити їх
                pass
            else:
                for old_id in old_info[0][6]:
                    flag = False
                    for new_id in group_info[6]:
                        if old_id == new_id:
                            flag = True
                    if not flag:
                        # видалити з інфо про групи студента з old_id group_info[0]
                        for student in all_students:
                            if student[0] == int(old_id):
                                inf_to_updt = student[3].split(",")
                                cor_inf_to_updt = ""
                                if len(inf_to_updt) > 1:
                                    for inf in inf_to_updt:
                                        if inf != str(group_info[0]):
                                            if cor_inf_to_updt != "":
                                                cor_inf_to_updt = f"{cor_inf_to_updt},{inf}"
                                            else:
                                                cor_inf_to_updt = f"{inf}"
                                else:
                                    cor_inf_to_updt = "none"
                                sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                                cursor.execute(sql_update_query, (cor_inf_to_updt, student[0]))
                                conection.commit()

                for new_id in group_info[6]:
                    flag = False
                    for old_id in old_info[0][6]:
                        if new_id == old_id:
                            flag = True
                    if not flag:
                        # додати до інфо про групи студента з new_id group_info[0]
                        for student in all_students:
                            if student[0] == int(new_id):
                                if student[3] == "none":
                                    inf_to_updt = f"{group_info[0]}"
                                    sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                                    cursor.execute(sql_update_query, (inf_to_updt, student[0]))
                                    conection.commit()
                                else:
                                    inf_to_updt = f"{student[3]},{group_info[0]}"
                                    sql_update_query = "UPDATE Students SET GroupId = ? WHERE StudentID = ?"
                                    cursor.execute(sql_update_query, (inf_to_updt, student[0]))
                                    conection.commit()

        return redirect(url_for('AdminGroup'))

    group_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
        cursor.execute("SELECT * FROM Groups WHERE GroupID = :us_group_id", {"us_group_id": int(group_id)}).fetchall())]
    list_with_teacher = [[str(item[0]), item[1], item[2], item[3]] for item in (
        cursor.execute('SELECT * FROM User').fetchall())]
    teacher_of_group_inf = [[item[0], item[1], item[2], item[3]] for item in (
        cursor.execute("SELECT * FROM User WHERE TeacherID = :us_id", {"us_id": group_info[0][4]}).fetchall())]
    if group_info[0][6] != 'none':
        students_ids = [int(id) for id in group_info[0][6].split(',')]
    else:
        students_ids = "В групі немає студентів"
    all_students = [[item[0], item[1], item[2], item[3]] for item in (
        cursor.execute("SELECT * FROM Students").fetchall())]
    students_dict = {student[0]: student[1] for student in all_students}
    if students_ids != "В групі немає студентів":
        students_names = ', '.join(map(str, ([students_dict[id] for id in students_ids])))
    else:
        students_names = students_ids

    return render_template('AdminEditGroup.html', group_id=group_id,
                           group_info=group_info, list_with_teacher=list_with_teacher,
                           teacher_of_group_inf=teacher_of_group_inf, students_names=students_names)


@app.route('/AdminEditStudent/<student_id>', methods=['GET', 'POST'])
def AdminEditStudent(student_id):
    if request.method == 'POST':
        old_inf = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students WHERE StudentID = :student_id",
                           {"student_id": int(student_id)}).fetchall())]

        new_inf = [int(student_id), request.form["studentName"], request.form["studentPhone"], request.form["group"]]
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]

        group_name_to_id = {group[5]: group[0] for group in all_groups_info}

        if new_inf[3] != "none":
            group_names = new_inf[3].split(',')
            group_ids = [group_name_to_id[name.strip()] for name in group_names if name.strip()]

            if len(group_ids) == 1:
                new_inf[3] = str(group_ids[0])
            else:
                new_inf[3] = ', '.join(map(str, group_ids))

        cursor.execute('DELETE FROM Students WHERE StudentID = :id', {'id': int(student_id)})
        conection.commit()
        sqlite_insert_with_param = """INSERT INTO Students (StudentID, Name, Phone, GroupId)
                                        VALUES (?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, new_inf)
        conection.commit()

        print(old_inf)
        if new_inf[3] == "none":
            if old_inf[0][3] != "none":
                old_ids = old_inf[0][3].split(",")
                for group in all_groups_info:
                    for id in old_ids:
                        if group[0] == int(id):
                            inf_to_updt = group[6].split(",")
                            cor_inf_to_updt = ""
                            if len(inf_to_updt) == 1:
                                cor_inf_to_updt = "none"
                            else:
                                for inf in inf_to_updt:
                                    if str(inf) != str(student_id):
                                        if cor_inf_to_updt != "":
                                            cor_inf_to_updt = f"{cor_inf_to_updt},{inf}"
                                        else:
                                            cor_inf_to_updt = inf
                            sql_update_query = "UPDATE Groups SET StudentIDs = ? WHERE GroupID = ?"
                            cursor.execute(sql_update_query, (cor_inf_to_updt, int(id)))
                            conection.commit()
                            if cor_inf_to_updt != "none":
                                cor_inf_to_updt = cor_inf_to_updt.split(",")
                                num_stdnt = len(cor_inf_to_updt)
                            else:
                                num_stdnt = 0
                            sql_update_query = "UPDATE Groups SET NumStudents = ? WHERE GroupID = ?"
                            cursor.execute(sql_update_query, (num_stdnt, int(id)))
                            conection.commit()

        elif old_inf[0][3] == "none":
            print(new_inf)
            print(old_inf)
            new_ids = new_inf[3].split(",")
            for group in all_groups_info:
                for id in new_ids:
                    if int(id) == int(group[0]):
                        if group[6] != "none":
                            inf_to_udt = f"{group[6]},{student_id}"
                        else:
                            inf_to_udt = f"{student_id}"
                        sql_update_query = "UPDATE Groups SET StudentIDs = ? WHERE GroupID = ?"
                        cursor.execute(sql_update_query, (inf_to_udt, group[0]))
                        conection.commit()
                        if inf_to_udt != "none":
                            inf_to_udt = inf_to_udt.split(",")
                            num_stdnt = len(inf_to_udt)
                        else:
                            num_stdnt = 0
                        sql_update_query = "UPDATE Groups SET NumStudents = ? WHERE GroupID = ?"
                        cursor.execute(sql_update_query, (num_stdnt, int(id)))
                        conection.commit()
        else:
            new_inf = sorted(map(int, new_inf[3].split(",")))
            old_inf = sorted(map(int, old_inf[0][3].split(",")))
            print(new_inf)
            print(old_inf)
            if new_inf == old_inf:
                pass
            else:
                for old_id in old_inf:
                    flag = False
                    for new_id in new_inf:
                        if old_id == new_id:
                            flag = True
                            break
                    if not flag:
                        for group in all_groups_info:
                            if int(group[0]) == int(old_id):
                                inf_to_updt = group[6].split(",")
                                new_inf_updt = ""
                                if len(inf_to_updt) == 1:
                                    new_inf_updt = "none"
                                else:
                                    for elem in inf_to_updt:
                                        if int(elem) != int(student_id):
                                            if new_inf_updt != "":
                                                new_inf_updt = f"{new_inf_updt},{elem}"
                                            else:
                                                new_inf_updt = f"{elem}"
                                sql_update_query = "UPDATE Groups SET StudentIDs = ? WHERE GroupID = ?"
                                cursor.execute(sql_update_query, (new_inf_updt, group[0]))
                                conection.commit()
                                if new_inf_updt != "none":
                                    new_inf_updt = new_inf_updt.split(",")
                                    num_stdnt = len(new_inf_updt)
                                else:
                                    num_stdnt = 0
                                sql_update_query = "UPDATE Groups SET NumStudents = ? WHERE GroupID = ?"
                                cursor.execute(sql_update_query, (num_stdnt, int(group[0])))
                                conection.commit()
                for new_id in new_inf:
                    flag = False
                    for old_id in old_inf:
                        if new_inf == old_id:
                            flag = True
                            break
                    if not flag:
                        for group in all_groups_info:
                            if int(group[0]) == int(new_id):
                                if group[6] != "none":
                                    inf_to_updt = f"{group[6]},{student_id}"
                                else:
                                    inf_to_updt = f"{student_id}"
                                if inf_to_updt != "none":
                                    inf_to_updt = ",".join(
                                        map(str, set([int(item) for item in list(inf_to_updt.split(","))])))
                                sql_update_query = "UPDATE Groups SET StudentIDs = ? WHERE GroupID = ?"
                                cursor.execute(sql_update_query, (inf_to_updt, group[0]))
                                conection.commit()
                                if inf_to_updt != "none":
                                    inf_to_updt = inf_to_updt.split(",")
                                    num_stdnt = len(inf_to_updt)
                                else:
                                    num_stdnt = 0
                                sql_update_query = "UPDATE Groups SET NumStudents = ? WHERE GroupID = ?"
                                cursor.execute(sql_update_query, (num_stdnt, int(group[0])))
                                conection.commit()

        return redirect(url_for('AdminAddStudent'))

    student_info = [[item[0], item[1], item[2], item[3]] for item in (
        cursor.execute("SELECT * FROM Students WHERE StudentID = :student_id",
                       {"student_id": int(student_id)}).fetchall())]

    if student_info[0][3] == 'none':
        student_groups = "Студент ніде не навчається"
    else:
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        ids = student_info[0][3].split(",")
        ids = [int(id.strip()) for id in ids]
        student_groups = [group_name for group_name, group_id in group_name_to_id.items() if group_id in ids]
        student_groups = ",".join(student_groups)

    return render_template('AdminEditStudent.html', student_id=student_id, student_info=student_info,
                           student_groups=student_groups)


@app.route('/AdminAddStudent', methods=['GET', 'POST'])
def AdminAddStudent():
    if request.method == 'POST':
        login = request.form['studentName']
        phone = request.form['studentPhone']
        all_student_ids = [[item[0]] for item in ((cursor.execute("SELECT StudentID FROM Students")).fetchall())]
        all_student_ids = [elem[0] for elem in all_student_ids] if all_student_ids else []
        studentId = 0 if not all_student_ids else max(all_student_ids) + 1
        sqlite_insert_with_param = """INSERT INTO Students
                                                    (StudentID, Name, Phone, GroupId)
                                                    VALUES (?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, [studentId, login, phone, "none"])
        conection.commit()

    all_students = [[item[0], item[1], item[2], item[3]] for item in (
        cursor.execute("SELECT * FROM Students").fetchall())]

    all_groups = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in
                  ((cursor.execute("SELECT * FROM Groups")).fetchall())]

    # Створюємо словник для швидкого доступу до повних даних груп по їхнім айді
    group_data_by_id = {group[0]: group[5] for group in all_groups}

    # Замінюємо айді груп у all_students на назви груп за умови, що значення не є 'none'
    for student in all_students:
        group_ids = student[3].split(',')
        group_names = ''
        if group_ids[0] != 'none':
            for id in group_ids:
                if int(id) in group_data_by_id.keys():
                    if group_names != '':
                        group_names = f"{group_names}, {group_data_by_id[int(id)]}"
                    else:
                        group_names = group_data_by_id[int(id)]
        else:
            group_names = "Не навчається в жодній групі"
        student[3] = group_names

    return render_template('AdminAddStudent.html', all_students=all_students)


@app.route('/PaymentInfo', methods=['GET', 'POST'])
def PaymentInfo():
    if request.method == 'POST':
        new_payment = [int(request.form['PayId']), request.form['GroupName'],
                       request.form['PIB'], request.form['Date'], request.form['Sum']]

        # request.form['GroupName'] => GroupID
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        new_payment[1] = int(group_name_to_id[new_payment[1]])

        # request.form['PIB'] => StudentID
        all_students = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students").fetchall())]
        student_name_to_id = {student[1]: student[0] for student in all_students}
        new_payment[2] = int(student_name_to_id[new_payment[2]])

        # перевірка чи була оплата з таким самим GroupID та StudentID
        # if true:
        #   видалити з бд
        # додати до бд new_payment
        all_payments_info = [[item[0], item[1], item[2], item[3], item[4]] for item in (
            cursor.execute("SELECT * FROM Payments").fetchall())]
        for payment in all_payments_info:
            if int(payment[1]) == new_payment[1] and int(payment[2]) == new_payment[2]:
                cursor.execute('DELETE FROM Payments WHERE GroupID = :group_id AND StudentID = :student_id',
                               {'group_id': int(payment[1]), 'student_id': int(payment[2])})
                conection.commit()
        sqlite_insert_with_param = """INSERT INTO Payments (PaymentID, GroupID, StudentID, Date, Amount)
                                                VALUES (?, ?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, new_payment)
        conection.commit()

    allPay = [[item[0], item[1], item[2], item[3], item[4]] for item in
              ((cursor.execute("SELECT * FROM Payments")).fetchall())]
    # змінити allPay[i][1] на GroupName
    # змінити allPay[i][2] на StudentName
    all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
        cursor.execute("SELECT * FROM Groups").fetchall())]
    group_name_to_id = {group[5]: group[0] for group in all_groups_info}
    all_students = [[item[0], item[1], item[2], item[3]] for item in (
        cursor.execute("SELECT * FROM Students").fetchall())]
    student_name_to_id = {student[1]: student[0] for student in all_students}
    for pay in allPay:
        pay[1] = next(key for key, value in group_name_to_id.items() if value == pay[1])
        pay[2] = next(key for key, value in student_name_to_id.items() if value == pay[2])

    return render_template('AdminPaymentInfo.html', allPay=allPay)


@app.route('/TeacherVisits', methods=['GET', 'POST'])
def TeacherVisits():
    teacher_id = userId
    if request.method == 'POST':
        new_absentees = [0, request.form['GroupName'], request.form['PIB'], request.form['Date'], "none"]

        # request.form['GroupName'] => GroupId
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        new_absentees[1] = int(group_name_to_id[new_absentees[1]])

        # request.form['PIB'] => StudentID
        all_students = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students").fetchall())]
        student_name_to_id = {student[1]: student[0] for student in all_students}
        new_absentees[2] = int(student_name_to_id[new_absentees[2]])

        # new_absentees[0] => correct max ID
        ids = [x[0] for x in (
            cursor.execute('SELECT AbsenteesID FROM Absentees').fetchall())]
        if ids:
            new_absentees[0] = max(ids) + 1
        else:
            new_absentees[0] = 1

        # INSERT to DB
        print("here")
        sqlite_insert_with_param = """INSERT INTO Absentees (AbsenteesID, GroupID, StudentID, AbsentDate, NewLessonDay)
                                                        VALUES (?, ?, ?, ?, ?);"""
        cursor.execute(sqlite_insert_with_param, new_absentees)
        conection.commit()

    # SELECT * FROM Absentees
    all_absentees_info = [[item[0], item[1], item[2], item[3], item[4]] for item in (
        cursor.execute("SELECT * FROM Absentees").fetchall())]

    # Absentees_with_date = [] Absentees_with_out_date = []
    absentees_with_date = []
    absentees_with_out_date = []

    # Пройтися по Absentees
    # В залежності від значення Absentees[i][4] додавати в Absentees_with_date або Absentees_with_out_date
    for absent in all_absentees_info:
        if absent[4] == "none":
            absentees_with_out_date.append(absent)
        else:
            absentees_with_date.append(absent)

    # якщо якийь масив пустий додавати елемент рядок про відсутність інформації
    if absentees_with_date == []:
        absentees_with_date = "Відсутня актуальна інформація"
    else:
        # absentees_with_date[i][1] => GroupName
        # absentees_with_date[i][2] => StudentName
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        all_students = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students").fetchall())]
        student_name_to_id = {student[1]: student[0] for student in all_students}
        for absent in absentees_with_date:
            absent[1] = next(key for key, value in group_name_to_id.items() if value == absent[1])
            absent[2] = next(key for key, value in student_name_to_id.items() if value == absent[2])

    if absentees_with_out_date == []:
        absentees_with_out_date = "Відсутня актуальна інформація"
    else:
        # absentees_with_out_date[i][1] => GroupName
        # absentees_with_out_date[i][2] => StudentName
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        all_students = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students").fetchall())]
        student_name_to_id = {student[1]: student[0] for student in all_students}
        if absentees_with_date != "Відсутня актуальна інформація":
            for absent in absentees_with_date:
                # absent[1] = next(key for key, value in group_name_to_id.items() if value == absent[1])
                # absent[2] = next(key for key, value in student_name_to_id.items() if value == absent[2])
                # Для absent[1]
                for key, value in group_name_to_id.items():
                    if value == absent[1]:
                        absent[1] = key
                        break  # Зупиняємо цикл після першого входження

                # Для absent[2]
                for key, value in student_name_to_id.items():
                    if value == absent[2]:
                        absent[2] = key
                        break  # Зупиняємо цикл після першого входження
        if absentees_with_out_date != "Відсутня актуальна інформація":
            for absent in absentees_with_out_date:
                # absent[1] = next(key for key, value in group_name_to_id.items() if value == absent[1])
                # absent[2] = next(key for key, value in student_name_to_id.items() if value == absent[2])
                # Для absent[1]
                for key, value in group_name_to_id.items():
                    if value == absent[1]:
                        absent[1] = key
                        break  # Зупиняємо цикл після першого входження

                # Для absent[2]
                for key, value in student_name_to_id.items():
                    if value == absent[2]:
                        absent[2] = key
                        break  # Зупиняємо цикл після першого входження
        print(absentees_with_date)
        print(absentees_with_out_date)

    return render_template('TeacherVisits.html', absentees_with_date=absentees_with_date,
                           absentees_with_out_date=absentees_with_out_date)


@app.route('/deleteAbsent/<absent_id>', methods=['GET', 'POST'])
def deleteAbsent(absent_id):
    cursor.execute("DELETE FROM Absentees WHERE AbsenteesID = :absent_id", {'absent_id': absent_id})
    conection.commit()

    return redirect(url_for('TeacherVisits'))


@app.route('/AdminVisits', methods=['GET', 'POST'])
def AdminVisits():
    # SELECT * FROM Absentees
    all_absentees_info = [[item[0], item[1], item[2], item[3], item[4]] for item in (
        cursor.execute("SELECT * FROM Absentees").fetchall())]

    # Absentees_with_date = [] Absentees_with_out_date = []
    absentees_with_date = []
    absentees_with_out_date = []

    # Пройтися по Absentees
    # В залежності від значення Absentees[i][4] додавати в Absentees_with_date або Absentees_with_out_date
    for absent in all_absentees_info:
        if absent[4] == "none":
            absentees_with_out_date.append(absent)
        else:
            absentees_with_date.append(absent)

    # якщо якийь масив пустий додавати елемент рядок про відсутність інформації
    if absentees_with_date == []:
        absentees_with_date = "Відсутня актуальна інформація"
    else:
        # absentees_with_date[i][1] => GroupName
        # absentees_with_date[i][2] => StudentName
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        all_students = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students").fetchall())]
        student_name_to_id = {student[1]: student[0] for student in all_students}
        for absent in absentees_with_date:
            absent[1] = next(key for key, value in group_name_to_id.items() if value == absent[1])
            absent[2] = next(key for key, value in student_name_to_id.items() if value == absent[2])

    if absentees_with_out_date == []:
        absentees_with_out_date = "Відсутня актуальна інформація"
    else:
        # absentees_with_out_date[i][1] => GroupName
        # absentees_with_out_date[i][2] => StudentName
        all_groups_info = [[item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]] for item in (
            cursor.execute("SELECT * FROM Groups").fetchall())]
        group_name_to_id = {group[5]: group[0] for group in all_groups_info}
        all_students = [[item[0], item[1], item[2], item[3]] for item in (
            cursor.execute("SELECT * FROM Students").fetchall())]
        student_name_to_id = {student[1]: student[0] for student in all_students}
        if absentees_with_date != "Відсутня актуальна інформація":
            for absent in absentees_with_date:
                # absent[1] = next(key for key, value in group_name_to_id.items() if value == absent[1])
                # absent[2] = next(key for key, value in student_name_to_id.items() if value == absent[2])
                # Для absent[1]
                for key, value in group_name_to_id.items():
                    if value == absent[1]:
                        absent[1] = key
                        break  # Зупиняємо цикл після першого входження

                # Для absent[2]
                for key, value in student_name_to_id.items():
                    if value == absent[2]:
                        absent[2] = key
                        break  # Зупиняємо цикл після першого входження
        if absentees_with_out_date != "Відсутня актуальна інформація":
            for absent in absentees_with_out_date:
                # absent[1] = next(key for key, value in group_name_to_id.items() if value == absent[1])
                # absent[2] = next(key for key, value in student_name_to_id.items() if value == absent[2])
                # Для absent[1]
                for key, value in group_name_to_id.items():
                    if value == absent[1]:
                        absent[1] = key
                        break  # Зупиняємо цикл після першого входження

                # Для absent[2]
                for key, value in student_name_to_id.items():
                    if value == absent[2]:
                        absent[2] = key
                        break  # Зупиняємо цикл після першого входження
        print(absentees_with_date)
        print(absentees_with_out_date)

    return render_template('AdminVisits.html', absentees_with_date=absentees_with_date,
                           absentees_with_out_date=absentees_with_out_date)


@app.route('/AddAbsentDate/<absent_id>', methods=['GET', 'POST'])
def AddAbsentDate(absent_id):
    new_date = request.form.get('NewDate')
    print(f"Absent ID: {absent_id}, New Date: {new_date}")
    sql_update_query = "UPDATE Absentees SET NewLessonDay = ? WHERE AbsenteesID = ?"
    cursor.execute(sql_update_query, (new_date, absent_id))
    conection.commit()

    return redirect(url_for('AdminVisits'))


port = 5100
if __name__ == '__main__':
    app.debug = True
    app.run(port=port)
