let scannerActive = false;
let lastScanTime = 0; // Timestamp of the last scan
const scanTimeout = 5000; // 5 seconds timeout

// Initialize the camera and start scanning
function startBarcodeScanner(videoElement, startButton, stopButton) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then(function (stream) {
            videoElement.srcObject = stream;
            videoElement.play();
            Quagga.init({
                inputStream: {
                    name: "Live",
                    type: "LiveStream",
                    target: videoElement, // Reference to the video element
                    constraints: {
                        facingMode: "environment", // Use back camera
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    },
                },
                decoder: {
                    readers: ["ean_reader"] // Specify barcode types to read
                }
            }, function (err) {
                if (err) {
                    console.error(err);
                    toastr.error("Failed to start scanner.");
                    return;
                }
                console.log("Quagga initialized");
                Quagga.start();
                startButton.hide(); // Hide start button
                stopButton.show(); // Show stop button
            });

            Quagga.onDetected(function (result) {
                const code = result.codeResult.code;
                // Handle detected barcode here
                toastr.success("Detected barcode: " + code);
                processBarcode(code); // Call the processBarcode function to handle the detected barcode
            });
        })
        .catch(function (err) {
            console.error("Error accessing camera: ", err);
            toastr.error("Camera access denied: " + err);
        });
}

function stopBarcodeScanner(videoElement, startButton, stopButton) {
    Quagga.stop();
    videoElement.srcObject.getTracks().forEach(track => track.stop());
    startButton.show(); // Show start button
    stopButton.hide(); // Hide stop button
}

// Process the detected barcode, fetch product, and add to cart
// Process the detected barcode, fetch product, and add to cart
function processBarcode(barcode) {
    const currentTime = new Date().getTime(); // Get the current time

    // Check if enough time has passed since the last scan
    if (currentTime - lastScanTime > scanTimeout) {
        lastScanTime = currentTime; // Update last scan time
        console.log("Barcode detected:", barcode);
        
        $.get(`${baseURL}/getProductByBarcode?barcode=${barcode}`, function (response) {
            console.log(response); // Check the response
            if (response) {
                const { product_id, product_name, price_per_unit } = response;
                
                // Prevent adding duplicate products
                const existingRow = $(`#itemsInOrder .row:has(.cart-product[value="${product_id}"])`);
                if (existingRow.length > 0) {
                    // Update quantity if product already exists
                    const qtyInput = existingRow.find('.product-qty');
                    qtyInput.val(parseInt(qtyInput.val()) + 1); // Increase the quantity
                    updateProductTotal.call(qtyInput); // Update total for this row
                } else {
                    // Ensure you pass product_id, product_name, and price_per_unit
                    addProductRow(product_id, product_name, price_per_unit, 1); // Add product to cart
                    toastr.success("Product added to the cart!");
                }
            } else {
                toastr.error("Product not found.");
            }
        }).fail(function (xhr, status, error) {
            toastr.error("Error fetching product: " + error);
        });
    } else {
        toastr.warning("Please wait before scanning again."); // Notify user to wait before scanning again
    }
}


// Event listeners for buttons
$(document).ready(function () {
    $("#startButton").click(function (e) {
        e.preventDefault();
        const videoElement = $('#video')[0];
        startBarcodeScanner(videoElement, $(this), $("#stopButton"));
    });

    $("#stopButton").click(function (e) {
        e.preventDefault();
        const videoElement = $('#video')[0];
        stopBarcodeScanner(videoElement, $("#startButton"), $(this));
    });
});
