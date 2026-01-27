import requests
import sys

url = "http://localhost:5001/plc/write"
payload = {
    "device": "Y1",
    "value": 1
}
response = requests.post(url, json=payload)