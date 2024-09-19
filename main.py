import listener
import logging
import server
from multiprocessing import Process 
import os 
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

if __name__ == '__main__':
    REGISTRY_COORDINATOR_ADDRESS = os.getenv('REGISTRY_COORDINATOR_ADDRESS')
    RPC_URL =  os.getenv('RPC_URL')
    print(RPC_URL)
    if not REGISTRY_COORDINATOR_ADDRESS or not RPC_URL:
        logging.error("Please set the environment variables REGISTRY_COORDINATOR_ADDRESS and RPC_URL")
        exit(1)
    JSON_FILE_PATH = 'operators.json'
    EVENT_SIGNATURE = "OperatorSocketUpdate(bytes32,string)" # Make sure not to put the variable names or event prefix in the signature
    socket_listener = listener.OperatorSocketListener(REGISTRY_COORDINATOR_ADDRESS, EVENT_SIGNATURE, RPC_URL, JSON_FILE_PATH)
    socket_listener_process = Process(target=socket_listener.run)
    socket_listener_process.start()
    EVENT_SIGNATURE = "OperatorDeregistered(address,bytes32)"
    deregistration_listener = listener.OperatorDeregistrationListener(REGISTRY_COORDINATOR_ADDRESS, EVENT_SIGNATURE, RPC_URL, JSON_FILE_PATH)
    deregistration_listener_process = Process(target=deregistration_listener.run)
    deregistration_listener_process.start()
    server_process = Process(target=server.run)
    server_process.start()
    socket_listener_process.join()
    deregistration_listener_process.join()
    server_process.join()