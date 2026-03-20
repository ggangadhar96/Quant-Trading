from broker.auth import UpstoxAuth
import sys
import json
import os

def main():
    print("=== Upstox API Auto Login Flow ===")
    print("This script helps you generate the interactive login link and fetch your access token.")
    
    config_path = "config.json"
    if not os.path.exists(config_path):
        print("Error: config.json not found.")
        sys.exit(1)
        
    with open(config_path, "r") as f:
        config = json.load(f)
        
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri")
    
    if not client_id or not client_secret or not redirect_uri:
        print("Error: 'client_id', 'client_secret', and 'redirect_uri' must be set in config.json.")
        sys.exit(1)
        
    auth_client = UpstoxAuth(client_id, client_secret, redirect_uri)
    
    # Step 1: Get Login URL
    login_url = auth_client.get_login_url()
    
    print("\n[STEP 1] Please go to the following URL in your web browser:")
    print("-" * 70)
    print(login_url)
    print("-" * 70)
    
    print("\nAfter successfully logging in, you will be redirected to an empty or broken page.")
    print("Look at the URL in your browser's address bar.")
    print("It will look something like:  https://your-redirect-uri/?code=mk404x&state=upstox_auth")
    
    # Step 2: Get Code from user
    code = input("\n[STEP 2] Copy the 'code' value from the URL and paste it here: ").strip()
    
    if not code:
        print("No code provided. Exiting.")
        sys.exit(1)
        
    # Step 3: Get Access Token
    print("\n[STEP 3] Exchanging authorization code for an access token...")
    try:
        token_response = auth_client.get_access_token(code)
        access_token = token_response.get("access_token")
        
        if access_token:
            config["access_token"] = access_token
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
                
            print("\nSUCCESS! Here is your Access Token:")
            print("=" * 70)
            print(access_token)
            print("=" * 70)
            print("\nThe token has been automatically saved to your config.json file!")
            print("Your application is now ready to run 'python main.py'")
        else:
            print(f"\nResponse did not contain an access_token. Raw response: {token_response}")
            
    except Exception as e:
        print(f"\nFailed to get access token: {e}")

if __name__ == "__main__":
    main()
