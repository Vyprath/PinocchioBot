#!/bin/bash
git pull
source venv/bin/activate
pip install -Ur requirements.txt
sudo systemctl restart pinocchio
