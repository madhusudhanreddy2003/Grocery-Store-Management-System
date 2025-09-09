import uuid

class PaymentsDAO:
    def __init__(self, connection):
        self.connection = connection

    # Insert payment method
    def insert_payment(self, order_id, payment_mode, grand_total=None, customer_name=None):
        try:
            payment_id = str(uuid.uuid4())  # Generate a unique payment ID
            payment_status = 'Pending'  # Initial payment status can be set to 'Pending'
            
            # Modified to insert grand_total and customer_name
            insert_query = """
                INSERT INTO payments (payment_id, order_id, payment_mode, payment_status, grand_total, customer_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            with self.connection.cursor() as cursor:
                cursor.execute(insert_query, (payment_id, order_id, payment_mode, payment_status, grand_total, customer_name))
                self.connection.commit()  # Commit the transaction

            return payment_id  # Return the generated payment ID

        except Exception as e:
            raise e  # Raise the exception for error handling in the calling function

    # Update payment status method
    def update_payment_status(self, payment_id, new_status):
        try:
            with self.connection.cursor() as cursor:
                update_query = """
                    UPDATE payments
                    SET payment_status = %s
                    WHERE payment_id = %s
                """
                cursor.execute(update_query, (new_status, payment_id))
                if cursor.rowcount == 0:
                    raise ValueError("Payment ID not found.")

                self.connection.commit()  # Commit the transaction

        except Exception as e:
            raise e  # Raise the exception for error handling in the calling function

    # Get payment details method
    def get_payment_details(self, payment_id):
        try:
            with self.connection.cursor() as cursor:
                select_query = """
                    SELECT * FROM payments
                    WHERE payment_id = %s
                """
                cursor.execute(select_query, (payment_id,))
                payment_details = cursor.fetchone()  # Fetch a single record

                return payment_details  # Returns all columns including payment_mode

        except Exception as e:
            raise e  # Raise the exception for error handling in the calling function
