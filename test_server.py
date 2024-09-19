import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import server  # Assuming your main code is in server.py

class TestProxyserver(unittest.TestCase):

    @patch('server.get_operator')
    @patch('requests.get')
    def test_proxy_request(self, mock_get, mock_get_operator):
        # Mock the operator to return a known value
        mock_get_operator.return_value = "70.34.203.161"

        # Mock the requests.get() to return a fake response
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"Mocked Response"

        # Create a mock connection object with a makefile method
        mock_connection = MagicMock()
        mock_connection.makefile.return_value = BytesIO(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")

        # Mock client address and server
        mock_client_address = ('127.0.0.1', 8080)
        mock_server = MagicMock()

        # Create an instance of the ProxyHTTPRequestHandler with the mocked request
        handler = server.ProxyHTTPRequestHandler(mock_connection, mock_client_address, mock_server)
        
        # Mock the output stream (wfile) for the handler
        handler.wfile = BytesIO()

        # Call the GET request handler
        handler.do_GET()

        # Check the response in the wfile
        handler.wfile.seek(0)
        response = handler.wfile.read()

        # Assert that the response contains the mocked response content
        self.assertIn(b"Mocked Response", response)
        mock_get.assert_called_with("https://70.34.203.161:7047", verify=False)

if __name__ == '__main__':
    unittest.main()
