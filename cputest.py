
import concurrent.futures
import os
import time
import requests

URL = os.environ.get("LOAD_URL", "http://127.0.0.1:5000/")
TOTAL_REQUESTS = int(os.environ.get("TOTAL_REQUESTS", "10000"))
WORKERS = int(os.environ.get("WORKERS", "50"))

def send_request(_):
    try:
        response = requests.get(URL, timeout=15)
        return response.status_code
    except requests.RequestException:
        return 0

print("Starting controlled load test...")

start = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
    results = list(executor.map(send_request, range(TOTAL_REQUESTS)))

elapsed = time.time() - start

print("Successful:", results.count(200))
print("Failed:", results.count(0))
print("Duration:", round(elapsed, 2), "seconds")
