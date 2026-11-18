
import concurrent.futures
import time
import requests

URL = "http://127.0.0.1:5000/"

TOTAL_REQUESTS = 3000
CONCURRENT_WORKERS = 50

def send_request(_):
    try:
        response = requests.get(URL, timeout=10)
        return response.status_code
    except requests.RequestException as error:
        return str(error)

print("Starting load test...")

start = time.time()

with concurrent.futures.ThreadPoolExecutor(
    max_workers=CONCURRENT_WORKERS
) as executor:
    results = list(executor.map(send_request, range(TOTAL_REQUESTS)))

elapsed = time.time() - start

successful = results.count(200)

print(f"Total requests: {TOTAL_REQUESTS}")
print(f"Successful requests: {successful}")
print(f"Failed requests: {TOTAL_REQUESTS - successful}")
print(f"Time taken: {elapsed:.2f} seconds")
