import time
from PIL import Image
from io import BytesIO
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shopify

# Example usage of the Shopify API
def shopify_example():
    API_KEY = 
    PASSWORD =
    SHOP_NAME =

    session = shopify.Session(SHOP_NAME, API_KEY, PASSWORD)
    shopify.ShopifyResource.activate_session(session)

    try:
        # Fetch products from the store
        products = shopify.Product.find()
        for product in products:
            print(product.title)
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        shopify.ShopifyResource.clear_session()

# Function to solve CAPTCHA using Tesseract OCR
def solve_captcha(image):
    return pytesseract.image_to_string(image)

# Function to solve CAPTCHA using manual input
def manual_solve_captcha(image_url):
    # Download the captcha image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img.show()  # Display the image for manual solving
    captcha_solution = input("Enter the captcha solution: ")
    return captcha_solution

# Function to perform auto-checkout with CAPTCHA
def auto_checkout_with_captcha(url):
    # Initialize WebDriver (assuming you have installed appropriate browser driver and set its path)
    driver = webdriver.Chrome('/path/to/chromedriver')
    driver.get(url)

    try:
        # Wait for the captcha image to load
        captcha_image = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'img.captcha-img'))
        )
        captcha_url = captcha_image.get_attribute('src')

        # Solve the captcha
        captcha_solution = manual_solve_captcha(captcha_url)

        # Fill in captcha solution
        captcha_input = driver.find_element_by_id('captcha-input')
        captcha_input.send_keys(captcha_solution)

        # Add other steps of auto-checkout here...

    finally:
        # Pause to see the result before closing the browser
        time.sleep(10)
        driver.quit()

# Function to check product availability
def check_product_availability(product_url):
    response = requests.get(product_url)
    if response.status_code == 200:
        if "Sold Out" not in response.text:
            return True
    return False

# Function to perform checkout
def perform_checkout(product_url, checkout_url, customer_info):
    session = requests.Session()
    
    # Retrieve authenticity token
    response = session.get(product_url)
    auth_token_start = response.text.find('authenticity_token') + len('authenticity_token') + 4
    auth_token_end = response.text.find('"', auth_token_start)
    auth_token = response.text[auth_token_start:auth_token_end]

    # Prepare checkout payload
    payload = {
        'utf8': '✓',
        'authenticity_token': auth_token,
        'checkout[email]': customer_info['email'],
        'checkout[shipping_address][first_name]': customer_info['first_name'],
        'checkout[shipping_address][last_name]': customer_info['last_name'],
        # Add more fields as needed
    }

    # Perform checkout
    response = session.post(checkout_url, data=payload)

    # Check if checkout was successful
    if response.status_code == 200 and 'Thank you for your order' in response.text:
        print("Checkout Successful! Order placed.")
    else:
        print("Checkout Failed. Please check the details and try again.")

# Function to check if the product is available on Shopify
def check_shopify_product_availability(product_id):
    try:
        session = shopify.Session(API_KEY, PASSWORD)
        shopify.ShopifyResource.activate_session(session)
        product = shopify.Product.find(product_id)
        return not product.variants[0].inventory_quantity <= 0
    except Exception as e:
        print(f"Error checking product availability: {e}")
        return False
    finally:
        shopify.ShopifyResource.clear_session()

# Function to perform checkout on Shopify
def perform_shopify_checkout(product_id, customer_info):
    try:
        session = shopify.Session(API_KEY, PASSWORD)
        shopify.ShopifyResource.activate_session(session)
        
        # Create a new checkout
        checkout = shopify.Checkout()
        checkout.line_items = [{'variant_id': product_id, 'quantity': 1}]
        checkout.email = customer_info['email']
        checkout.shipping_address = {
            'first_name': customer_info['first_name'],
            'last_name': customer_info['last_name'],
            # Add more address fields as needed
        }
        checkout.shipping_address.update(customer_info['shipping_address'])
        checkout.shipping_address['country_code'] = 'US'  # Example: Change to your country code
        checkout.shipping_address['province_code'] = 'NY'  # Example: Change to your province code
        checkout.shipping_address['phone'] = '123456789'  # Example: Change to customer's phone number
        checkout.shipping_address['zip'] = '10001'  # Example: Change to customer's zip code

        # Create the checkout
        checkout.save()

        # Redirect the customer to the checkout URL
        print(f"Checkout URL: {checkout.to_json()['order_status_url']}")
    except Exception as e:
        print(f"Error performing checkout: {e}")
    finally:
        shopify.ShopifyResource.clear_session()

# Function to check payment information for an order on Shopify
def check_shopify_payment_info(order_id):
    try:
        session = shopify.Session(API_KEY, PASSWORD)
        shopify.ShopifyResource.activate_session(session)
        
        order = shopify.Order.find(order_id)
        payment_gateway = order.gateway
        if payment_gateway == 'shopify_payments':
            # Check payment status
            if order.financial_status == 'paid':
                print(f"Order {order_id} payment is successful.")
            else:
                print(f"Order {order_id} payment is pending.")
        else:
            print(f"Order {order_id} payment is processed through {payment_gateway}.")
    except Exception as e:
        print(f"Error occurred while checking payment for order {order_id}: {e}")
    finally:
        shopify.ShopifyResource.clear_session()

# Main function
def main(product_url, checkout_url, customer_info, product_id, order_id):
    # Check product availability on the website
    while not check_product_availability(product_url):
        print("Product is not available yet. Retrying in 5 seconds...")
        time.sleep(5)
    
    print("Product is available! Proceeding to checkout...")
    perform_checkout(product_url, checkout_url, customer_info)

    # Check product availability on Shopify
    while not check_shopify_product_availability(product_id):
        print("Product is not available yet on Shopify. Retrying in 5 seconds...")
        time.sleep(5)
    
    print("Product is available on Shopify! Proceeding to checkout...")
    perform_shopify_checkout(product_id, customer_info)

    # Check payment information for an order on Shopify
    check_shopify_payment_info(order_id)

if __name__ == "__main__":
    # Example usage
    product_url = "URL_TO_YOUR_PRODUCT"  # Insert the product URL here
    checkout_url = "URL_TO_CHECKOUT_PAGE"  # Insert the checkout URL here
    customer_info = {
        'email': 'customer@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        # Add more customer information as needed
        'shipping_address': {
            'address1': '123 Shipping St',
            'address2': 'Apt 1',  # Optional
            'city': 'New York',
            # Add more address fields as needed
        }
    }
    
    product_id = 'PRODUCT_ID'  # Replace with your product ID
    order_id = 'ORDER_ID'  # Replace with your order ID

    main(product_url, checkout_url, customer_info, product_id, order_id)

