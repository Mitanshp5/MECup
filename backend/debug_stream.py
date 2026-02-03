import requests

def test_stream():
    try:
        url = "http://localhost:5001/camera/stream"
        print(f"Connecting to {url}...")
        # stream=True to avoid downloading infinite data
        with requests.get(url, stream=True, timeout=5) as r:
            print(f"Status Code: {r.status_code}")
            print(f"Headers: {r.headers}")
            if r.status_code == 200:
                print("Reading first 1024 bytes...")
                chunk = next(r.iter_content(chunk_size=1024))
                print(f"Received {len(chunk)} bytes.")
                print(f"Start of data: {chunk[:50]}")
            else:
                print("Stream failed.")
                
    except Exception as e:
        print(f"Error reading stream: {e}")

if __name__ == "__main__":
    test_stream()
