from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
import bcrypt

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    from app import mysql  # Import MySQL instance from app.py
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        # Query only by username
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user:  # If user exists
            stored_password_hash = user[4]  # Assuming password is the 5th column in the table (index starts at 0)

            # Check if the password matches the stored hashed password
            try:
                if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                    session['username'] = username  # Store username in session
                    return jsonify({"success": True, "redirect": url_for('home')})  # Redirect to home/dashboard after login
                else:
                    return jsonify({"success": False, "message": 'Invalid password. Please try again.'})
            except Exception as e:
                return jsonify({"success": False, "message": 'Error verifying password. Please try again.'})
        else:
            return jsonify({"success": False, "message": 'User not found. Please register first.'})

    return render_template('login.html')

# Route to check if the username exists
@login_bp.route('/check-username', methods=['POST'])
def check_username():
    from app import mysql
    username = request.json.get('username')
    
    # Check if the username exists in the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return jsonify({"exists": True})  # Username exists
    else:
        return jsonify({"exists": False})  # Username does not exist