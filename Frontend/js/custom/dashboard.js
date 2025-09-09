$(function () {
    // Fetch orders, products, and UOMs when the document is ready
    fetchOrders();
    fetchProducts();
    fetchUOMs();
});


// Function to fetch orders from the backend
function fetchOrders() {
    $.ajax({
        url: `${baseURL}/getAllOrders`,  // API endpoint for fetching all orders
        method: 'GET',
        success: function(data) {
            console.log('Orders:', data); // Debugging line to inspect the API response
            var ordersTableBody = $('#ordersTableBody');
            ordersTableBody.empty();  // Clear existing rows

            if (Array.isArray(data) && data.length > 0) {
                data.forEach(function(order) {
                    // Format datetime to include both date and time
                    var dateTime = new Date(order.datetime);
                    var formattedDate = dateTime.toLocaleDateString(); // Format date
                    var formattedTime = dateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }); // Format time

                    // Get product names and quantities for the current order
                    var productDetails = order.order_details.map(detail => `${detail.product_name} (Qty: ${detail.quantity})`).join(', ');

                    // Append each order to the table
                    ordersTableBody.append(`
                        <tr class="order-row">
                            <td>${order.order_id}</td>
                            <td>${order.customer_name}</td>
                            <td>${formattedDate}</td>
                            <td>${formattedTime}</td>
                            <td>${productDetails}</td>
                            <td>${parseFloat(order.total).toFixed(2)} Rs</td> <!-- Ensure total is formatted correctly -->
                        </tr>
                    `);
                });
            } else {
                ordersTableBody.append('<tr><td colspan="6">No orders found.</td></tr>');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching orders:', error);
            console.error('XHR:', xhr); // Log the full XHR object for debugging
            var ordersTableBody = $('#ordersTableBody');
            // Optionally show an error message in the table
            ordersTableBody.append('<tr><td colspan="6">Failed to fetch orders. Please try again later.</td></tr>');
        }
    });
}


// Function to fetch products from the backend
function fetchProducts() {
    $.ajax({
        url: `${baseURL}/getProducts`,  // API endpoint for fetching all products
        method: 'GET',
        success: function(data) {
            console.log('Products:', data); // Debugging line to inspect the API response
            var productsTableBody = $('#productsTableBody');
            productsTableBody.empty();  // Clear existing rows

            if (Array.isArray(data) && data.length > 0) {
                data.forEach(function(product) {
                    // Append each product to the table
                    productsTableBody.append(`
                        <tr class="product-row">
                            <td>${product.product_id}</td>
                            <td>${product.product_name}</td>
                            <td>${product.uom_name}</td>
                            <td>${parseFloat(product.price_per_unit).toFixed(2)} Rs</td> <!-- Ensure price is formatted correctly -->
                            <td>${product.quantity_in_stock}</td>
                        </tr>
                    `);
                });
            } else {
                productsTableBody.append('<tr><td colspan="5">No products found.</td></tr>');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching products:', error);
        }
    });
}

// Function to fetch UOMs from the backend
function fetchUOMs() {
    $.ajax({
        url: `${baseURL}/getUOMs`,  // API endpoint for fetching all UOMs
        method: 'GET',
        success: function(data) {
            console.log('UOMs:', data); // Debugging line to inspect the API response
            var uomSelect = $('#uomSelect'); // Assuming you have a select element for UOMs
            uomSelect.empty();  // Clear existing options

            if (Array.isArray(data) && data.length > 0) {
                data.forEach(function(uom) {
                    // Append each UOM as an option
                    uomSelect.append(`<option value="${uom.uom_id}">${uom.uom_name}</option>`);
                });
            } else {
                uomSelect.append('<option disabled>No UOMs found.</option>');
            }
        },
        error: function(xhr, status, error) {
            console.error('Error fetching UOMs:', error);
        }
    });
}
