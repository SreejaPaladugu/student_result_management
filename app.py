
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_connection, init_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
init_db()

def calculate_grade(marks):
    marks = int(marks)
    return 'A' if marks >= 90 else 'B' if marks >= 75 else 'C' if marks >= 60 else 'D'

@app.route('/')
def home():
    return redirect(url_for('dashboard') if 'username' in session else 'login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        hashed = generate_password_hash(password, method='sha256')
        try:
            conn = get_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
            conn.commit()
            flash('User registered!')
            return redirect(url_for('login'))
        except:
            flash('Username already exists.')
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, pwd = request.form['username'], request.form['password']
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (user,))
        u = cur.fetchone()
        if u and check_password_hash(u['password'], pwd):
            session['username'] = user
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        name, roll, marks = request.form['name'], request.form['roll'], request.form['marks']
        grade = calculate_grade(marks)
        try:
            conn = get_connection()
            conn.execute('INSERT INTO students (name, roll, marks, grade) VALUES (?, ?, ?, ?)', (name, roll, marks, grade))
            conn.commit()
            flash('Student added!')
            return redirect(url_for('view_students'))
        except:
            flash('Error adding student.')
        finally:
            conn.close()
    return render_template('add_student.html')

@app.route('/view_students')
def view_students():
    if 'username' not in session: return redirect(url_for('login'))
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM students')
    data = cur.fetchall()
    conn.close()
    return render_template('view_students.html', students=data)

@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'username' not in session: return redirect(url_for('login'))
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM students WHERE id = ?', (id,))
    student = cur.fetchone()
    if request.method == 'POST':
        name, roll, marks = request.form['name'], request.form['roll'], request.form['marks']
        grade = calculate_grade(marks)
        cur.execute('UPDATE students SET name=?, roll=?, marks=?, grade=? WHERE id=?',
                    (name, roll, marks, grade, id))
        conn.commit()
        conn.close()
        flash('Student updated!')
        return redirect(url_for('view_students'))
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'username' not in session: return redirect(url_for('login'))
    conn = get_connection()
    conn.execute('DELETE FROM students WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Student deleted!')
    return redirect(url_for('view_students'))

if __name__ == '__main__':
    app.run(debug=True)
