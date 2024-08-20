# PANGMASA


- You must need to buy a VPS for running Allora Worker
- You can buy from : Contabo
- You should buy VPS which is fulfilling all these requirements : 
```bash
Operating System : Ubuntu 22.04
CPU: Minimum of 1/2 core.
Memory: 2 to 4 GB.
Storage: SSD or NVMe with at least 5GB of space.
```
# Prerequisites
Before you start, ensure you have docker compose installed.
```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
docker version

# Install Docker-Compose
VER=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)

curl -L "https://github.com/docker/compose/releases/download/"$VER"/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Docker Permission to user
sudo groupadd docker
sudo usermod -aG docker $USER
```

Clean Old Docker
```
docker compose down -v
docker container prune
cd $HOME && rm -rf allora-huggingface-walkthrough
```

### Deployment - Read Carefully! 
## Step 1: 
```bash
git clone https://github.com/allora-network/allora-huggingface-walkthrough
cd allora-huggingface-walkthrough
```
## Step 2: 
```bash
cp config.example.json config.json
nano config.json
```

####  Edit addressKeyName & addressRestoreMnemonic / Copy & Paste Inside config.json
#### Optional: RPC :  https://sentries-rpc.testnet-1.testnet.allora.network/
```bash
{
    "wallet": {
        "addressKeyName": "test",
        "addressRestoreMnemonic": "<your mnemoric phase>",
        "alloraHomeDir": "/root/.allorad",
        "gas": "1000000",
        "gasAdjustment": 1.0,
        "nodeRpc": "https://allora-rpc.testnet-1.testnet.allora.network/",
        "maxRetries": 1,
        "delay": 1,
        "submitTx": false
    },
    "worker": [
        {
            "topicId": 1,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 5,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "ETH"
            }
        },
        {
            "topicId": 3,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 7,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "BTC"
            }
        },
        {
            "topicId": 5,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 9,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "SOL"
            }
        },
        {
            "topicId": 7,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 5,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "ETH"
            }
        },
        {
            "topicId": 8,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 7,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "BNB"
            }
        },
        {
            "topicId": 9,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 9,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "ARB"
            }
        },
        {
            "topicId": 10,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 1,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{blockheight}",
                "Token": "ARB"
            }
        }
        
    ]
}
```
## Step 3: Export 
```bash
chmod +x init.config
./init.config
```
## Step 4: Edit App.py
- Register on Coingecko https://www.coingecko.com/en/developers/dashboard & Create Demo API KEY
- Register on UPSHOT https://developer.upshot.xyz/ & Create Demo API KEY

- Copy & Replace API with your `UPSHOT API` -`COINGECKO API` , then save `Ctrl+X Y ENTER`.
```bash
nano app.py
```
```bash
from flask import Flask, Response
import requests
import json
import pandas as pd
import torch
import random

# create our Flask app
app = Flask(__name__)
        
def get_memecoin_token(blockheight):
    
    upshot_url = f"https://api.upshot.xyz/v2/allora/tokens-oracle/token/{blockheight}"
    headers = {
        "accept": "application/json",
        "x-api-key": "UP-XXXXXXXXXXXXXXXXXXXXXXXXX" # replace with your API key
    }   
    
    response = requests.get(upshot_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        name_token = str(data["data"]["token_id"]) #return "boshi"
        return name_token
    else:
        raise ValueError("Unsupported token") 
    
def get_simple_price(token):
    base_url = "https://api.coingecko.com/api/v3/simple/price?ids="
    token_map = {
        'ETH': 'ethereum',
        'SOL': 'solana',
        'BTC': 'bitcoin',
        'BNB': 'binancecoin',
        'ARB': 'arbitrum'
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-XXXXXXXXXXXXXXXXXXXXXXXXX" # replace with your API key
    }
    token = token.upper()
    if token in token_map:
        url = f"{base_url}{token_map[token]}&vs_currencies=usd"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return str(data[token_map[token]]["usd"])
        
    elif token not in token_map:
        token = token.lower()
        url = f"{base_url}{token}&vs_currencies=usd"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return str(data[token]["usd"])   
           
    else:
        raise ValueError("Unsupported token") 

def get_last_price(token, p):
    
    price_up = p
    price_down = p
    
    token = token.upper()

    if token == 'BTC':
        price_up = float(p)*1.025
        price_down = float(p)*0.98
        return str(format(random.uniform(price_up, price_down), ".2f"))
    
    elif token == 'ETH':
        price_up = float(p)*1.025
        price_down = float(p)*0.98
        return str(format(random.uniform(price_up, price_down), ".2f"))

    elif token == 'SOL':
        price_up = float(p)*1.02
        price_down =float(p)*0.99
        return str(format(random.uniform(price_up, price_down), ".2f"))

    elif token == 'BNB':
        price_up = float(p)*1.025
        price_down =float(p)*0.98  
        return str(format(random.uniform(price_up, price_down), ".2f"))

    elif token == 'ARB':
        price_up = float(p)*1.02
        price_down =float(p)*0.99   
        return str(format(random.uniform(price_up, price_down), ".4f"))
    else:
        return str(p)

# define our endpoint
@app.route("/inference/<string:tokenorblockheight>")
def get_inference(tokenorblockheight):
    
    if tokenorblockheight.isnumeric():
        namecoin = get_memecoin_token(tokenorblockheight)
    else:
        namecoin = tokenorblockheight 
    try:
        return get_last_price(namecoin, get_simple_price(namecoin))
        
    except Exception as e:
        return get_last_price(namecoin, get_simple_price(namecoin))

    
# run our Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

```

## Step 5: Edit requirements.txt
```bash
nano requirements.txt
```
#- Copy & Paste, then save `Ctrl+X Y ENTER`.

```
flask[async]
gunicorn[gthread]
transformers[torch]
pandas
torch==2.0.1 
python-dotenv
requests==2.31.0
```
## Step 6: Build
```bash
docker compose up --build -d
```

## Check your wallet here: http://worker-tx.nodium.xyz/
![image](https://github.com/user-attachments/assets/6e9ce7fd-fdf5-40d2-98f9-d20eb8486fce)

Congrats! Join our Discord if you having problem with the setup https://discord.gg/r6PPSjRZec







