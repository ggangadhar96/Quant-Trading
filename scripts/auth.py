import requests
import urllib.parse
from typing import Dict, Any

class UpstoxAuth:
    """
    Handles the Upstox OAuth 2.0 flow to acquire an access token.
    """
    BASE_URL = 'https://api.upstox.com/v2'

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_login_url(self, state: str = "upstox_auth") -> str:
        """
        Generates the Upstox login URL to redirect the user to.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state
        }
        query_string = urllib.parse.urlencode(params)
        return f"{self.BASE_URL}/login/authorization/dialog?{query_string}"

    def get_access_token(self, code: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code for an access token.
        """
        url = f"{self.BASE_URL}/login/authorization/token"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        return response.json()
