import logging

def get_uoms(connection):
    """Fetches all units of measurement (UOMs) from the database."""
    response = []
    try:
        with connection.cursor() as cursor:  # Use context manager for cursor
            query = "SELECT uom_id, uom_name FROM uom"
            cursor.execute(query)
            response = [{'uom_id': uom_id, 'uom_name': uom_name} for uom_id, uom_name in cursor]
        logging.info("Retrieved UOMs successfully.")
    except Exception as e:
        logging.error("Error retrieving UOMs: %s", str(e), exc_info=True)  # Log error with traceback
    return response

if __name__ == '__main__':
    from sql_connection import get_sql_connection

    connection = get_sql_connection()
    logging.basicConfig(level=logging.DEBUG)  # Set logging level
    try:
        uoms = get_uoms(connection)
        logging.info("Retrieved UOMs: %s", uoms)
    except Exception as e:
        logging.error("Failed to retrieve UOMs: %s", str(e), exc_info=True)
    finally:
        connection.close()  # Ensure connection is closed
