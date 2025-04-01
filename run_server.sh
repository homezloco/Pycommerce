#!/bin/bash
# Run the uvicorn server 
cd /home/runner/workspace
python -m uvicorn web_server:app --host 0.0.0.0 --port 5000 --reload