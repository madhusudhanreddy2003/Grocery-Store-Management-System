// Define your API URLs (baseURL is now from config.js)
const API_URLS = {
    productList: `${baseURL}/getProducts`,
    uomList: `${baseURL}/getUOMs`, // Updated endpoint for UOMs
    productSave: `${baseURL}/insertProduct`,
    productUpdate: (productId) => `${baseURL}/updateProduct/${productId}`, // Added update endpoint
    productDelete: (productId) => `${baseURL}/deleteProduct/${productId}`,
    orderList: `${baseURL}/getAllOrders`,
    orderSave: `${baseURL}/insertOrder`,
};

// Function to call APIs
function callApi(method, url, data, reloadPage = true) {
    $.ajax({
        method: method,
        url: url,
        contentType: 'application/json', // Set the content type to JSON
        data: JSON.stringify(data), // Ensure the data is sent as JSON
        success: function (response) {
            if (reloadPage) {
                window.location.reload(); // Reload the page on successful response
            } else {
                console.log('API response:', response); // Log the response for debugging
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.error('Error:', textStatus, errorThrown); // Log error details to console
            console.error('Response:', jqXHR.responseText); // Log full response for more details

            // Display specific error messages based on status
            switch (jqXHR.status) {
                case 400:
                    alert('Bad Request: Please check your input.');
                    break;
                case 401:
                    alert('Unauthorized: Please log in.');
                    break;
                case 404:
                    alert('Not Found: The requested resource could not be found.');
                    break;
                case 500:
                    alert('Internal Server Error: Please try again later.');
                    break;
                default:
                    alert('An error occurred: ' + errorThrown);
            }
        }
    });
}

// Save or update product
function saveProduct(productId = null) {
    if ($('#productForm')[0].checkValidity()) { // Check if the form is valid
        // Gather product data from form fields
        const productData = {
            product_name: $('#name').val().trim(), // Ensure whitespace is trimmed
            uom_id: $('#uoms').val(),
            price_per_unit: parseFloat($('#price').val()), // Convert price to float
            quantity_in_stock: parseInt($('#stock').val()), // Convert stock to integer
        };

        // Log the productData to debug
        console.log('Product data being sent:', JSON.stringify(productData));

        // Validate that product_name is not empty
        if (!productData.product_name) {
            alert("Product name is required."); // Alert if product name is empty
            return; // Stop execution
        }

        // Validate price_per_unit
        if (isNaN(productData.price_per_unit) || productData.price_per_unit <= 0) {
            alert("Please enter a valid price."); // Alert if price is not valid
            return; // Stop execution
        }

        // Validate quantity_in_stock
        if (isNaN(productData.quantity_in_stock) || productData.quantity_in_stock < 0) {
            alert("Please enter a valid quantity in stock."); // Alert if quantity is not valid
            return; // Stop execution
        }

        const method = productId ? 'PUT' : 'POST'; // Determine method based on productId
        const url = productId ? API_URLS.productUpdate(productId) : API_URLS.productSave; // Determine URL based on productId

        callApi(method, url, productData); // Use the common API call function
    } else {
        alert("Please fill in all required fields."); // Alert if form is invalid
    }
}

// To enable Bootstrap tooltip globally
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});
