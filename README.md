## Build From Source 
### Pre-requisites
Python, Foundry 
### Instructions 
1. `python -m venv venv` 
2. `source venv/bin/activate`
3. `pip install requirements.txt`
4. `cp example.env .env` And change the variables 
5. `chmod +x operators_init.sh && ./operators_init.sh`
6. `python main.py` 
7. `curl http://localhost:8080` > Will return a random Opacity operator's IP address 

## Build and use with Docker 
### Pre-requisites
Docker 
### Instructions 
1. `docker build . -t opacitynodeselector`
2. `cp example.env .env` And change the variables 
3. `docker run --env-file .env -p 8080:8080 opacitynodeselector` 
4. `curl http://localhost:8080` > Will return a random Opacity operator's IP address 
