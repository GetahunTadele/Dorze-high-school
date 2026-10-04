import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'dorze_school_2019_secret_key'

# Database ማዘጋጃ ተግባር
def init_db():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    
    # የላኪዎች/ተጠቃሚዎች ሰንጠረዥ (Users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL
        )
    ''')
    
    # የተማሪዎች ሰንጠረዥ (Students)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade_section TEXT NOT NULL
        )
    ''')
    
    # የአቴንዳንስ እና ውጤት ሰንጠረዥ (Records)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            attendance TEXT,
            quiz REAL,
            mid REAL,
            final REAL,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    # Default Admin የመግቢያ አካውንት ከሌለ መፍጠር
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
                       ('admin', 'admin123', 'admin', 'ትምህርት ቤት አስተዳዳሪ'))
        
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn

# HTML Templates (የገጽታዎች ንድፍ)
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="am">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ዶርዜ 2ኛ ደረጃ ትምህርት ቤት - መግቢያ</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f3; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .login-card { background: white; padding: 35px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); width: 100%; max-width: 360px; text-align: center; }
        h2 { color: #1a365d; margin-bottom: 5px; font-size: 22px; }
        p { color: #718096; font-size: 14px; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #cbd5e0; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        button { width: 100%; padding: 12px; background-color: #2b6cb0; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 15px; margin-top: 10px; }
        button:hover { background-color: #2c5282; }
        .alert { background-color: #fed7d7; color: #9b2c2c; padding: 10px; border-radius: 6px; font-size: 13px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>ዶርዜ 2ኛ ደረጃ ትምህርት ቤት</h2>
        <p>የ2019 ዓ.ም የተማሪዎች መዝገብ ሲስተም</p>
        {% if error %}
            <div class="alert">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username (መጠቃሚያ ስም)" required>
            <input type="password" name="password" placeholder="Password (የይለፍ ቃል)" required>
            <button type="submit">ወደ ሲስተሙ ግባ</button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="am">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>አስተዳዳሪ - ዶርዜ 2ኛ ደረጃ ትምህርት ቤት</title>
    <style>
        body { font-family: sans-serif; background-color: #f7fafc; margin: 0; padding: 20px; }
        .header { background: #2b6cb0; color: white; padding: 15px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        h3 { margin-top: 0; color: #2d3748; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #e2e8f0; border-radius: 5px; box-sizing: border-box; }
        button { background: #38a169; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #edf2f7; padding: 8px; text-align: left; font-size: 14px; }
        th { background: #edf2f7; }
        .logout { background: #e53e3e; color: white; text-decoration: none; padding: 8px 12px; border-radius: 5px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>የአስተዳዳሪ ገፅ (Admin Dashboard)</h2>
        <a href="{{ url_for('logout') }}" class="logout">ውጣ</a>
    </div>

    <div class="grid">
        <div class="card">
            <h3>አዲስ መምህር መመዝገቢያ</h3>
            <form action="{{ url_for('add_teacher') }}" method="POST">
                <input type="text" name="full_name" placeholder="የመምህሩ ሙሉ ስም" required>
                <input type="text" name="username" placeholder="Username (መጠቃሚያ ስም)" required>
                <input type="password" name="password" placeholder="Password (የይለፍ ቃል)" required>
                <button type="submit">መምህር መዝግብ</button>
            </form>

            <h4 style="margin-top: 25px;">የተመዘገቡ መምህራን ዝርዝር</h4>
            <table>
                <tr><th>ስም</th><th>Username</th></tr>
                {% for t in teachers %}
                <tr><td>{{ t.full_name }}</td><td>{{ t.username }}</td></tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h3>አዲስ ተማሪ መመዝገቢያ</h3>
            <form action="{{ url_for('add_student') }}" method="POST">
                <input type="text" name="name" placeholder="የተማሪው ሙሉ ስም" required>
                <input type="text" name="grade_section" placeholder="ክፍል (ምሳሌ፦ 10A, 9B)" required>
                <button type="submit">ተማሪ መዝግብ</button>
            </form>

            <h4 style="margin-top: 25px;">የተማሪዎች ዝርዝር</h4>
            <table>
                <tr><th>ተ.ቁ</th><th>ስም</th><th>ክፍል</th></tr>
                {% for s in students %}
                <tr><td>{{ s.id }}</td><td>{{ s.name }}</td><td>{{ s.grade_section }}</td></tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
'''

TEACHER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="am">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>መምህር - ዶርዜ 2ኛ ደረጃ ትምህርት ቤት</title>
    <style>
        body { font-family: sans-serif; background-color: #f7fafc; margin: 0; padding: 15px; }
        .header { background: #2b6cb0; color: white; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-top: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; overflow-x: auto; display: block; }
        th, td { border: 1px solid #cbd5e0; padding: 8px; text-align: center; min-width: 80px; }
        th { background: #edf2f7; font-size: 13px; }
        input[type="text"], input[type="number"] { width: 90%; padding: 5px; text-align: center; border: 1px solid #cbd5e0; border-radius: 4px; }
        button { background: #38a169; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .logout { background: #e53e3e; color: white; text-decoration: none; padding: 8px 12px; border-radius: 5px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h3 style="margin: 0;">እንኳን ደህና መጡ፣ {{ user.full_name }}</h3>
            <small>የ2019 ዓ.ም የመምህራን መዝገብ</small>
        </div>
        <a href="{{ url_for('logout') }}" class="logout">ውጣ</a>
    </div>

    <div class="card">
        <h3>የተማሪዎች አቴንዳንስ እና ውጤት መሙያ</h3>
        <form action="{{ url_for('save_records') }}" method="POST">
            <table>
                <thead>
                    <tr>
                        <th>ተ.ቁ</th>
                        <th>የተማሪው ስም</th>
                        <th>ክፍል</th>
                        <th>አቴንዳንስ (P/A/E)</th>
                        <th>ክዊዝ (20%)</th>
                        <th>ሚድ (30%)</th>
                        <th>ፋይናል (50%)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td>{{ student.id }}</td>
                        <td>{{ student.name }}</td>
                        <td>{{ student.grade_section }}</td>
                        <td><input type="text" name="att_{{ student.id }}" value="P"></td>
                        <td><input type="number" step="0.1" name="quiz_{{ student.id }}" placeholder="0"></td>
                        <td><input type="number" step="0.1" name="mid_{{ student.id }}" placeholder="0"></td>
                        <td><input type="number" step="0.1" name="final_{{ student.id }}" placeholder="0"></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <button type="submit">መረጃውን ሴቭ ያድርጉ (Save Records)</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        else:
            error = 'የተሳሳተ Username ወይም Password አስገብተዋል!'
            
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db()
    teachers = conn.execute('SELECT * FROM users WHERE role = "teacher"').fetchall()
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    
    return render_template_string(ADMIN_TEMPLATE, teachers=teachers, students=students)

@app.route('/admin/add_teacher', methods=['POST'])
def add_teacher():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    full_name = request.form['full_name']
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
                     (username, password, 'teacher', full_name))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_student', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    name = request.form['name']
    grade_section = request.form['grade_section']
    
    conn = get_db()
    conn.execute('INSERT INTO students (name, grade_section) VALUES (?, ?)', (name, grade_section))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/teacher')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    
    user = {'full_name': session.get('full_name')}
    return render_template_string(TEACHER_TEMPLATE, user=user, students=students)

@app.route('/teacher/save_records', methods=['POST'])
def save_records():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    students = conn.execute('SELECT id FROM students').fetchall()
    
    for s in students:
        sid = s['id']
        att = request.form.get(f'att_{sid}', 'P')
        quiz = request.form.get(f'quiz_{sid}', 0)
        mid = request.form.get(f'mid_{sid}', 0)
        final = request.form.get(f'final_{sid}', 0)
        
        conn.execute('''
            INSERT INTO records (student_id, attendance, quiz, mid, final)
            VALUES (?, ?, ?, ?, ?)
        ''', (sid, att, quiz, mid, final))
        
    conn.commit()
    conn.close()
    return redirect(url_for('teacher_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
