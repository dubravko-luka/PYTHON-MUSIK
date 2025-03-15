#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --break-system-packages
echo "Virtual environment activated."