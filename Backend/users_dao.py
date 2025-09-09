import bcrypt
from sql_connection import get_sql_connection

# Register a new user (admin or cashier)
def register_user(connection, username, password, role):
    cursor = connection.cursor()
    
    # Hash the password before storing it
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, hashed_password, role))
    connection.commit()

    return cursor.lastrowid

# Verify login credentials and return the user role
def login_user(connection, username, password):
    cursor = connection.cursor()
    
    # Check if the user exists
    query = "SELECT password, role FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    if user:
        stored_password, role = user
        # Check if the password is correct
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return {'role': role}  # Return the role if login is successful
        else:
            return None  # Invalid password
    return None  # User not found
