import requests

def test_memory_manager_save_and_get():
    base_url = "http://localhost:8080"
    # Save data via MemoryManager
    save_resp = requests.post(
        f"{base_url}/memory/manager/save",
        json={"key": "testkey", "value": "testvalue", "type_": "short_term"}
    )
    assert save_resp.status_code == 200
    # Get data via MemoryManager
    get_resp = requests.get(f"{base_url}/memory/manager/get/short_term/testkey")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["value"] == "testvalue"

if __name__ == "__main__":
    test_memory_manager_save_and_get()
    print("Memory API test passed!")
