let productPrices = {};
let productDetailsByID = {};

// On document ready, fetch products and set up event listeners
$(document).ready(function () {
    fetchProducts();
    $("#addMoreButton").click(addProductRow);
    $("#saveOrder").click(saveOrder);
    toastr.info("Ready to create a new order.");

    // Set up event listeners for dynamic dropdowns and quantities
    $('#itemsInOrder').on('change', '.cart-product', updateProductPrice);
    $('#itemsInOrder').on('input', '.product-qty', updateProductTotal);
    $('#itemsInOrder').on('click', '.remove-row', removeProductRow);

    // Initialize camera controls for barcode scanning
    initCameraControls();
});

// Fetch products from the backend to populate product selection
function fetchProducts() {
    $.get(`${baseURL}/getProducts`, function (response) {
        if (response && Array.isArray(response) && response.length > 0) {
            let options = '<option value="">--Select Product--</option>';
            response.forEach(product => {
                options += `<option value="${product.product_id}">${product.product_name}</option>`;
                productPrices[product.product_id] = product.price_per_unit;
                productDetailsByID[product.product_id] = product;
            });
            window.productOptions = options;
            if ($("#itemsInOrder").children().length === 0) {
                addProductRow(); // Add initial row if no products added
            }
        } else {
            console.error("Invalid product response.");
            toastr.error("Failed to load products.");
        }
    }).fail(function (xhr, status, error) {
        toastr.error("Error fetching products: " + error);
    });
}

function addProductRow(productId = "", productName = "", price = 0, quantity = 1) {
    const rowHtml = `
        <div class="row mb-2">
            <div class="col-sm-4">
                <select class="form-control cart-product">
                    ${window.productOptions}
                </select>
            </div>
            <div class="col-sm-2">
                <input type="text" class="form-control price" value="${price}" readonly>
            </div>
            <div class="col-sm-2">
                <input type="number" class="form-control product-qty" value="${quantity}" min="1">
            </div>
            <div class="col-sm-3">
                <input type="text" class="form-control total" value="${(price * quantity).toFixed(2)}" readonly>
            </div>
            <div class="col-sm-1">
                <button type="button" class="btn btn-danger btn-sm remove-row">X</button>
            </div>
        </div>
    `;

    // Append the new row to the order list
    const $row = $(rowHtml);
    $("#itemsInOrder").append($row);

    // Automatically select the product from the dropdown based on the scanned productId
    if (productId) {
        $row.find(".cart-product").val(productId);
    }

    updateGrandTotal();
}


const $row = $(rowHtml);
$row.find('.cart-product').val(productId); // Set the correct product in the dropdown
$("#itemsInOrder").append($row);
updateGrandTotal();


// Update the product price based on selected product
function updateProductPrice() {
    const selectedProductId = $(this).val();
    const row = $(this).closest('.row');
    const priceInput = row.find('.price');
    const qtyInput = row.find('.product-qty');

    if (selectedProductId) {
        const product = productDetailsByID[selectedProductId];
        priceInput.val(productPrices[selectedProductId]);
        qtyInput.val(1); // Reset quantity to 1
        updateProductTotal.call(qtyInput); // Update total for this row
    } else {
        priceInput.val(0);
        row.find('.total').val(0);
    }
    updateGrandTotal();
}

// Update the total for each product based on quantity
function updateProductTotal() {
    const row = $(this).closest('.row');
    const price = parseFloat(row.find('.price').val());
    const qty = parseInt($(this).val());
    const total = price * qty;
    row.find('.total').val(total.toFixed(2));
    updateGrandTotal();
}

// Calculate and update the grand total of the order
function updateGrandTotal() {
    let grandTotal = 0;
    $('#itemsInOrder .total').each(function () {
        grandTotal += parseFloat($(this).val()) || 0;
    });
    $('#product_grand_total').val(grandTotal.toFixed(2));
}

// Remove product row
function removeProductRow() {
    $(this).closest('.row').remove();
    updateGrandTotal();
}

// Save Order
function saveOrder() {
    const orderDetails = collectOrderDetails();

    // Check if at least one product is added
    if (orderDetails.length === 0) {
        toastr.warning("Please add at least one product to the order.");
        return;
    }

    const customerName = $('#customerName').val();
    const grandTotal = parseFloat($('#product_grand_total').val());

    // Log values for debugging
    console.log('Customer Name:', customerName); // Check if customer name is retrieved correctly
    console.log('Grand Total:', grandTotal); // Check if grand total is retrieved correctly

    // Proceed only if values are valid
    if (!customerName || isNaN(grandTotal)) {
        toastr.error("Please ensure the customer name and grand total are valid.");
        return;
    }

    const orderData = {
        customer_name: customerName,
        grandTotal: grandTotal,
        order_details: orderDetails,
    };

    // Store order details in sessionStorage before redirecting
    sessionStorage.setItem('orderProducts', JSON.stringify(orderDetails));

    // Ajax call to insert order in backend
    $.ajax({
        url: `${baseURL}/insertOrder`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(orderData),
        success: function(response) {
            // Assuming the response contains the order_id
            const orderId = response.order_id; // Get the generated order_id

            // Redirect to payment page with order ID
            window.location.href = `payment.html?customer=${customerName}&grandTotal=${grandTotal}&order_id=${orderId}`;
        },
        error: function(xhr) {
            console.error(xhr); // Log the entire xhr object for debugging
            let errorMessage = 'Error placing order.';
            
            // Check if the response contains a JSON object with a message
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMessage = xhr.responseJSON.message;
            } else if (xhr.responseText) {
                // Fallback to responseText if JSON is not available
                errorMessage = xhr.responseText;
            }
            
            toastr.error(errorMessage);
        }
    });
}
$('#orderForm').on('submit', function(e) {
    e.preventDefault(); // Prevent the form from submitting normally
    saveOrder(); // Call saveOrder function
});


// Collect order items
function collectOrderDetails() {
    const orderDetails = [];
    $('#itemsInOrder .row').each(function () {
        const productId = $(this).find('.cart-product').val();
        const qty = parseInt($(this).find('.product-qty').val());
        const pricePerUnit = parseFloat($(this).find('.price').val());

        // Ensure productId, qty, and pricePerUnit are valid before pushing to orderDetails
        if (productId && qty > 0 && !isNaN(pricePerUnit)) {
            const productName = productDetailsByID[productId]?.product_name || 'Unknown Product'; // Fallback
            orderDetails.push({
                product_id: productId,
                product_name: productName,
                quantity: qty,
                price_per_unit: pricePerUnit
            });
        }
    });
    return orderDetails;
}


// Initialize camera controls for barcode scanning
function initCameraControls() {
    const startButton = $('#startButton');
    const stopButton = $('#stopButton');
    const videoElement = $('#video')[0];

    startButton.on('click', function (e) {
        e.preventDefault();
        startBarcodeScanner(videoElement, startButton, stopButton);
    });

    stopButton.on('click', function (e) {
        e.preventDefault();
        stopBarcodeScanner(videoElement, startButton, stopButton);
    });
}
