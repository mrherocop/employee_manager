from flask import Flask, render_template, request, redirect, session, send_file
import pickle, os, csv
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key'

DATA_FILE = "empstatus.dat"
USD_RATE = 83

# Static login credentials (can be improved later)
VALID_USERNAME = "admin"
VALID_PIN = "1234"

def load_all():
    emps = []
    if not os.path.exists(DATA_FILE): return emps
    try:
        with open(DATA_FILE, 'rb') as f:
            while True:
                emps.append(pickle.load(f))
    except EOFError:
        pass
    return emps

def save_all(emps):
    with open(DATA_FILE, 'wb') as f:
        for e in emps:
            pickle.dump(e, f)

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form['username']
        pin = request.form['pin']
        if username == VALID_USERNAME and pin == VALID_PIN:
            session['logged_in'] = True
            return redirect('/')
        else:
            error = "Invalid credentials"
    return render_template('template.html', mode='login', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    return render_template('template.html', mode='index')

@app.route('/add', methods=["GET", "POST"])
def add():
    if not session.get('logged_in'): return redirect('/login')
    if request.method == "POST":
        emp = {
            'Name': request.form['name'],
            'ID': request.form['id'],
            'Salary': float(request.form['salary']),
            'Department': request.form['department'],
            'Designation': request.form['designation'],
            'Currency': 'INR'
        }
        with open(DATA_FILE, 'ab') as f:
            pickle.dump(emp, f)
        return redirect('/list')
    return render_template('template.html', mode='add')

@app.route('/list')
def list_emp():
    if not session.get('logged_in'): return redirect('/login')
    return render_template('template.html', mode='list', employees=load_all())

@app.route('/edit/<emp_id>', methods=["GET", "POST"])
def edit(emp_id):
    if not session.get('logged_in'): return redirect('/login')
    emps = load_all()
    emp = next((e for e in emps if e['ID'] == emp_id), None)
    if request.method == "POST":
        emp.update({
            'Name': request.form['name'],
            'Salary': float(request.form['salary']),
            'Department': request.form['department'],
            'Designation': request.form['designation']
        })
        save_all(emps)
        return redirect('/list')
    return render_template('template.html', mode='edit', emp=emp)

@app.route('/convert')
def convert():
    if not session.get('logged_in'): return redirect('/login')
    emps = load_all()
    for e in emps:
        if e.get('Currency') != 'USD':
            e['Salary'] = round(e['Salary'] / USD_RATE, 2)
            e['Currency'] = 'USD'
    save_all(emps)
    return redirect('/list')

@app.route('/delete/<emp_id>')
def delete(emp_id):
    if not session.get('logged_in'): return redirect('/login')
    emps = [e for e in load_all() if e['ID'] != emp_id]
    save_all(emps)
    return redirect('/list')

@app.route('/search', methods=["GET", "POST"])
def search():
    if not session.get('logged_in'): return redirect('/login')
    result = None
    if request.method == "POST":
        eid = request.form['id']
        result = next((e for e in load_all() if e['ID'] == eid), None)
    return render_template('template.html', mode='search', emp=result, searched=request.method == "POST")

@app.route('/search-name', methods=["GET", "POST"])
def search_name():
    if not session.get('logged_in'): return redirect('/login')
    results = []
    if request.method == "POST":
        q = request.form['name'].lower()
        results = [e for e in load_all() if q in e['Name'].lower()]
    return render_template('template.html', mode='search_name', results=results, searched=request.method == "POST")

@app.route('/export')
def export():
    if not session.get('logged_in'): return redirect('/login')
    emps = load_all()
    csv_file = "employees.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "ID", "Salary", "Currency", "Department", "Designation"])
        writer.writeheader()
        writer.writerows(emps)
    pd.read_csv(csv_file).to_excel("employees.xlsx", index=False)
    return send_file("employees.xlsx", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
