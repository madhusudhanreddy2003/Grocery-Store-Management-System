from typing import Dict, Union, List
import logging
from sql_connection import get_sql_connection  # Use your connection from sql_connection.py
import mysql.connector
import decimal  # Import decimal to handle Decimal type
from stock_dao import get_initial_stock

def product_exists(connection, barcode: str) -> bool:
    """Check if a product with the given barcode already exists."""
    cursor = connection.cursor()
    try:
        query = "SELECT COUNT(*) FROM products WHERE barcode = %s"
        cursor.execute(query, (barcode,))
        count = cursor.fetchone()[0]
        return count > 0  # Return True if a product exists, otherwise False
    finally:
        cursor.close()

def insert_product(connection, product_data: Dict) -> Dict[str, str]:
    """Insert a new product and return its ID, or update if it already exists."""
    try:
        # Logging the incoming product data for debugging purposes
        logging.info(f"Received product data: {product_data}")

        # Validate the presence of required fields
        required_fields = ['product_name', 'price_per_unit', 'uom_id', 'quantity_in_stock']
        for field in required_fields:
            if field not in product_data or product_data[field] is None:
                return {'status': 'fail', 'message': f'Missing or invalid {field} in product data'}

        # Additional validation for product_name
        product_name = product_data['product_name'].strip()
        if product_name == '':
            return {'status': 'fail', 'message': 'Product name cannot be empty.'}

        with connection.cursor() as cursor:
            # Check if product already exists
            cursor.execute("SELECT product_id FROM products WHERE product_name = %s AND uom_id = %s",
                           (product_name, product_data['uom_id']))
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
                insert_product_query = """
                INSERT INTO products (product_name, price_per_unit, uom_id)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_product_query, (product_name, product_data['price_per_unit'], product_data['uom_id']))
                new_product_id = cursor.lastrowid
                logging.info(f"Inserted new product with ID: {new_product_id}")

            connection.commit()  # Commit changes
            return {'status': 'success', 'product_id': existing_product[0] if existing_product else new_product_id}

    except mysql.connector.Error as db_err:
        connection.rollback()
        logging.error(f"Database error inserting product: {str(db_err)}")
        return {'status': 'fail', 'message': 'Database error occurred'}

    except Exception as e:
        connection.rollback()
        logging.error(f"General error inserting product: {str(e)}")
        return {'status': 'fail', 'message': str(e)}

def update_stock(product_id: int, quantity: int) -> Dict[str, str]:
    """Update the stock for a given product."""
    try:
        connection = get_sql_connection()  # Get connection
        with connection.cursor() as cursor:
            update_stock_query = """
            UPDATE stock 
            SET quantity_in_stock = %s 
            WHERE product_id = %s
            """
            cursor.execute(update_stock_query, (quantity, product_id))
            if cursor.rowcount > 0:
                connection.commit()
                logging.info(f"Stock updated successfully for product ID {product_id}")
                return {'status': 'success', 'message': f'Stock updated for product ID {product_id}'}
            else:
                logging.warning(f"No stock entry found for product ID {product_id}.")
                return {'status': 'fail', 'message': 'No stock entry found for this product.'}
    except Exception as e:
        logging.error(f"Error updating stock for product ID {product_id}: {str(e)}")
        return {'status': 'fail', 'message': str(e)}
    finally:
        connection.close()  # Close the connection here

def update_product(product_id: int, product_data: Dict) -> Dict[str, str]:
    """Update an existing product with the given data."""
    connection = get_sql_connection()
    cursor = connection.cursor()
    try:
        fields_to_update = []
        params = []

        # Collect fields to update
        if 'product_name' in product_data:
            fields_to_update.append("product_name = %s")
            params.append(product_data['product_name'])
        if 'price_per_unit' in product_data:
            fields_to_update.append("price_per_unit = %s")
            params.append(product_data['price_per_unit'])
        if 'uom_id' in product_data:
            fields_to_update.append("uom_id = %s")
            params.append(product_data['uom_id'])
        if 'barcode' in product_data:
            fields_to_update.append("barcode = %s")
            params.append(product_data['barcode'])

        if 'quantity_in_stock' in product_data:
            # Handle stock update separately if needed
            return update_stock(product_id, product_data['quantity_in_stock'])

        if not fields_to_update:
            logging.error("No fields provided to update for product")
            return {'status': 'fail', 'message': 'No fields to update'}

        params.append(product_id)

        update_query = f"""
            UPDATE products SET {', '.join(fields_to_update)} WHERE product_id = %s
        """
        logging.info(f"Executing query: {update_query} with params: {params}")

        cursor.execute(update_query, tuple(params))
        connection.commit()

        return {'status': 'success' if cursor.rowcount > 0 else 'fail'}
    except Exception as e:
        logging.error(f"Error updating product {product_id}: {str(e)}")
        connection.rollback()
        return {'status': 'fail', 'message': str(e)}
    finally:
        cursor.close()
        connection.close()


def fetch_product_by_id(connection, product_id: int) -> Dict[str, str]:
    """Fetch a product by its ID."""
    connection = get_sql_connection()
    cursor = connection.cursor()
    try:
        query = """
            SELECT p.product_id, p.product_name, p.price_per_unit, p.barcode, p.uom_id, u.uom_name, s.quantity_in_stock
            FROM products p
            LEFT JOIN uom u ON p.uom_id = u.uom_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.product_id = %s
        """
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()

        if result is None:
            return {'status': 'fail', 'message': 'Product not found'}

        return {
            'product_id': result[0],
            'product_name': result[1],
            'price_per_unit': float(result[2]) if isinstance(result[2], decimal.Decimal) else result[2],
            'barcode': result[3],  # Include barcode in response
            'uom_id': result[4],
            'uom_name': result[5] if result[5] is not None else 'N/A',
            'quantity_in_stock': result[6] if result[6] is not None else 0
        }
    except Exception as e:
        logging.error(f"Error fetching product by ID {product_id}: {str(e)}")
        return {'status': 'fail', 'message': str(e)}
    finally:
        cursor.close()
        connection.close()

def get_product_by_barcode(barcode: str) -> Dict[str, Union[str, int]]:
    """Fetch a product by its barcode."""
    connection = get_sql_connection()
    cursor = connection.cursor()
    try:
        query = """
            SELECT p.product_id, p.product_name, p.price_per_unit, p.barcode, u.uom_name, s.quantity_in_stock
            FROM products p
            LEFT JOIN uom u ON p.uom_id = u.uom_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            WHERE p.barcode = %s
        """
        cursor.execute(query, (barcode,))
        result = cursor.fetchone()

        if result is None:
            return {'status': 'fail', 'message': 'Product not found'}

        return {
            'product_id': result[0],
            'product_name': result[1],
            'price_per_unit': float(result[2]) if isinstance(result[2], decimal.Decimal) else result[2],
            'barcode': result[3],
            'uom_name': result[4] if result[4] is not None else 'N/A',
            'quantity_in_stock': result[5] if result[5] is not None else 0
        }
    except Exception as e:
        logging.error(f"Error fetching product by barcode {barcode}: {str(e)}")
        return {'status': 'fail', 'message': str(e)}
    finally:
        cursor.close()
        connection.close()

def get_all_products(connection) -> List[Dict[str, Union[str, int]]]:
    """Fetch all products along with their stock and UOM details."""
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.price_per_unit, p.barcode, u.uom_name, s.quantity_in_stock
            FROM products p
            LEFT JOIN uom u ON p.uom_id = u.uom_id
            LEFT JOIN stock s ON p.product_id = s.product_id
        """)
        products = []
        for row in cursor.fetchall():
            products.append({
                'product_id': row[0],
                'product_name': row[1],
                'price_per_unit': float(row[2]) if isinstance(row[2], decimal.Decimal) else row[2],
                'barcode': row[3],
                'uom_name': row[4],
                'quantity_in_stock': row[5] if row[5] is not None else 0
            })
        return products
    except Exception as e:
        logging.error(f"Error fetching all products: {str(e)}")
        return []
    finally:
        cursor.close()

