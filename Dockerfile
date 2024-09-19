FROM python
RUN apt update && apt install -y jq 
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN curl -L https://foundry.paradigm.xyz | bash
RUN ~/.foundry/bin/foundryup 
COPY . . 
EXPOSE 8080
ENTRYPOINT [ "/bin/bash", "-c" ,"chmod +x /operators_init.sh && /operators_init.sh && python3 main.py > output.txt"]