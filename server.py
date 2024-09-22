import random
import requests
import urllib3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import ssl
import os
from dotenv import load_dotenv
import json 

def log(message):
    file = open("server.log.txt", "a")
    file.write(message + "\n")
    file.close()

# Generate random bytes and convert them to an integer
def random_int():
    return random.randint(0, 255)

# Get a random operator address
def get_operator():
    rand_int = random_int()
    with open('operators.json', 'r') as file:
        data = json.load(file)
    log(f"Selecting from json data {data}")
    ip_addresses = [data[operator_id] for operator_id in data['operators']] 
    return ip_addresses[rand_int % len(ip_addresses)]

# Proxy request handler
class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        load_dotenv()
        # initalize the max attempts using the environment variable MAX_OPERATOR_RETRY_ATTEMPTS or default to 5 
        max_attempts = int(os.getenv('MAX_OPERATOR_RETRY_ATTEMPTS', 5))
        attempts = 0
        operator = None
        target_url = None

        while attempts < max_attempts:
            operator = get_operator()
            target_url = f"https://{operator}:7047"
            log(f"Selected operator IP: {operator} | Target URL: {target_url}")

            if self.liveness_check(target_url):
                log(f"Operator is live: {target_url}")
                break
            else:
                log(f"Operator is not live: {target_url}. Trying another operator.")
                attempts += 1
        
        if attempts == max_attempts:
            self.send_error(500, "No live operators available.")
            return

        # Return the target URL in the response
        self.send_response(200)  # OK status
        self.send_header('Content-type', 'text/plain')  # Set content type to plain text
        self.end_headers()
        self.wfile.write(target_url.encode('utf-8'))  # Write the target URL in the response body

    def liveness_check(self, url):
        """Check if the target URL is live by sending a HEAD request."""
        try:
            response = requests.head(url, verify=False, timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    # Ignore SSL certificate verification
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    # Optional: handle TLS/SSL connections with self-signed certificates
    # httpd.socket = ssl.wrap_socket(httpd.socket, certfile="path/to/cert.pem", keyfile="path/to/key.pem", server_side=True)

    log(f'Server running on port {port}')
    httpd.serve_forever()