def get_product_price(connection, product_id: int) -> Union[float, None]:
    """Fetch the price of a product by its ID."""
    connection = get_sql_connection()
    cursor = connection.cursor()
    try:
        query = "SELECT price_per_unit FROM products WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()
        
        if result is None:
            return None  # or raise an exception if preferred
        return float(result[0]) if isinstance(result[0], decimal.Decimal) else result[0]
        
    except Exception as e:
        logging.error(f"Error fetching product price for ID {product_id}: {str(e)}")
        return None  # or handle as needed
    finally:
        cursor.close()
        connection.close()
def delete_product(connection, product_id: int) -> Dict[str, str]:
    """Delete a product by its ID."""
    connection = get_sql_connection()  # Get the connection
    try:
        with connection.cursor() as cursor:
            # Delete the product from the products table
            delete_query = "DELETE FROM products WHERE product_id = %s"
            cursor.execute(delete_query, (product_id,))
            connection.commit()  # Commit the changes
            
            if cursor.rowcount > 0:
                logging.info(f"Deleted product with ID: {product_id}")
                return {'status': 'success', 'message': f'Product with ID {product_id} deleted successfully.'}
            else:
                logging.warning(f"No product found with ID: {product_id}")
                return {'status': 'fail', 'message': 'No product found with the given ID.'}
    
    except mysql.connector.Error as db_err:
        connection.rollback()  # Rollback in case of error
        logging.error(f"Database error deleting product ID {product_id}: {str(db_err)}")
        return {'status': 'fail', 'message': 'Database error occurred'}
    
    except Exception as e:
        connection.rollback()  # Rollback in case of any other error
        logging.error(f"General error deleting product ID {product_id}: {str(e)}")
        return {'status': 'fail', 'message': str(e)}
    
    finally:
        connection.close()  # Close the connection
