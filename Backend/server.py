from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from sql_connection import get_sql_connection, close_sql_connection
import products_dao
from products_dao import get_product_price
import orders_dao
from orders_dao import insert_order
import uom_dao
import stock_dao
from payments_dao import PaymentsDAO
import logging
from logging.handlers import RotatingFileHandler
import datetime
app = Flask(__name__)

# Enable CORS with specific settings
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

# Configure logging for better clarity and debugging
# Configure logging
# Create a logger for the Flask app
logger = logging.getLogger('flask_app')
logger.setLevel(logging.INFO)

# Create handlers: one for the log file and one for the console
file_handler = RotatingFileHandler('flask_app.log', maxBytes=10000, backupCount=1)  # Log to file (rotation enabled)
console_handler = logging.StreamHandler()  # Log to console (VSCode terminal)

# Create a logging format that matches typical Flask output
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# Apply formatter to both handlers
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set logger to propagate messages to Flask's default logger (for consistency)
app.logger.handlers = logger.handlers
app.logger.setLevel(logging.INFO)
# Helper function for error responses
def error_response(message, status_code=500):
    """Create a JSON error response."""
    return jsonify({"error": message}), status_code

def validate_fields(request_payload, required_fields):
    """Check if all required fields are present in the request payload."""
    for field in required_fields:
        if field not in request_payload:
            return error_response(f'{field.replace("_", " ").title()} is required', 400)
    return None

@app.before_request
def before_request():
    """Connect to the database before each request."""
    app.config['db_connection'] = get_sql_connection()
    app.logger.info("Database connection established.")

@app.teardown_request
def teardown_request(exception):
    """Close the database connection after each request."""
    connection = app.config.get('db_connection')
    if connection:
        connection.close()
        app.logger.info("Database connection closed.")

# GET UOMs
@app.route('/getUOMs', methods=['GET'])
@cross_origin()
def get_uoms():
    """Fetch all Units of Measurement (UOMs)."""
    try:
        connection = app.config['db_connection']
        response = uom_dao.get_uoms(connection)
        return jsonify(response), 200
    except Exception as e:
        app.logger.error(f"Error fetching UOMs: {str(e)}")
        return error_response(str(e))

# CHECK Stock
@app.route('/checkStock', methods=['POST'])
@cross_origin()
def check_stock():
    try:
        request_payload = request.get_json()
        
        if 'order_details' not in request_payload:
            return error_response('Order details are required to check stock', 400)

        connection = app.config['db_connection']
        stock_check_results = []
        
        added_products = set()
        
        for item in request_payload['order_details']:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            if not product_id or quantity is None:
                return error_response('Both product_id and quantity are required for stock checking', 400)
            
            if product_id in added_products:
                continue
            
            added_products.add(product_id)
            available_stock = stock_dao.get_stock_by_product_id(connection, product_id)
            
            if available_stock is None:
                stock_check_results.append({
                    'product_id': product_id,
                    'available': False,
                    'message': 'Product not found'
                })
            elif available_stock >= quantity:
                stock_check_results.append({
                    'product_id': product_id,
                    'available': True,
                    'available_stock': available_stock
                })
            else:
                stock_check_results.append({
                    'product_id': product_id,
                    'available': False,
                    'message': f'Insufficient stock. Available: {available_stock}, Required: {quantity}'
                })

        return jsonify(stock_check_results), 200

    except Exception as e:
        app.logger.error(f"Error checking stock: {str(e)}")
        return error_response('An error occurred while checking stock.', 500)

