import sqlite3
from flask import Flask, request, render_template, send_file, redirect, url_for,session
import cv2
import numpy as np
import io
import os
from PIL import Image
app = Flask(__name__)
app.secret_key = '123'
# Set up SQLite database
def create_connection():
    conn = sqlite3.connect('database.db')
    return conn

def create_table(conn):
    sql_create_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        );
    """
    cur = conn.cursor()
    cur.execute(sql_create_table)
    conn.commit()

# Sign up route
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirmPassword']

    if password != confirm_password:
        return 'Passwords do not match!'

    conn = create_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
    conn.commit()
    conn.close()

    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = create_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]  # Store the username in the session
            return render_template("index.html")  # You can redirect to a dashboard page or any other page here
        else:
            return 'Invalid username or password'

    return render_template("index.html")


# Serve the HTML file
@app.route('/')
def index():
    return render_template('signup.html')


app.config['UPLOAD_FOLDER'] = 'static'

def convert_to_sketch(image):
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Invert the grayscale image
    inverted_image = cv2.bitwise_not(gray_image)
    # Blur the inverted image
    blurred = cv2.GaussianBlur(inverted_image, (21, 21), 0)
    # Invert the blurred image
    inverted_blurred = cv2.bitwise_not(blurred)
    # Create the pencil sketch image
    sketch = cv2.divide(gray_image, inverted_blurred, scale=256.0)
    return sketch


@app.route('/bot')
def bot():
    return render_template('bot.html')



@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        # Convert the uploaded file to a numpy array
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)

        # Convert to sketch
        sketch = convert_to_sketch(image)

        # Save the sketch to a file
        sketch_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'sketch.png')
        cv2.imwrite(sketch_filename, sketch)

        return redirect(url_for('show_sketch', filename='sketch.png'))

@app.route('/show_sketch/<filename>')
def show_sketch(filename):
    return render_template('result.html', sketch_url=url_for('static', filename=filename))



if __name__ == '__main__':
    create_table(create_connection())
    app.run(debug=True)
