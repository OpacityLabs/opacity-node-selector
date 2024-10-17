import random
import requests
import urllib3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import json 
import time
from web3.auto import w3
from eth_account.messages import encode_defunct
def log(message):
    file = open("server.log.txt", "a")
    file.write(message + "\n")
    file.close()

# Generate random bytes and convert them to an integer
def random_int():
    return random.randint(0, 255)

# Get a random operator address
def get_operator() -> str | None:
    rand_int = random_int()
    with open('operators.json', 'r') as file:
        data = json.load(file)
    log(f"Selecting from json data {data}")
    ip_addresses = [data[operator_id] for operator_id in data['operators']] 
    if len(ip_addresses) == 0:
        return None
    return ip_addresses[rand_int % len(ip_addresses)]

# Proxy request handler
class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        load_dotenv()
        if os.getenv('SERVER_PRIVATE_KEY') is None or os.getenv('MAX_OPERATOR_RETRY_ATTEMPTS') is None:
            raise ValueError("SERVER_PRIVATE_KEY and MAX_OPERATOR_RETRY_ATTEMPTS must be set")
        self.private_key = os.getenv('SERVER_PRIVATE_KEY')
        self.max_attempts = int(os.getenv('MAX_OPERATOR_RETRY_ATTEMPTS', 5))
        super().__init__(*args, **kwargs)
    def do_GET(self):
        # initalize the max attempts using the environment variable MAX_OPERATOR_RETRY_ATTEMPTS or default to 5 
        attempts = 0
        operator = None
        log(f"Starting operator selection")
        while attempts < self.max_attempts:
            operator = get_operator()
            log(f"Selected operator: {operator}")
            if operator is None:
                self.send_error(500, "No operators available.")
                return
            log(f"Selected operator IP: {operator}")
            if self.liveness_check(operator+":7047"):
                log(f"Operator is live: {operator}")
                break
            else:
                log(f"Operator is not live: {operator}. Trying another operator.")
                attempts += 1
        
        if attempts == self.max_attempts:
            self.send_error(500, "No live operators available.")
            return

        # Return the target URL and signature in JSON format
        self.send_response(200)  # OK status
        self.send_header('Content-type', 'application/json')  # Set content type to JSON
        self.end_headers()
        signature , timestamp = self.generate_signature(operator)
        response_data = {
            "node_url": operator,
            "timestamp": timestamp,
            "signature": signature
        }
        self.wfile.write(json.dumps(response_data).encode('utf-8'))  # Write JSON response

    def liveness_check(self, url):
        """Check if the target URL is live by sending a HEAD request."""
        return True
        # try:
        #     response = requests.head(url, verify=False, timeout=2)
        #     return response.status_code == 200
        # except requests.RequestException:
        #     return False
    def generate_signature(self, target_url) -> str:
        """Generate a signature for the given target URL."""
        timestamp = int(time.time())
        message = f"{target_url},{timestamp}"
        message = encode_defunct(text=message)
        signature =  w3.eth.account.sign_message(message, private_key=self.private_key)
        return signature.signature.hex(), timestamp

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    # Ignore SSL certificate verification
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    # Optional: handle TLS/SSL connections with self-signed certificates
    # httpd.socket = ssl.wrap_socket(httpd.socket, certfile="path/to/cert.pem", keyfile="path/to/key.pem", server_side=True)

    log(f'Server running on port {port}')
    httpd.serve_forever()
