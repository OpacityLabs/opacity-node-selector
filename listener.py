import json
import asyncio
from web3 import AsyncWeb3, WebSocketProvider, Web3
import ipaddress
import time
import validators
from eth_abi import decode


def log(message):
    file = open("listener.log.txt", "a")
    file.write(message + "\n")
    file.close()


class Listener():
    def __init__(self, contract_address, event_signature, rpc_url, json_file_path):
        if not contract_address or not event_signature or not rpc_url or not json_file_path:
            raise ValueError("All parameters are required")
        self.contract_address = contract_address
        self.rpc_url = rpc_url
        self.event_signature = event_signature
        self.event_topic = Web3.keccak(text=event_signature).hex()
        self.json_file_path = json_file_path
        log(f"Listener initalized with contract address {self.contract_address}, event signature {self.event_signature}, rpc url {self.rpc_url}, json file path {self.json_file_path}")
        log(f"Attempting subscription to events on {self.contract_address} with event {self.event_signature} on {self.rpc_url}")

    def handle_event(self, event):
        pass

    async def subscribe_to_events(self):
        async with AsyncWeb3(WebSocketProvider(self.rpc_url)) as w3:
            filter_params = {
                "address": self.contract_address,
                "topics": [self.event_topic],
            }
            subscription_id = await w3.eth.subscribe("logs", filter_params)
            log(f"Subscription ID: {subscription_id}")
            async for payload in w3.socket.process_subscriptions():
                log(f"Received payload: {payload}")
                result = payload["result"]
                self.handle_event(result)

    def run(self):
        while True:
            try:
                asyncio.run(self.subscribe_to_events())
            except Exception as e:
                log(f"Error: {e}")
                time.sleep(5)


class OperatorSocketListener(Listener):
    def __init__(self, contract_address, event_signature, rpc_url, json_file_path):
        super().__init__(contract_address, event_signature, rpc_url, json_file_path)

    def handle_event(self, result):
        ip = decode(["string"], result["data"])[0]
        operator_id = '0x' + result["topics"][1].hex()
        log(f"Operator {operator_id} updated with IP: {ip}")
        if validate_ip(ip) or validate_domain(ip):
            # Read the JSON file
            with open(self.json_file_path, 'r') as file:
                data = json.load(file)

            # Add operator_id to operators array if not already present
            if operator_id not in data['operators']:
                data['operators'].append(operator_id)

            # Update or add the IP address for the operator_id
            data[operator_id] = ip

            # Write the updated data back to the JSON file
            with open(self.json_file_path, 'w') as file:
                json.dump(data, file, indent=2)

            log(f"Updated operator {operator_id} with IP: {ip}")
        else:
            log(f"Invalid IP address: {ip}")


class OperatorDeregistrationListener(Listener):
    def __init__(self, contract_address, event_signature, rpc_url, json_file_path):
        super().__init__(contract_address, event_signature, rpc_url, json_file_path)

    def handle_event(self, result):
        operator_id = '0x' + result["topics"][2].hex()
        log(f"Operator {operator_id} deregistered, removing from json")
        with open(self.json_file_path, 'r') as file:
            data = json.load(file)
        if operator_id in data['operators']:
            data['operators'].remove(operator_id)
            del data[operator_id]
        with open(self.json_file_path, 'w') as file:
            json.dump(data, file, indent=2)
        log(f"Deregistered operator {operator_id}")


def validate_ip(ip_string) -> bool:
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False
def validate_domain(domain_string) -> bool:
    try:
        validators.domain(domain_string)
        return True
    except ValueError:
        return False
