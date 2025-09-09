$(document).ready(function () {
    // Retrieve URL parameters
    const { customer, grandTotal, order_id } = getUrlParameters(['customer', 'grandTotal', 'order_id']);

    // Display customer name and grand total dynamically
    $('#customerName').val(customer);
    $('#grandTotal').val(formatGrandTotal(grandTotal));

    // Load products from session storage and display in the table
    loadProducts();

    // Handle payment mode change (UPI or Cash)
    $('input[name="paymentMode"]').on('change', handlePaymentModeChange);

    // Handle "Pay Now" button click
    $('#payNow').on('click', payNow);
});

// Function to format the grand total to 2 decimal places
function formatGrandTotal(total) {
    const parsedTotal = parseFloat(total);
    return isNaN(parsedTotal) ? '0.00' : parsedTotal.toFixed(2);
}

// Function to get multiple URL parameters
function getUrlParameters(names) {
    return names.reduce((params, name) => {
        const value = new URLSearchParams(window.location.search).get(name);
        params[name] = value;
        return params;
    }, {});
}

// Function to load products into the payment page
function loadProducts(orderDetails = JSON.parse(sessionStorage.getItem('orderProducts') || '[]')) {
    const productTableBody = document.getElementById('productTableBody');
    productTableBody.innerHTML = '';

    if (orderDetails.length === 0) {
        console.log('No order details found in sessionStorage');
    } else {
        orderDetails.forEach(product => {
            const pricePerUnit = parseFloat(product.price_per_unit).toFixed(2);
            const totalPrice = (product.quantity * product.price_per_unit).toFixed(2);

            const row = `
                <tr>
                    <td>${product.product_name}</td>
                    <td>${product.quantity}</td>
                    <td>₹${pricePerUnit}</td>
                    <td>₹${totalPrice}</td>
                </tr>
            `;
            productTableBody.insertAdjacentHTML('beforeend', row);
        });
    }
}

// Function to handle payment mode change
function handlePaymentModeChange() {
    const selectedPaymentMode = $('input[name="paymentMode"]:checked').val();
    if (selectedPaymentMode === 'upi') {
        $('#qrcodeCanvas').show();
        $('#scanToPayLabel').show();
        const grandTotal = $('#grandTotal').val();
        $('#amountValue').text(grandTotal);
        $('#amountDisplay').show();
        generateQRCode(grandTotal);
    } else {
        $('#qrcodeCanvas').hide();
        $('#scanToPayLabel').hide();
        $('#amountDisplay').hide();
    }
}

// Function to generate a QR Code for UPI payments
/**
 * Generates a UPI payment QR code and displays it on the canvas element.
 * @param {string|number} amount - The payment amount to encode in the QR code.
 */
function generateQRCode(amount) {
    new QRious({
        element: document.getElementById('qrcodeCanvas'),
        value: `upi://pay?pa=maddoxer143-1@okaxis&pn=Groceries-Store&am=${amount}&cu=INR`,
        size: 200
    });
}

//Function to handly Pay Now button.
function payNow() {
    const grandTotal = parseFloat($('#grandTotal').val());
    const orderId = getUrlParameter('order_id');
    const customerName = $('#customerName').val();
    const paymentMode = $('input[name="paymentMode"]:checked').val();
    const orderDetails = JSON.parse(sessionStorage.getItem('orderProducts') || '[]');

    // Validate inputs
    if (isNaN(grandTotal) || grandTotal <= 0) {
        toastr.error('Grand total must be valid.');
        return;
    }
    if (!paymentMode) {
        toastr.error('Please select a payment mode.');
        return;
    }

    // Build the payment payload to send to the backend
    const orderData = {
        grandTotal: grandTotal.toFixed(2),
        order_id: orderId,
        customer_name: customerName,
        payment_mode: paymentMode,
        order_details: orderDetails
    };

    // Set the toastr options
    toastr.options = {
        timeOut: 3000, // Timeout in milliseconds
        positionClass: 'toast-top-right', // Position of the notification
        preventDuplicates: true, // Prevent duplicate notifications
        closeButton: true // Show a close button on the notification
    };

    // Send payment data to the backend
    fetch(`${baseURL}/processPayment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        console.log('Payment response:', data); // Log payment response
        if (data.message) {  // Use message from the server response
            toastr.success(data.message); // Show success message from server
            clearOrderData();
            console.log('Redirecting to index.html');
            // Redirect to index.html after a slight delay
            setTimeout(() => {
                console.log('Redirecting now');
                window.location.href = `index.html`;
            }, 2000); // Redirect after 2 seconds
        } else {
            toastr.error(data.message || 'Payment failed. Please try again.', 'Error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastr.error('Error Processing Payment. Try again!'); // Handle errors
    });
}



// Function to clear order data from sessionStorage
function clearOrderData() {
    sessionStorage.removeItem('orderProducts');
}

// Function to get a single URL parameter
function getUrlParameter(name) {
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}
