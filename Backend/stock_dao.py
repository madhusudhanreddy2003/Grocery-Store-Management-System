import logging
from typing import Dict, Optional, List
from sql_connection import get_sql_connection  # Import the connection function
import mysql.connector
from mysql.connector import Error  # Import Error class
def get_initial_stock(uom_id: int) -> int:
    """Determine initial stock based on UOM ID."""
    stock_dict = {1: 80, 2: 50}
    return stock_dict.get(uom_id, 0)  # Default to 0 if uom_id is not found


def insert_or_update_product_with_stock(connection, product_data: Dict, quantity_in_stock: int) -> bool:
    logging.info("Attempting to insert or update product with data: %s", product_data)  # Log the incoming data

    with connection.cursor() as cursor:
        
        try:
            # Check if product already exists
            cursor.execute("SELECT product_id FROM products WHERE product_name = %s AND uom_id = %s",
                           (product_data['product_name'], product_data['uom_id']))
            existing_product = cursor.fetchone()

            if existing_product:
                # Update existing product
                product_id = existing_product[0]
                update_product_query = """
                UPDATE products 
                SET price_per_unit = %s 
                WHERE product_id = %s
                """
                cursor.execute(update_product_query, (product_data['price_per_unit'], product_id))
                logging.info(f"Updated existing product ID: {product_id}")

            else:
                # Insert new product
                logging.info("Inserting new product")
                insert_product_query = """
                INSERT INTO products (product_name, price_per_unit, uom_id) 
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_product_query, (
                    product_data['product_name'],
                    product_data['price_per_unit'],
                    product_data['uom_id']
                ))

                new_product_id = cursor.lastrowid

                # Log confirmation of successful product insert
                logging.info(f"Product inserted successfully. New product ID: {new_product_id}")
                
                if not new_product_id:
                    logging.error("Product insertion failed, no product ID returned.")
                    return False

            connection.commit()  # Commit changes
            return True

        except Error as e:  # Handle mysql.connector errors
            connection.rollback()  # Rollback if there's a database error
            logging.error(f"Database error while inserting or updating product and stock: {str(e)}")
            return False
        except Exception as e:
            connection.rollback()  # Rollback for any other error
            logging.error(f"Unexpected error while inserting or updating product and stock: {str(e)}")
            return False

def get_product_with_stock_by_id(connection, product_id: int) -> Optional[Dict]:
    """Fetch product details along with stock by product ID."""
    cursor = connection.cursor()
    try:
        query = """
        SELECT p.product_id, p.product_name, p.price_per_unit, p.uom_id, s.quantity_in_stock
        FROM products p
        LEFT JOIN stock s ON p.product_id = s.product_id
        WHERE p.product_id = %s
        """
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()

        if result:
            return {
                'product_id': result[0],
                'name': result[1],
                'price_per_unit': result[2],
                'uom_id': result[3],
                'quantity_in_stock': result[4]
            }
        else:
            logging.warning(f"No product found with ID {product_id}.")
            return None

    except Error as e:
        logging.error(f"Database error while fetching product with ID {product_id}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while fetching product with ID {product_id}: {str(e)}")
        return None
    finally:
        cursor.close()


def delete_stock_by_product_id(connection, product_id):
    """Delete stock entry by product ID."""
    cursor = connection.cursor()
    try:
        delete_query = "DELETE FROM stock WHERE product_id = %s"
        cursor.execute(delete_query, (product_id,))
        connection.commit()
        return cursor.rowcount > 0  # Returns True if a row was deleted
    except Exception as e:
        connection.rollback()
        logging.error(f"Error deleting stock for product ID {product_id}: {str(e)}")
        return False
    finally:
        cursor.close()


def update_stock(connection, product_id: int, quantity: int) -> Dict[str, str]:
    """Update the stock for a given product."""
    cursor = connection.cursor()
    try:
        # Update stock entry
        update_stock_query = """
        UPDATE stock 
        SET quantity_in_stock = quantity_in_stock + %s 
        WHERE product_id = %s
        """
        cursor.execute(update_stock_query, (quantity, product_id))
        if cursor.rowcount > 0:
            connection.commit()
            logging.info(f"Stock updated successfully for product ID {product_id}")
            return {'status': 'success'}
        else:
            logging.warning(f"No stock entry found for product ID {product_id}.")
            return {'status': 'fail', 'message': 'No stock entry found for this product.'}
    except Error as e:
        connection.rollback()  # Rollback on database error
        logging.error(f"Database error while updating stock for product ID {product_id}: {str(e)}")
        return {'status': 'fail', 'message': 'Database error occurred.'}
    except Exception as e:
        connection.rollback()  # Rollback on any other error
        logging.error(f"Unexpected error while updating stock for product ID {product_id}: {str(e)}")
        return {'status': 'fail', 'message': str(e)}
    finally:
        cursor.close()


def get_stock(connection) -> List[Dict]:
    """Fetch current stock information."""
    with connection.cursor() as cursor:
        try:
            query = """
            SELECT s.product_id, p.product_name, s.quantity_in_stock
            FROM stock s
            JOIN products p ON s.product_id = p.product_id
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return [
                {
                    'product_id': result[0],
                    'product_name': result[1],
                    'quantity_in_stock': result[2]
                }
                for result in results
            ]
        except Error as e:
            logging.error(f"Database error while fetching stock: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error while fetching stock: {str(e)}")
            return []
def decrease_stock(connection, product_id: int, quantity: int) -> bool:
    """Decrease the stock for a given product."""
    with connection.cursor() as cursor:
        try:
            # Update stock entry
            update_stock_query = """
            UPDATE stock 
            SET quantity_in_stock = quantity_in_stock - %s 
            WHERE product_id = %s AND quantity_in_stock >= %s
            """
            cursor.execute(update_stock_query, (quantity, product_id, quantity))
            
            if cursor.rowcount > 0:
                connection.commit()
                logging.info(f"Stock decreased successfully for product ID {product_id}")
                return True
            else:
                logging.warning(f"Insufficient stock for product ID {product_id} or no entry found.")
                return False
        except Error as e:
            connection.rollback()  # Rollback on database error
            logging.error(f"Database error while decreasing stock for product ID {product_id}: {str(e)}")
            return False
        except Exception as e:
            connection.rollback()  # Rollback on any other error
            logging.error(f"Unexpected error while decreasing stock for product ID {product_id}: {str(e)}")
            return False
def is_stock_available(connection, product_id: int, requested_quantity: int) -> bool:
    """Check if the requested quantity of the product is available in stock."""
    with connection.cursor() as cursor:
        try:
            # Fetch the current quantity in stock for the given product_id
            cursor.execute("SELECT quantity_in_stock FROM stock WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()
            
            if result:
                current_stock = result[0]
                return current_stock >= requested_quantity  # Check if requested quantity is available
            else:
                logging.warning(f"No stock entry found for product ID {product_id}.")
                return False
            
        except Error as e:
            logging.error(f"Database error while checking stock availability for product ID {product_id}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error while checking stock availability for product ID {product_id}: {str(e)}")
            return False
def get_stock_by_product_id(connection, product_id: int) -> Optional[int]:
    """Fetch the stock quantity for a given product ID."""
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT quantity_in_stock FROM stock WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            logging.error(f"Database error while fetching stock for product ID {product_id}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error while fetching stock for product ID {product_id}: {str(e)}")
            return None

