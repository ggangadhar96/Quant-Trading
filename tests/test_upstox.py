import sys
import json
from broker.upstox_api import UpstoxAPI

def check_setup():
    print("Initializing Upstox API client...")
    try:
        with open("config.json", "r") as f:
            token = json.load(f).get("access_token")
    except Exception as e:
        print(f"Failed to load config: {e}")
        return
        
    client = UpstoxAPI(access_token=token)
    print("Client initialized. Fetching profile...")
    
    try:
        profile = client.get_profile()
        print("\nSUCCESS! Profile Data:")
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print(f"Error fetching profile: {e}")

if __name__ == "__main__":
    check_setup()
