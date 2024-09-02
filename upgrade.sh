#!/bin/bash

BOLD="\033[1m"
UNDERLINE="\033[4m"
DARK_YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0;32m"


echo -e "${CYAN}Upgrade Your Allora Model to BiLSTM(TYPE/Y):${RESET}"
read -p "" installdep
echo

if [[ "$installdep" =~ ^[Yy]$ ]]; then

    echo -e "${CYAN}Clone & Replace old file :${RESET}"
    echo
    rm -rf app.py
    rm -rf requirements.txt
    wget -q https://raw.githubusercontent.com/0xScraipa/0gx/blob/LSTM/app.py -O /root/allora-huggingface-walkthrough/app.py
    wget -q https://raw.githubusercontent.com/0xScraipa/0gx/blob/LSTM/requirements.txt -O /root/allora-huggingface-walkthrough/requirements.txt
    wget -q https://raw.githubusercontent.com/0xScraipa/0gx/blob/LSTM/enhanced_bilstm_model.pth -O /root/allora-huggingface-walkthrough/enhanced_bilstm_model.pth
    wait
	
    echo -e "${CYAN}Rebuild and run a model :${RESET}"

    cd /root/allora-huggingface-walkthrough/
    echo
    docker compose up --build -d
    echo
	
    echo
    docker compose logs -f
    echo
	
else
    echo -e "${CYAN}Success :${RESET}"
    
fi

echo
echo -e "==============Allora==============="
