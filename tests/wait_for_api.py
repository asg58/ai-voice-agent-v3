import time
import requests

def wait_for_api(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print("API is up!")
                return True
        except Exception:
            pass
        print("Wachten op API...")
        time.sleep(2)
    raise TimeoutError(f"API niet bereikbaar op {url} na {timeout} seconden.")

if __name__ == "__main__":
    wait_for_api("http://localhost:8080/health")
    print("API healthcheck geslaagd.")
