import mysql.connector
from mysql.connector import pooling
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define connection pool
connection_pool = None

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10,  # Set pool size according to your needs
        pool_reset_session=False,
        host='localhost',
        user='root',
        password='madhu_since_2003',
        database='sms'
    )
    logging.info("Connection pool initialized successfully.")
except mysql.connector.Error as err:
    logging.error(f"Error initializing connection pool: {err.errno} - {err.sqlstate}: {err.msg}")

def get_sql_connection():
    """Get a connection from the connection pool."""
    global connection_pool
    try:
        if connection_pool is None:
            raise Exception("Connection pool not initialized.")
        logging.info(f"Getting MySQL connection from pool. Active connections: {connection_pool._cnx_queue.qsize()}")
        cnx = connection_pool.get_connection()
        logging.info("Connection obtained.")
        return cnx
    except mysql.connector.Error as err:
        logging.error(f"Error getting connection: {err.errno} - {err.sqlstate}: {err.msg}")
        return None
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return None

def close_sql_connection(cnx):
    """Close the connection passed to the function."""
    if cnx is not None and cnx.is_connected():
        try:
            cnx.close()
            logging.info("MySQL connection closed and returned to pool.")
        except mysql.connector.Error as err:
            logging.error(f"Error closing connection: {err.errno} - {err.sqlstate}: {err.msg}")

# Usage example
if __name__ == "__main__":
    connection = get_sql_connection()
    if connection:
        # Perform database operations here
        # For example:
        # cursor = connection.cursor()
        # cursor.execute("SELECT * FROM your_table")
        # result = cursor.fetchall()
        # cursor.close()
        
        close_sql_connection(connection)
