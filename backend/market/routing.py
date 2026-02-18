"""WebSocket URL routing for market and system events."""

from django.urls import path

from market.consumers import MarketTickerConsumer, SystemEventsConsumer

websocket_urlpatterns = [
    path("ws/market/tickers/", MarketTickerConsumer.as_asgi()),
    path("ws/system/", SystemEventsConsumer.as_asgi()),
]
