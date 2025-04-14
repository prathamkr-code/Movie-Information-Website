from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_cors import CORS
import requests
import sqlite3
import os

app = Flask(__name__)
CORS(app)
app.secret_key = 'supersecretkey'  # For session management

API_KEY = 'dad68388ae999611b2174cd7a0df7eeb'

# Ensure database exists
DB_FILE = 'users.db'
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    conn.close()

# --- API ROUTES ---
@app.route('/api/categories')
def get_categories():
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}&language=en-US"
    res = requests.get(url)
    return jsonify(res.json())

@app.route('/api/popular/<genre_id>')
def get_movies_by_genre(genre_id):
    sort_by = request.args.get('sort_by', 'popularity.desc')  # Default sorting
    url = (
        f"https://api.themoviedb.org/3/discover/movie?"
        f"api_key={API_KEY}&with_genres={genre_id}&sort_by={sort_by}"
    )
    res = requests.get(url)
    return jsonify(res.json())

@app.route('/api/movie/<int:movie_id>')
def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&append_to_response=credits,reviews"
    res = requests.get(url)
    return res.json()

# --- PAGE ROUTES ---
@app.route('/')
def home():
    if 'username' in session:
        return render_template('module1.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/movie')
def movie_page():
    return render_template('movie.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        passwd = request.form['password']
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (uname, passwd))
        user = cur.fetchone()
        conn.close()
        if user:
            session['username'] = uname
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        passwd = request.form['password']
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (uname, passwd))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('signup.html', error='Username already exists')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# ✅ NEW: Search Route
@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return redirect('/')

    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={query}"
    res = requests.get(url)
    movies = res.json().get('results', [])

    return render_template('search_results.html', movies=movies, query=query)

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
