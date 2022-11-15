#!/bin/sh

if [ ! -d "./venv" ]
then
    echo "Virtual environment not found, running initial setup!"

    pip3 install virtualenv
    python3 -m venv venv
    source ./venv/bin/activate
    pip3 install -r requirements.txt
fi

source ./venv/bin/activate
./web_check.py
