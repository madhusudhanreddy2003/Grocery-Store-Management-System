from datetime import datetime
from sql_connection import get_sql_connection
import stock_dao  # Import stock_dao to manage stock
import logging  # Import logging for better error tracking
from products_dao import get_product_price


def insert_order(connection, order):
    """Insert a new order and order details, and update stock."""
    logging.debug("Inserting Order: %s", order)

    if 'customer_name' not in order or 'order_details' not in order:
        logging.error("Required fields are missing in the order: %s", order)
        raise ValueError("Missing required fields")

    # Map grandTotal to total
    order['total'] = float(order.pop('grandTotal', 0))

    if not order['order_details']:
        logging.error("Order details are missing or invalid: %s", order)
        raise ValueError("Invalid order details")

    with connection.cursor() as cursor:
        try:
            order_query = ("INSERT INTO orders (customer_name, total, datetime) VALUES (%s, %s, %s)")
            order_data = (order['customer_name'], order['total'], datetime.now())
            cursor.execute(order_query, order_data)
            order_id = cursor.lastrowid
            
            order_details_query = ("INSERT INTO order_details "
                                   "(order_id, product_id, quantity, total_price) "
                                   "VALUES (%s, %s, %s, %s) "
                                   "ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity), "
                                   "total_price = total_price + VALUES(total_price)")

            order_details_data = []
            for order_detail_record in order['order_details']:
                product_id = int(order_detail_record.get('product_id', 0))  # Use 'product_id'
                quantity = float(order_detail_record['quantity'])  # Use 'quantity'
                
                # Fetch product price
                product_price = get_product_price(connection, product_id)
                total_price = product_price * quantity  # Calculate total price

                if not stock_dao.is_stock_available(connection, product_id, quantity):
                    logging.error("Insufficient stock for product ID: %s", product_id)
                    raise ValueError("Insufficient stock")

                stock_dao.update_stock(connection, product_id, -quantity)
                order_details_data.append((order_id, product_id, quantity, total_price))

            cursor.executemany(order_details_query, order_details_data)
            connection.commit()
            return order_id

        except Exception as e:
            logging.error("Error inserting order: %s", str(e))
            connection.rollback()
            raise  # Propagate the exception

def delete_order(connection, order_id):
    """Delete an order and restore stock."""
    with connection.cursor() as cursor:
        try:
            # Get order details to restore stock
            order_details = get_order_details(connection, order_id)
            for detail in order_details:
                product_id = detail['product_id']
                quantity = detail['quantity']
                stock_dao.increase_stock(connection, product_id, quantity)

            # Delete from order_details and orders
            cursor.execute("DELETE FROM order_details WHERE order_id = %s", (order_id,))
            cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))

            connection.commit()
            logging.info("Order with ID %s deleted successfully.", order_id)
            return order_id

        except Exception as e:
            connection.rollback()  # Rollback in case of error
            logging.error("Error deleting order: %s", str(e), exc_info=True)
            return None

def get_order_details(connection, order_id):
    """Fetch order details for a given order."""
    with connection.cursor() as cursor:
        query = ("SELECT order_details.order_id, order_details.quantity, order_details.total_price, "
                 "order_details.product_id, products.product_name, products.price_per_unit "
                 "FROM order_details "
                 "LEFT JOIN products ON order_details.product_id = products.product_id "
                 "WHERE order_details.order_id = %s")

        cursor.execute(query, (order_id,))
        records = cursor.fetchall()

        return [{
            'order_id': record[0],
            'quantity': record[1],
            'total_price': record[2],
            'product_id': record[3],
            'product_name': record[4],
            'price_per_unit': record[5]
        } for record in records]

def get_all_orders(connection):
    """Fetch all orders and their details."""
    with connection.cursor() as cursor:
        query = ("SELECT orders.order_id, orders.customer_name, orders.total, orders.datetime, "
                 "order_details.product_id, order_details.quantity, order_details.total_price, "
                 "products.product_name, products.price_per_unit "
                 "FROM orders "
                 "LEFT JOIN order_details ON orders.order_id = order_details.order_id "
                 "LEFT JOIN products ON order_details.product_id = products.product_id")

        cursor.execute(query)
        rows = cursor.fetchall()

        response = {}
        for row in rows:
            order_id, customer_name, total, dt, product_id, quantity, total_price, product_name, price_per_unit = row
            if order_id not in response:
                response[order_id] = {
                    'order_id': order_id,
                    'customer_name': customer_name,
                    'total': total,
                    'datetime': dt.strftime("%Y-%m-%d %H:%M:%S"),
                    'order_details': []
                }
            if product_id:
                response[order_id]['order_details'].append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'total_price': total_price,
                    'product_name': product_name,
                    'price_per_unit': price_per_unit
                })

        return list(response.values())

if __name__ == '__main__':
    connection = get_sql_connection()
    logging.basicConfig(level=logging.DEBUG)
    try:
        orders = get_all_orders(connection)
        logging.info("Retrieved all orders: %s", orders)
    except Exception as e:
        logging.error("Failed to retrieve orders: %s", str(e), exc_info=True)
    finally:
        connection.close()
