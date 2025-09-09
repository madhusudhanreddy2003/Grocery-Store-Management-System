// Global cart array to keep track of added products
let cart = [];

// Constants for API URLs
const API_URLS = {
  getProducts: `${baseURL}/getProducts`,
  getUOMs: `${baseURL}/getUOMs`,
  insertProduct: `${baseURL}/insertProduct`,
  updateProduct: (productId) => `${baseURL}/updateProduct/${productId}`,
  deleteProduct: (productId) => `${baseURL}/deleteProduct/${productId}`,
  getProduct: (productId) => `${baseURL}/getProduct/${productId}`,
};

// Show toast notifications
function showSuccessToast(message) {
  toastr.success(message);
}

function showErrorToast(message) {
  toastr.error(message);
}
// Function to show the loading overlay
function showLoadingOverlay() {
  $('#loadingOverlay').show();
}

// Function to hide the loading overlay
function hideLoadingOverlay() {
  $('#loadingOverlay').hide();
}
// Show/Hide loading overlay with fade effects
function showLoadingSpinner() {
  $('#loadingOverlay').fadeIn(100);
}

function hideLoadingSpinner() {
  $('#loadingOverlay').fadeOut(300);
}

// Fetch Products
function fetchProducts() {
  showLoadingSpinner();
  $.ajax({
    url: API_URLS.getProducts, // Ensure this URL is correct
    method: 'GET',
    success: function(data) {
      console.log("Fetched products data:", data);
      const productTable = $('#productstableBody'); // Access the tbody directly by ID
      
      productTable.empty(); // Clear existing rows in the tbody

      if (Array.isArray(data) && data.length > 0) {
        data.forEach(function(product) {
          const productRow = createProductRow(product); // Ensure this function returns a proper HTML string
          productTable.append(productRow); // Append the product row to tbody
        });
      } else {
        productTable.append('<tr><td colspan="6">No products found.</td></tr>');
      }
      hideLoadingSpinner();
      attachEditButtonListeners(); // Attach listeners to edit buttons if necessary
    },
    error: function(xhr, status, error) {
      console.error(`Error fetching products [${status}]:`, xhr);
      console.error(`Response text: ${xhr.responseText}`);
      showErrorToast("Error fetching products. Please try again.");
      hideLoadingSpinner();
  }
  
    
  });
}

// Function to create a table row for a product
function createProductRow(product) {
  return `
    <tr>
      <td>${product.product_id !== undefined ? product.product_id : 'N/A'}</td>
      <td>${product.product_name || 'N/A'}</td>
      <td>${product.uom_name || 'N/A'}</td>
      <td>${(product.price_per_unit !== undefined ? parseFloat(product.price_per_unit).toFixed(2) : '0.00')}</td>
      <td>${(product.quantity_in_stock !== undefined ? product.quantity_in_stock : '0')}</td>
      <td>
        <button class="btn btn-warning btn-sm updateProductBtn" data-id="${product.product_id}">Edit</button>
        <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.product_id})">Delete</button>
      </td>
    </tr>
  `;
}

// Function to fetch and populate UOMs in the dropdown
function fetchUoms(callback) {
  showLoadingSpinner();
  $.ajax({
    url: API_URLS.getUOMs,
    method: 'GET',
    success: function(data) {
      const uomsSelect = $('#uom_id');
      uomsSelect.empty();
      uomsSelect.append('<option value="">Select Unit</option>');

      if (Array.isArray(data) && data.length > 0) {
        data.forEach(function(uom) {
          uomsSelect.append(`<option value="${uom.uom_id}">${uom.uom_name}</option>`);
        });
      } else {
        uomsSelect.append('<option disabled>No UOMs found.</option>');
      }
      hideLoadingSpinner();
      if (callback) {
        callback();
      }
    },
    error: function(xhr, status, error) {
      console.error(`Error fetching UOMs [${status}]:`, error);
      showErrorToast("Error fetching units of measure. Please try again.");
      hideLoadingSpinner();
    }
  });
}

function resetForm() {
  $('#productForm')[0].reset();
  $('#productForm').find('input, textarea, select').removeClass('is-invalid');
}

// On page load, fetch UOMs and products
$(document).ready(function() {
 
  // Add event listener to save button
  $('#saveProductBtn').off('click').on('click', function() {
    saveProduct();
  });
});

// When "Add New Product" or "Edit" form is opened, fetch UOMs
$('#productModal').on('show.bs.modal', function() {
  fetchUoms();
});

// Function to attach event listeners to edit buttons
function attachEditButtonListeners() {
  $('.updateProductBtn').off('click').on('click', function() {
    const productId = $(this).attr('data-id'); // Get the productId from the data-id attribute
    editProduct(productId);
  });
}

$(document).ready(function() {
  // Fetch UOMs and products on page load
  fetchUoms();
  fetchProducts();

  // Add event listener to save button
  $('#saveProduct').on('click', function() {
      saveProduct();
  });

  // Reset form fields when clicking on "Add New Product" button
  $('#addProductBtn').on('click', function() {
      resetForm();
  });
});

// Reset form function to clear all input fields
function resetForm() {
  $('#productForm')[0].reset();
  $('#productForm').find('input, textarea, select').removeClass('is-invalid');
}

