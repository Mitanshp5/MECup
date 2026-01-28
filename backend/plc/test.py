try:
    import requests
    import sys

    url = "http://localhost:5001/plc/write"
    payload = {
        "device": "M77",
        "value": 1
    }
    response = requests.post(url, json=payload)
    print(response.json())
except:
    import rk_mcprotocol as mc
    sock= mc.open_socket('192.168.1.30',5000)
    mc.write_bit(sock,'Y1',[1])
    print(mc.read_bit(sock,'Y1',1))