@app.route('/getProducts', methods=['GET'])
@cross_origin()
def get_products():
    connection = get_sql_connection()
    if connection:
        try:
            products = products_dao.get_all_products(connection)  # Pass the connection here
            return jsonify(products)  # Return the products as JSON
        except Exception as e:
            logging.error(f"Error retrieving products: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            close_sql_connection(connection)  # Close the connection
    else:
        return jsonify({'error': 'Failed to connect to database'}), 500

@app.route('/getProduct/<int:product_id>', methods=['GET'])
@cross_origin()
def get_product_by_id(product_id):
    """Fetch a single product by its ID along with stock information."""
    app.logger.info(f"Fetching product with ID: {product_id}")

    try:
        with get_sql_connection() as connection:  # Use the context manager
            if connection is None:
                app.logger.error("Could not establish a database connection.")
                return jsonify({'error': "Could not establish a database connection."}), 500

            product = products_dao.fetch_product_by_id(connection, product_id)  # Call the renamed function
            app.logger.info(f"Product fetched: {product}")

            if product.get('status') == 'fail':
                app.logger.warning(f"Product not found for ID: {product_id}")
                return jsonify({'error': product['message']}), 404
            else:
                product_data = {
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'uom_id': product['uom_id'],
                    'price_per_unit': product['price_per_unit'],
                    'quantity_in_stock': product['quantity_in_stock'],
                    'barcode': product['barcode'],
                    'uom_name': product['uom_name']
                }
                return jsonify(product_data), 200
    except Exception as e:
        app.logger.error(f"Error fetching product by ID {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


#insert Order

@app.route('/insertOrder', methods=['POST'])
@cross_origin()
def insert_order():
    try:
        request_payload = request.get_json()
        app.logger.info(f"Received payload for order: {request_payload}")

        if 'order_details' not in request_payload or not isinstance(request_payload['order_details'], list):
            return error_response('Order details are required and should be a list', 400)

        connection = app.config['db_connection']
        order_id = orders_dao.insert_order(connection, request_payload)

        added_products = set()

        for item in request_payload['order_details']:
            product_id = item.get('product_id')
            quantity = item.get('quantity')

            # Get product price for the order
            price = get_product_price(connection, product_id) 

            if price is None:
                app.logger.error(f"Product ID {product_id} not found.")
                return error_response('Product not found', 400)

            # Update stock if the product is valid
            if product_id in added_products:
                continue

            added_products.add(product_id)

            if product_id and quantity:
                stock_dao.update_stock(connection, product_id, -quantity)

        return jsonify({'message': 'Order added successfully', 'order_id': order_id}), 201

    except Exception as e:
        app.logger.error(f"Error inserting order: {str(e)}")
        return error_response('An error occurred while inserting the order. Please check the details and try again.', 500)

#Update Product
@app.route('/updateProduct/<int:product_id>', methods=['PUT'])
@cross_origin()
def update_product(product_id):
    """Update an existing product, including barcode if provided."""    
    request_payload = request.get_json()

    required_fields = ['product_name', 'uom_id', 'price_per_unit']
    validation_error = validate_fields(request_payload, required_fields)
    if validation_error:
        return validation_error

    try:
        connection = app.config['db_connection']
        
        # Check if the product exists
        product = products_dao.fetch_product_by_id(connection, product_id)
        if not product:
            return error_response('Product not found', 404)

        # Update the product
        update_result = products_dao.update_product(product_id, request_payload)
        request_payload = request.get_json()
        app.logger.info(f"Received payload: {request_payload}")

        
        if update_result['status'] == 'success':
            # Update the stock if quantity_in_stock is provided
            if 'quantity_in_stock' in request_payload:
                stock_dao.update_stock(connection, product_id, request_payload['quantity_in_stock'])
            return jsonify({'message': 'Product updated successfully'}), 200
        else:
            return error_response(update_result['message'], 400)

    except Exception as e:
        app.logger.error(f"Error updating product ID {product_id}: {str(e)}")
        return error_response('An error occurred while updating the product. Please try again.', 500)
    finally:
        connection.close()  # Ensure the connection is closed


# DELETE Product
@app.route('/deleteProduct/<int:product_id>', methods=['DELETE'])
@cross_origin()
def delete_product(product_id):
    """Delete a product by ID along with its stock information."""
    try:
        connection = app.config['db_connection']
        
        deleted_id = products_dao.delete_product(connection, product_id)
        
        if deleted_id:
            stock_deleted = stock_dao.delete_stock_by_product_id(connection, product_id)
            
            if stock_deleted:
                return jsonify({'message': f'Product with ID {deleted_id} and its stock deleted successfully'}), 200
            else:
                app.logger.warning(f'No stock found for product ID {product_id}.')
                return jsonify({'message': f'Product with ID {deleted_id} deleted, but no associated stock found.'}), 200
        
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        app.logger.error(f"Error deleting product ID {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()  # Ensure the connection is closed


# GET Stock
@app.route('/getStock', methods=['GET'])
@cross_origin()
def get_stock():
    """Fetch current stock information."""
    try:
        connection = app.config['db_connection']
        stock_data = stock_dao.get_stock(connection)
        return jsonify(stock_data), 200
    except Exception as e:
        app.logger.error(f"Error fetching stock: {str(e)}")
        return error_response(str(e))

# UPDATE Stock
@app.route('/updateStock/<int:product_id>', methods=['PUT'])
@cross_origin()
def update_stock(product_id):
    """Update stock for a product."""  
    request_payload = request.get_json()
    
    if 'quantity_in_stock' not in request_payload:
        return error_response('Quantity in stock is required to update', 400)

    try:
        connection = app.config['db_connection']
        
        updated = stock_dao.update_stock(connection, product_id, request_payload['quantity_in_stock'])
        
        if updated:
            return jsonify({'message': 'Stock updated successfully'}), 200
        else:
            return error_response('Failed to update stock, product may not exist', 404)

    except Exception as e:
        app.logger.error(f"Error updating stock for product ID {product_id}: {str(e)}")
        return error_response('An error occurred while updating the stock. Please try again.', 500)

# GET Product by Barcode
@app.route('/getProductByBarcode', methods=['GET'])
@cross_origin()
def get_product_by_barcode_route():
    """Get product details based on barcode."""
    try:
        barcode = request.args.get('barcode')  # Get barcode from query parameters
        
        if not barcode:
            return error_response('Barcode is required', 400)

        connection = app.config['db_connection']

        # Fetch product details based on the barcode
        product = products_dao.get_product_by_barcode(barcode)
        
        if product:
            return jsonify(product), 200
        else:
            return error_response('Product not found for the given barcode', 404)
    
    except Exception as e:
        app.logger.error(f"Error fetching product by barcode: {str(e)}")
        return error_response('An error occurred while fetching product details. Please try again.', 500)
@app.route('/getAllOrders', methods=['GET'])
@cross_origin()
def get_all_orders():
    """Fetch all order information."""
    try:
        connection = app.config['db_connection']  # Get the database connection
        orders_data = orders_dao.get_all_orders(connection)  # Fetch orders using the DAO
        
        # Assuming orders_data is a list of dicts containing order_id and other fields
        return jsonify(orders_data), 200  # Return the orders as JSON with a 200 status code
    except Exception as e:
        app.logger.error(f"Error fetching orders: {str(e)}")  # Log the error
        return error_response(str(e))  # Return an error response


#insert product
@app.route('/insertProduct', methods=['POST'])
@cross_origin()
def insert_product():
    """Insert a new product along with its stock."""
    request_payload = request.get_json()
    app.logger.info(f"Received payload for insert product: {request_payload}")

    # Validate required fields
    required_fields = ['product_name', 'uom_id', 'price_per_unit', 'quantity_in_stock']
    validation_error = validate_fields(request_payload, required_fields)
    if validation_error:
        return validation_error

    try:
        connection = app.config['db_connection']

        # Insert the product into the products table
        product_id = products_dao.insert_product(connection, request_payload)

        # Update the stock table with the initial quantity
        stock_dao.update_stock(connection, product_id, request_payload['quantity_in_stock'])

        return jsonify({'message': 'Product inserted successfully', 'product_id': product_id}), 201

    except Exception as e:
        app.logger.error(f"Error inserting product: {str(e)}")
        return error_response('An error occurred while inserting the product. Please try again.', 500)

    finally:
        connection.close()  # Ensure the connection is closed


@app.route('/processPayment', methods=['POST'])
@cross_origin()
def process_payment():
    request_payload = request.get_json()
    app.logger.info(f"Received payment payload: {request_payload}")

    # Validate required fields
    required_fields = ['payment_mode', 'order_id', 'customer_name', 'grandTotal', 'order_details']
    validation_error = validate_fields(request_payload, required_fields)
    if validation_error:
        return validation_error

    payment_mode = request_payload['payment_mode']  
    order_id = request_payload['order_id']
    customer_name = request_payload['customer_name']
    grand_total = request_payload['grandTotal']
    order_details = request_payload['order_details']

    try:
        connection = app.config['db_connection']
        payments_dao = PaymentsDAO(connection)

        app.logger.info(f"Processing payment for order ID: {order_id} with mode: {payment_mode}") 

        # Log order details for reference
        app.logger.info(f"Order details: {order_details}")

        if payment_mode.lower() == 'upi':
            success = validate_upi_payment(request_payload)
            if success:
                payment_id = payments_dao.insert_payment(order_id, payment_mode, grand_total, customer_name)
                payments_dao.update_payment_status(payment_id, 'Paid')

                app.logger.info(f"UPI payment successful for order ID: {order_id}, payment ID: {payment_id}")
                return jsonify({'message': 'UPI payment successful, order confirmed.', 'payment_id': payment_id}), 200

            else:
                app.logger.warning(f"UPI payment failed for order ID: {order_id}")
                return error_response('UPI payment failed, please try again.', 400)

        elif payment_mode.lower() == 'cash':
            payment_id = payments_dao.insert_payment(order_id, payment_mode, grand_total, customer_name)
            payments_dao.update_payment_status(payment_id, 'Paid')

            app.logger.info(f"Cash payment confirmed for order ID: {order_id}, payment ID: {payment_id}")
            return jsonify({'message': 'Cash payment confirmed, order completed.', 'payment_id': payment_id}), 200

        else:
            app.logger.warning(f"Invalid payment mode: {payment_mode}")
            return error_response('Invalid payment mode provided.', 400)

    except Exception as e:
        app.logger.error(f"Error processing payment: {str(e)}")
        return error_response('An error occurred while processing the payment. Please try again.', 500)

def validate_upi_payment(request_payload):
    # Placeholder function for UPI payment validation
    return True  # Always returns True for testing

#payment details route
@app.route('/payment/<payment_id>', methods=['GET'])
@cross_origin()
def get_payment_details(payment_id):
    try:
        connection = app.config['db_connection']
        payments_dao = PaymentsDAO(connection)

        payment_details = payments_dao.get_payment_details(payment_id)
        if payment_details:
            return jsonify({'payment_details': payment_details}), 200
        else:
            return error_response('Payment not found.', 404)

    except Exception as e:
        app.logger.error(f"Error retrieving payment details: {str(e)}")
        return error_response('An error occurred while retrieving payment details. Please try again.', 500)



if __name__ == '__main__':
    app.run(debug=True, port=3000)
