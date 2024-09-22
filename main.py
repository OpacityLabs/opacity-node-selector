import listener
import logging
import server
from multiprocessing import Process
import os
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    REGISTRY_COORDINATOR_ADDRESS = os.getenv('REGISTRY_COORDINATOR_ADDRESS')
    WEBSOCKET_RPC_URL = os.getenv('WEBSOCKET_RPC_URL')
    JSON_FILE_PATH = 'operators.json'
    # Make sure not to put the variable names or event prefix in the signature
    EVENT_SIGNATURE = "OperatorSocketUpdate(bytes32,string)"
    socket_update_listener = listener.OperatorSocketListener(
        REGISTRY_COORDINATOR_ADDRESS, EVENT_SIGNATURE, WEBSOCKET_RPC_URL, JSON_FILE_PATH)
    socket_update_listener_process = Process(target=socket_update_listener.run)
    socket_update_listener_process.start()
    EVENT_SIGNATURE = "OperatorDeregistered(address,bytes32)"
    deregistration_listener = listener.OperatorDeregistrationListener(
        REGISTRY_COORDINATOR_ADDRESS, EVENT_SIGNATURE, WEBSOCKET_RPC_URL, JSON_FILE_PATH)
    deregistration_listener_process = Process(
        target=deregistration_listener.run)
    deregistration_listener_process.start()
    server_process = Process(target=server.run)
    server_process.start()
    socket_update_listener_process.join()
    deregistration_listener_process.join()
    server_process.join()
