import requests
import json
from typing import Optional, Dict, Any

class UpstoxAPI:
    """
    A client for the Upstox v2 API, capable of handling REST requests
    for profile info, order placement, etc.
    """
    BASE_URL = 'https://api.upstox.com/v2'

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        })

    def _request(self, method: str, endpoint: str, 
                 params: Optional[Dict[str, Any]] = None, 
                 data: Optional[Dict[str, Any]] = None,
                 json_payload: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None,
                 version: str = 'v2') -> Any:
        
        # Support for different base versions (e.g., v3)
        base_url = self.BASE_URL.replace('/v2', f'/{version}')
        url = f"{base_url}{endpoint}"
        req_headers = {}
        if headers:
            req_headers.update(headers)

        if json_payload is not None:
            req_headers['Content-Type'] = 'application/json'
        elif data is not None:
            req_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json_payload,
            headers=req_headers
        )
        
        response.raise_for_status()
        return response.json()

    def get_profile(self) -> dict:
        """
        Fetch the user profile.
        GET /user/profile
        """
        return self._request('GET', '/user/profile')

    def place_order(self, order_data: dict) -> dict:
        """
        Place a new order.
        POST /order/place
        Requires application/json Content-Type and JSON payload.
        """
        return self._request('POST', '/order/place', json_payload=order_data)

    def get_order_book(self) -> dict:
        """
        Fetch the order book.
        GET /order/retrieve-all
        """
        return self._request('GET', '/order/retrieve-all')
