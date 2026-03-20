import asyncio
import websockets
import json
import logging
from typing import Callable, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpstoxMarketData:
    """
    WebSocket client for receiving real-time tick data from Upstox.
    """
    def __init__(self, api_client):
        """
        api_client: An instance of UpstoxAPI to fetch the authorized WebSocket URL.
        """
        self.api_client = api_client
        self.ws_url: Optional[str] = None
        self.connection = None
        self.on_tick_callback: Optional[Callable] = None
        self._running = False

    def get_authorized_ws_url(self) -> str:
        """
        Calls the Upstox API to get the authorized WebSocket URL.
        Uses V3 as V2 is deprecated.
        """
        response = self.api_client._request('GET', '/feed/market-data-feed/authorize', version='v3')
        if 'data' in response and 'authorizedRedirectUri' in response['data']:
            return response['data']['authorizedRedirectUri']
        raise ValueError(f"Failed to get authorized URL: {response}")

    def on_tick(self, callback: Callable):
        """
        Registers a callback function to handle incoming ticks.
        """
        self.on_tick_callback = callback

    async def connect_and_subscribe(self, instrument_tokens: List[str]):
        """
        Connects to the WebSocket and subscribes to instruments immediately after.
        """
        self.ws_url = self.get_authorized_ws_url()
        self._running = True
        
        logger.info(f"Connecting to Upstox WebSocket...")
        async with websockets.connect(self.ws_url) as websocket:
            self.connection = websocket
            logger.info("Connected to Market Data Feed!")
            
            # Subscribe immediately after connecting
            await self.subscribe(instrument_tokens)
            
            # Start listening
            await self._listen()

    async def connect(self):
        """
        Legacy connect method. Use connect_and_subscribe for live trades.
        """
        self.ws_url = self.get_authorized_ws_url()
        self._running = True
        
        logger.info(f"Connecting to Upstox WebSocket...")
        async with websockets.connect(self.ws_url) as websocket:
            self.connection = websocket
            logger.info("Connected to Market Data Feed!")
            await self._listen()
            
    async def _listen(self):
        """
        Listens to messages continuously until stopped.
        """
        import upstox_client.feeder.proto.MarketDataFeedV3_pb2 as pb
        from google.protobuf.json_format import MessageToDict
        
        try:
            while self._running:
                message = await self.connection.recv()
                
                if self.on_tick_callback:
                    try:
                        # Decode the binary protobuf message
                        feed_response = pb.FeedResponse()
                        feed_response.ParseFromString(message)
                        
                        # Convert to standard Python Dictionary for easy use in strategies
                        tick_dict = MessageToDict(feed_response)
                        
                        self.on_tick_callback(tick_dict)
                    except Exception as decode_err:
                        logger.error(f"Failed to decode Protobuf: {decode_err}")
                        # Fallback to passing raw bytes if decode fails
                        self.on_tick_callback(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed.")
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
        finally:
            self._running = False

    async def subscribe(self, instrument_tokens: List[str]):
        """
        Sends a subscription message for given instrument tokens.
        """
        if not self.connection:
            raise ConnectionError("WebSocket is not connected.")
        
        # Payload structure depends on the exact Upstox v2 specs
        payload = {
            "guid": "subscription_1",
            "method": "sub",
            "data": {
                "mode": "full", # 'full' or 'ltp'
                "instrumentKeys": instrument_tokens
            }
        }
        # WebSocket API generally expects data to be sent inside a binary frame or specific format.
        # This is a sample text JSON send.
        await self.connection.send(json.dumps(payload).encode('utf-8'))
        logger.info(f"Subscribed to {instrument_tokens}")
        
    def stop(self):
        """
        Stops the listener loop.
        """
        self._running = False
