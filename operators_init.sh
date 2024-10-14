#!/bin/bash
source .env
chain="mainnet"
operators=""

usage() {
  echo "Usage: $0 [--chain <mainnet|testnet>]"
  exit 1
}

# Parse named arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --chain)
      chain=${2}
      shift 2
      ;;
    *)
      echo "Unknown parameter passed: $1"
      usage
      ;;
  esac
done

if [ "$chain" = "mainnet" ]; then
  rpc_url=$RPC_URL
else
  rpc_url=https://ethereum-holesky-rpc.publicnode.com
fi
registryCoordinator=$REGISTRY_COORDINATOR_ADDRESS
indexRegistry=$(~/.foundry/bin/cast c $REGISTRY_COORDINATOR_ADDRESS "indexRegistry()" -r $rpc_url | ~/.foundry/bin/cast parse-bytes32-address)
if [ $? -ne 0 ]; then
  echo -e "ERROR getting the index registry"
  exit 1
fi
stakeRegistry=$(~/.foundry/bin/cast c $REGISTRY_COORDINATOR_ADDRESS "stakeRegistry()" -r $rpc_url | ~/.foundry/bin/cast parse-bytes32-address)
if [ $? -ne 0 ]; then
  echo -e "ERROR getting the stake registry"
  exit 1
fi
delegationManager=$(~/.foundry/bin/cast c $stakeRegistry "delegation()" -r $rpc_url | ~/.foundry/bin/cast parse-bytes32-address)
if [ $? -ne 0 ]; then
  echo -e "ERROR getting the delegation manager"
  exit 1
fi

function get_operator() {
    operatorID=$1
    operator=$(~/.foundry/bin/cast  call ${registryCoordinator} "function getOperatorFromId(bytes32)" ${operatorID} -r ${rpc_url} | ~/.foundry/bin/cast  parse-bytes32-address)
    if [ $? -ne 0 ]; then
      echo -e "ERROR getting the operator"
      exit 1
    fi
    if [ "${operators}" != "" ]; then
        if [[ ! ${operators} =~ ${operator} ]]; then
            return
        fi
    fi
    socket_event_data=$(~/.foundry/bin/cast  logs --address ${registryCoordinator} --from-block earliest --to-block latest "OperatorSocketUpdate(bytes32 indexed operatorId, string socket)" ${operatorID} -r ${rpc_url}  | grep 'data:' | awk '{print $2}')
    if [ $? -ne 0 ]; then
      echo -e "ERROR getting the socket event data"
      exit 1
    fi
    matches=($(echo "$socket_event_data" | grep -o '0x[0-9a-fA-F]\+' | tr -d '\"'))

    # Get the number of elements
    count=${#matches[@]}

    # If there's more than one occurrence, print the last one
    if [ "$count" -gt 1 ]; then
        last_index=$((count - 1))
        socket_event_data=${matches[$last_index]}
    fi
    ip_address=$(~/.foundry/bin/cast  abi-decode -i "decoder(string socket)" ${socket_event_data})
    if [ $? -ne 0 ]; then
      echo -e "ERROR decoding the socket event data"
      exit 1
    fi
    # Append operatorID to the list of operators
    jq -r --arg opID "$operatorID" '.operators += [$opID]' "operators.json" > tmp.json && mv tmp.json "operators.json"
    if [ $? -ne 0 ]; then
      echo -e "ERROR updating the operators.json"
      exit 1
    fi
    # Add or update the key:value pair for ip_address:operatorID
    jq -r --arg key "$operatorID" --arg value $ip_address '.[$key] = $value' "operators.json" > tmp.json && mv tmp.json "operators.json"
    if [ $? -ne 0 ]; then
      echo -e "ERROR updating the operators.json"
      exit 1
    fi
    echo -e "Operator: ${operatorID} - ${operator} - ${ip_address}"

}


block=$(~/.foundry/bin/cast  block-number -r ${rpc_url})
if [ $? -ne 0 ]; then
  echo -e "ERROR getting the block number"
  exit 1
fi

operatorsIDRaw=$(~/.foundry/bin/cast  call ${indexRegistry} "function getOperatorListAtBlockNumber(uint8,uint32)" 0 ${block} -r ${rpc_url})
if [ $? -ne 0 ]; then
  echo -e "ERROR getting the operator list"
  exit 1
fi

operatorsID=$(~/.foundry/bin/cast  abi-decode "function(uint8,uint32) returns (bytes32[])" ${operatorsIDRaw})
if [ $? -ne 0 ]; then
  echo -e "ERROR decoding the operator list"
  exit 1
fi
operatorsID=$(echo ${operatorsID} | tr -d '[' | tr -d ']' | tr -d ',')
if [ $? -ne 0 ]; then
  echo -e "ERROR cleaning the operator list"
  exit 1
fi
echo '{"operators": []}' > "operators.json"

for operatorID in ${operatorsID[@]}; do
  get_operator ${operatorID} ${operators} 
done
sed 's/\\"//g' operators.json > tmp.json
mv tmp.json operators.json
wait
