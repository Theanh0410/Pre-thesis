from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import bcrypt

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    from app import mysql, seed_default_rooms  # Import from app.py
    
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the username already exists
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        username_error = None  # Initialize the error message for the username
        email_error = None  # Initialize the error message for the email

        if existing_user:
            # If username exists, set the error message
            if existing_user[1] == username:  # Assuming the username is at index 1 in the user record
                username_error = "Username already exists. Please choose another."
        
        # Check if the email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user_email = cursor.fetchone()
        
        if existing_user_email:
            email_error = "Email already exists. Please choose another."

        # Return JSON response with error messages if any
        if username_error or email_error:
            return render_template('register.html', usernameError=username_error, emailError=email_error)

        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user into the database
        cursor.execute("INSERT INTO users (fullname, username, email, password) VALUES (%s, %s, %s, %s)",
                       (fullname, username, email, hashed_password))
        mysql.connection.commit()
        new_user_id = cursor.lastrowid
        cursor.close()

        seed_default_rooms(new_user_id)

        return redirect(url_for('login.login'))  # Redirect to login page after successful registration

    return render_template('register.html')  # Render the registration form

# Route to check if the username exists
@register_bp.route('/check-username', methods=['POST'])
def check_username():
    from app import mysql
    username = request.json.get('username')
    
    # Check if the username exists in the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return jsonify({"available": False})  # Username exists
    else:
        return jsonify({"available": True})  # Username available

# Route to check if the email exists
@register_bp.route('/check-email', methods=['POST'])
def check_email():
    from app import mysql
    email = request.json.get('email')
    
    # Check if the email exists in the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return jsonify({"available": False})  # Email exists
    else:
        return jsonify({"available": True})  # Email available