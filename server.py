import random
import requests
import urllib3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import ssl

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
        # Choose a random operator and construct the target URL
        operator = get_operator()
        log(f"Selected operator ip: {operator}")
        target_url = f"https://{operator}:7047"
        log(f"Redirecting to: {target_url}")

        # Send the request to the operator
        try:
            response = requests.get(target_url, verify=False)
            self.send_response(response.status_code)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(response.content)
        except Exception as e:
            self.send_error(500, f"Proxy error: {str(e)}")

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    # Ignore SSL certificate verification
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    # Optional: handle TLS/SSL connections with self-signed certificates
    # httpd.socket = ssl.wrap_socket(httpd.socket, certfile="path/to/cert.pem", keyfile="path/to/key.pem", server_side=True)

    log(f'Server running on port {port}')
    httpd.serve_forever()