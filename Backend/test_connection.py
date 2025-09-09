from products_dao import get_product_price

test_product_id = 10  # Replace with a valid product ID from your database
price = get_product_price(test_product_id)
print(f"Price for product ID {test_product_id}: {price}")