//edit product
function editProduct(productId) {
  console.log(`Editing product with ID: ${productId}`); // Log the product ID

  // Show the loading overlay
  showLoadingOverlay();

  // Fetch the product data
  $.ajax({
      type: 'GET',
      url: `${baseURL}/getProduct/${productId}`,
      success: function(response) {
          console.log(`Response: ${JSON.stringify(response)}`); // Log the response

          // Hide the loading overlay
          hideLoadingOverlay();

          // Populate the product form with the product data
          $('#product_name').val(response.product_name);
          $('#uom_id').val(response.uom_id);
          $('#price_per_unit').val(parseFloat(response.price_per_unit).toFixed(2));
          $('#quantity_in_stock').val(response.quantity_in_stock);
          $('#barcode').val(response.barcode);
          $('#productId').val(response.product_id);

          // Update the saveProduct button to call the updateProduct function
          $('#saveProduct').off('click').on('click', function() {
              updateProduct();
          });

          // Show the product modal
          $('#productModal').modal('show');
      },
      error: function(xhr, status, error) {
          console.log(`Error: ${error}`); // Log the error

          // Hide the loading overlay
          hideLoadingOverlay();

          // Check if the error is a 404 error
          if (xhr.status === 404) {
              // Show an error message
              toastr.error(`Product not found: ${error}`);
          } else {
              // Show an error message
              toastr.error(`Error fetching product: ${error}`);
          }
      }
  });
}

function updateProduct() {
  console.log('Updating product...');

  // Get the product data from the form
  const productData = {
    product_id: $('#productId').val(),
    product_name: $('#product_name').val(),
    uom_id: $('#uom_id').val(),
    price_per_unit: parseFloat($('#price_per_unit').val()).toFixed(2),
    quantity_in_stock: parseInt($('#quantity_in_stock').val()),
    barcode: $('#barcode').val()
  };

  console.log(`Product data: ${JSON.stringify(productData)}`);

  // Show the loading overlay
  showLoadingOverlay();

  // Update the product data
  $.ajax({
    type: 'PUT',
    url: `${baseURL}/updateProduct/${productData.product_id}`, // Update the URL to include the product_id parameter
    data: JSON.stringify(productData),
    contentType: 'application/json',
    success: function(response) {
      console.log(`Response: ${JSON.stringify(response)}`);

      // Hide the loading overlay
      hideLoadingOverlay();

      // Show a success message
      toastr.success('Product updated successfully');

      // Refresh the product table
      refreshProductTable();
    },
    error: function(xhr, status, error) {
      console.log(`Error: ${error}`);

      // Hide the loading overlay
      hideLoadingOverlay();

      // Show an error message
      toastr.error(`Error updating product: ${error}`);
    }
  });
}

// Function to delete a product
function deleteProduct(productId) {
  console.log(`Deleting product with ID: ${productId}`);

  // Show the loading overlay
  showLoadingOverlay();

  // Correct URL for the DELETE request
  $.ajax({
    url: `${baseURL}/deleteProduct/${productId}`, // Ensure this is the correct endpoint for deleting a product
    type: 'DELETE',
    success: function(response) {
      console.log(`Response: ${JSON.stringify(response)}`);

      // Hide the loading overlay
      hideLoadingOverlay();

      // Show a success message
      toastr.success(response.message);

      // Refresh the product table
      refreshProductTable();
    },
    error: function(xhr, status, error) {
      console.log(`Error: ${error}`);

      // Hide the loading overlay
      hideLoadingOverlay();

      // Show an error message
      toastr.error(`Error deleting product: ${error}`);
    }
  });
}


// Save Product function
function saveProduct() {
  console.log("Save Product function called");
  const productForm = $('#productForm');
  const formData = new FormData(productForm[0]);

  // Validate form data
  const productName = formData.get('product_name');
  const uomId = formData.get('uom_id');
  const pricePerUnit = formData.get('price_per_unit');
  const quantityInStock = formData.get('quantity_in_stock');

  if (!productName || !uomId || !pricePerUnit || !quantityInStock) {
      showErrorToast("All fields are required.");
      return; // Stop execution if validation fails
  }

  const productId = formData.get('product_id');
  const url = productId && productId !== '' ? API_URLS.updateProduct(productId) : API_URLS.insertProduct;

  const productData = {
      product_name: productName,
      uom_id: uomId,
      price_per_unit: pricePerUnit,
      quantity_in_stock: quantityInStock
  };

  console.log("Form Data Before Saving:", JSON.stringify(productData));

  showLoadingSpinner();

  // Send AJAX request with JSON data
  $.ajax({
      url: url,
      method: productId && productId !== '' ? 'PUT' : 'POST',
      data: JSON.stringify(productData),
      contentType: 'application/json',
      headers: {
          'Content-Type': 'application/json'
      },
      success: function(data) {
          console.log("Saved product:", data);
          if (productId && productId !== '') {
              showSuccessToast("Product updated successfully.");
          } else {
              showSuccessToast("Product added successfully.");
          }
          fetchProducts();
          hideLoadingSpinner();
          $('#productModal').modal('hide');
      },
      error: function(xhr, status, error) {
          console.error(`Error saving product [${status}]:`, xhr.responseText);
          showErrorToast("Error saving product. Please try again.");
          hideLoadingSpinner();
      }
  });
}
$(document).ready(function() {
  // Bind form submission to updateProduct
  $('#productForm').on('submit', function(event) {
      event.preventDefault();
      updateProduct();
  });
});
