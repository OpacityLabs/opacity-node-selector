#!/bin/bash

# ANSI escape codes for text color
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BOLD="\033[1m"
RESET="\033[0m"  # Reset to default color

chain="mainnet"
operators=""

usage() {
  echo "Usage: $0 [--chain <mainnet|testnet>] [--operators <operator1,operator2,...>]"
  exit 1
}

# Parse named arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --chain)
      chain=${2}
      shift 2
      ;;
    --operators)
      operators=${2}
      shift 2
      ;;
    *)
      echo "Unknown parameter passed: $1"
      usage
      ;;
  esac
done
if [ "$chain" = "mainnet" ]; then
  # add the infura url 
  # rpc_url=$RPC_URL
  rpc_url=https://mainnet.infura.io/v3/b660f863444c456780e56fe08662b025
  registryCoordinator=0xeCd099fA5048c3738a5544347D8cBc8076E76494
  indexRegistry=0x9eCe1f5B8aAfC6E4126FF0DA9c86F4549439bEe9
  delegationManager=0x39053D51B77DC0d36036Fc1fCc8Cb819df8Ef37A
else
  rpc_url=https://ethereum-holesky-rpc.publicnode.com
  registryCoordinator=0xb7ba8bbc36AA5684fC44D02aD666dF8E23BEEbF8
  indexRegistry=0xda12A0D0fE8a1A2250eAaA16166908a877497Be7
  delegationManager=0xA44151489861Fe9e3055d95adC98FbD462B948e7
fi

function get_operator() {
    operatorID=$1
    color=${YELLOW}
    operator=$(~/.foundry/bin/cast  call ${registryCoordinator} "function getOperatorFromId(bytes32)" ${operatorID} -r ${rpc_url} | ~/.foundry/bin/cast  parse-bytes32-address)
    if [ "${operators}" != "" ]; then
        if [[ ! ${operators} =~ ${operator} ]]; then
            return
        fi
    fi
    socket_event_data=$(~/.foundry/bin/cast  logs --address ${registryCoordinator} --from-block earliest --to-block latest "OperatorSocketUpdate(bytes32 indexed operatorId, string socket)" ${operatorID} -r ${rpc_url}  | grep 'data:' | awk '{print $2}')

    matches=($(echo "$socket_event_data" | grep -o '0x[0-9a-fA-F]\+' | tr -d '\"'))

    # Get the number of elements
    count=${#matches[@]}

    # If there's more than one occurrence, print the last one
    if [ "$count" -gt 1 ]; then
        last_index=$((count - 1))
        socket_event_data=${matches[$last_index]}
    fi
    ip_address=$(~/.foundry/bin/cast  abi-decode -i "decoder(string socket)" ${socket_event_data})
    # Append operatorID to the list of operators
    jq -r --arg opID "$operatorID" '.operators += [$opID]' "operators.json" > tmp.json && mv tmp.json "operators.json"

    # Add or update the key:value pair for ip_address:operatorID
    jq -r --arg key "$operatorID" --arg value $ip_address '.[$key] = $value' "operators.json" > tmp.json && mv tmp.json "operators.json"
    echo -e "${color}Operator: ${operatorID} - ${operator} - ${ip_address}${RESET}"

}


block=$(~/.foundry/bin/cast  block-number -r ${rpc_url})
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${RESET} getting the block number"
  exit 1
fi

operatorsIDRaw=$(~/.foundry/bin/cast  call ${indexRegistry} "function getOperatorListAtBlockNumber(uint8,uint32)" 0 ${block} -r ${rpc_url})
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR${RESET} getting the operator list"
  exit 1
fi

operatorsID=$(~/.foundry/bin/cast  abi-decode "function(uint8,uint32) returns (bytes32[])" ${operatorsIDRaw})
operatorsID=$(echo ${operatorsID} | tr -d '[' | tr -d ']' | tr -d ',')
echo '{"operators": []}' > "operators.json"

for operatorID in ${operatorsID[@]}; do
  get_operator ${operatorID} ${operarors} 
done
sed 's/\\"//g' operators.json > tmp.json
mv tmp.json operators.json
wait
