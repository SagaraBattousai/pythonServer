import os
import sqlite3
import hashlib
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash


app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, "pythonServer.db"),
    SECRET_KEY="development key",
))

SELECT_QUERY = "select username, title, text from entries order by id desc"
INSERT_QUERY = "insert into entries (username, title, text) values (?, ?, ?)"

SELECT_USER = "select username from users where username=? AND password=?"
INSERT_USER = "insert into users (username, password) values (?, ?)"

USER_EXISTS = "select username from users where username=?"


SALT="AlwaysBeSalthingDemHashes!"

hashfunc = lambda password: hashlib.sha256(str.encode(password + SALT)).hexdigest()

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()
   # session.pop('logged_in', None)


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print("Database Initialised")


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute(SELECT_QUERY)
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(INSERT_QUERY, [session['user'], request.form['title'], request.form['text']])
    db.commit()
    flash("New entry was posted")
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = hashfunc(request.form['password'])
        verify = db.execute(SELECT_USER, [username, password]).fetchone()
        if verify == None:
            error = "Login Error"
        else:
            session['user'] = username
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You Were Logged Out")
    return redirect(url_for('show_entries'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = hashfunc(request.form['password'])
        userExists = db.execute(USER_EXISTS, [username]).fetchone()
        if userExists != None:
            error = "Username Taken!"
        else:
            db.execute(INSERT_USER, [username, password])
            db.commit()
            session['logged_in'] = True
            flash('You were registered and logged in')
            return redirect(url_for('show_entries'))
    return render_template('register.html', error=error)



