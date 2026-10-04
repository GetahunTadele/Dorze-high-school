from flask import Flask, render_template_string, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'dorze_school_secret_key'

# የመግቢያ መረጃዎች (Default Credentials)
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'አስተዳዳሪ (Admin)'},
    'teacher1': {'password': '123456', 'role': 'teacher', 'name': 'መምህር (Teacher 1)'}
}

# የተማሪዎች ናሙና መረጃ
STUDENTS = [
    {'id': 1, 'name': 'አበበ ከበደ', 'grade': '10A'},
    {'id': 2, 'name': 'አልማዝ ተስፋዬ', 'grade': '10A'},
    {'id': 3, 'name': 'ጫላ በከለ', 'grade': '10A'}
]

# HTML Templates (የገጽታዎች ንድፍ)
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="am">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ዶርዜ 2ኛ ደረጃ ትምህርት ቤት - መግቢያ</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 320px; text-align: center; }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #27ae60; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #219150; }
        .error { color: red; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>ዶርዜ 2ኛ ደረጃ ትምህርት ቤት</h2>
        <p style="color: #7f8c8d; font-size: 14px;">የ2019 ዓ.ም የመግቢያ ገጽ</p>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username (መጠቃሚያ ስም)" required>
            <input type="password" name="password" placeholder="Password (የይለፍ ቃል)" required>
            <button type="submit">ግቡ (Login)</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="am">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ዳሽቦርድ - ዶርዜ 2ኛ ደረጃ ትምህርት ቤት</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }
        .header { background-color: #2c3e50; color: white; padding: 15px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
        th { background-color: #f2f2f2; }
        .btn-logout { background-color: #e74c3c; color: white; text-decoration: none; padding: 8px 15px; border-radius: 5px; font-size: 14px; }
        .badge { background-color: #3498db; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h3 style="margin: 0;">እንኳን ደህና መጡ፣ {{ user_info.name }}</h3>
            <span class="badge">{{ user_info.role.upper() }}</span>
        </div>
        <a href="{{ url_for('logout') }}" class="btn-logout">ውጣ (Logout)</a>
    </div>

    <div class="card">
        <h4>የተማሪዎች አቴንዳንስ እና ውጤት መዝገብ</h4>
        <table>
            <thead>
                <tr>
                    <th>ተ.ቁ</th>
                    <th>የተማሪው ስም</th>
                    <th>ክፍል</th>
                    <th>አቴንዳንስ (P/A)</th>
                    <th>ውጤት (100%)</th>
                </tr>
            </thead>
            <tbody>
                {% for student in students %}
                <tr>
                    <td>{{ student.id }}</td>
                    <td>{{ student.name }}</td>
                    <td>{{ student.grade }}</td>
                    <td><input type="text" value="P" style="width: 50px; text-align: center;"></td>
                    <td><input type="number" placeholder="0" style="width: 60px; text-align: center;"></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <br>
        <button style="padding: 10px 20px; background-color: #27ae60; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">መረጃውን መዝግብ (Save)</button>
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
        
        user = USERS.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'የተሳሳተ Username ወይም Password አስገብተዋል!'
            
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_info = USERS.get(username)
    return render_template_string(DASHBOARD_TEMPLATE, user_info=user_info, students=STUDENTS)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
