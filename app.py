from flask import Flask, render_template, request, redirect, url_for, session, send_file, Response, send_from_directory
from flask_mysqldb import MySQL
from werkzeug import secure_filename, FileWrapper
import MySQLdb.cursors
import mysql.connector
from mysql.connector import Error
import re
from flask_wtf import FlaskForm
from wtforms import FileField, StringField,validators, SelectField, RadioField
from flask_wtf.file import FileAllowed
import os
from pdf2image import convert_from_path

app = Flask(__name__)
app.secret_key = 'te amo'
# Initialize  FLask- SocketIO


conn = MySQLdb.connect("localhost","root","root","kika" )
cursor = conn.cursor()

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'kika'
app.config['UPLOADED_BOOK_DEST'] = 'static/uploads/books'

mysql = MySQL(app)



#actually the featured
@app.route('/home')
def home():
    if 'loggedin' in session:
        cursor.execute("SELECT booklink, title, author from newbooks limit 10")
        conn.commit()
        data = cursor.fetchall() #data from database
        return render_template('home.html', username=session['username'], data=data)
    return redirect(url_for('login'))
@app.route('/home', methods=['GET', 'POST'])
def search():
        if request.method == "POST":
            book = request.form['book']
            # search by author or book
            cursor.execute("SELECT booklink, title, author from newbooks WHERE title LIKE %s OR author LIKE %s", (book, book))
            conn.commit()
            data = cursor.fetchall()

            if len(data) == 0 and book == 'all': 
                cursor.execute("SELECT booklink, title, author from newbooks")
                conn.commit()
                data = cursor.fetchall()
            return render_template('search.html', data=data)
        return render_template('search.html', data=data)




# # @app.route('/home')
# def home():
#     # Check if user is logged in
#     if 'loggedin' in session:
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
#         account = cursor.fetchone()
    
#         return render_template('home.html', username=session['username'], profile_pic = account['profilepic'])
#     return redirect(url_for('login'))




@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg=''

    # Check if "username" and password" POST exist(user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Varaibles for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password) )
        account = cursor. fetchone()

        if account:
            # Create session data, we can access this data in other routes

            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']

            # Redirect to home page
            return redirect(url_for('home'))

        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Account doesnt exist or username/password incorrect'

    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/register', methods=['GET','POST'])
def register():
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (in form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        profile_pic = ''
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (username, password, email, profile_pic))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty
        msg = 'Please fill out the form!'

    return render_template('register.html', msg=msg)




@app.route('/profile', methods=['GET','POST'])
def profile():

    # Check if user is logged in. redirect if not
    if  not 'loggedin' in session:
        return redirect(url_for('login'))

    # WE need all the account info
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()

   

    return render_template('profile.html', account=account)




# This is the library Page
@app.route('/library')
def ulibrary():
    if 'loggedin' in session:
        cursor.execute('SELECT booklink, title, author, bookpage from newbooks WHERE uploader = %s', ( session['username'],))
        conn.commit()
        data = cursor.fetchall() #data from database
        return render_template('library.html', username=session['username'], data=data)
    return redirect(url_for('login'))
@app.route('/library', methods=['GET','POST'])
def library(msg=''):
    if not 'loggedin' in session:
        return redirect(url_for('login'))

    if request.method == "POST":
    
        title = request.form['title']
        author = request.form['author']
        f = request.files['book']
        booklink = secure_filename(f.filename)
        f.save('static/uploads/books/' + booklink)
        username = session['username']
        pages = convert_from_path('static/uploads/books/'+ booklink)
        bookpage = booklink + '.jpg'
        page = pages[0]
        page.save('static/uploads/books/' + bookpage, 'JPEG')

        try:
            cursor.execute('INSERT INTO newbooks VALUES (NULL, %s, %s, %s,%s,%s)', (booklink, title, author, username, bookpage))
            # mysql.connection.commit()
            # cursor.execute('UPDATE newbooks SET bookpage = %s WHERE booklink = %s', (bookpage, booklink))
            # cursor.execute('UPDATE accounts SET profilepic = %s WHERE id = %s', (pic_name, session['id']))
            mysql.connection.commit()
            return render_template('library.html', msg='Upload successful')
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print(e)
            return e
        
    return render_template('library.html', msg=msg)




@app.route('/search/<filename>', methods= ['POST', 'GET'])
def download(filename):

    # Takes in requests from the html file.
    title = request.args['title']
    author = request.args['author']

    return send_from_directory(directory=app.config['UPLOADED_BOOK_DEST'], 
    filename=filename, as_attachment=True, attachment_filename=filename)

@app.route('/update', methods= ['POST', 'GET'])
def update():
    msg=''
    # Connect to database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()

    if request.method=='POST':
        # IF password field is filled
        if 'password' in request.form:
            # If password and confirm password are the same update password
            if request.form['password'] == request.form['confirm-password']:
                # Updating the database
                msg = ''
                password = request.form['password']
                cursor.execute('UPDATE accounts SET password = %s WHERE id= %s', (password, session['id']))
                mysql.connection.commit()
                print('Authentication success')
                print(request.form)
                
            # Password and Confirm password are different
            else:
                msg = 'Passwords are not the same'
                print(request.form)
        # If a file has been uploaded
        if 'profile-photo' in request.files:
            # Pick file from request
            f = request.files['profile-photo']
            # Saves to static/uploads/images with username.jpg
            pic_name = session['username'] + '.jpg'
            f.save('static/uploads/images/' + pic_name)
            # Adds the profilepic link to database
            cursor.execute('UPDATE accounts SET profilepic = %s WHERE id = %s', (pic_name, session['id']))
            mysql.connection.commit()


            # Upload to the server, send link to the database


    return render_template('update.html', msg=msg)



        



# @app.before_request
# def before_request():
#     if request.args.password != request.args.confirm-password:
#         redirect(url_for('update', msg="Passwords don't match"))
#     else:
#         pass


if __name__ == '__main__':
    app.run(debug=True)

# # end point for inserting data dynamicaly in the database
# @app.route('/insert', methods=['GET', 'POST'])
# def insert():
#     if request.method == "POST":
#         book = request.form['book']
#         author = request.form['author']
#         cursor.execute("INSERT INTO Book (name, author) Values (%s, %s)", (book, author))
#         conn.commit()
#         return redirect("http://localhost:5000/search", code=302)
#     return render_template('insert.html')

