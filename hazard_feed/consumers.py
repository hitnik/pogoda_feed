from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .utils import get_actial_hazard_feeds


class WeatherJsonConsumer(AsyncJsonWebsocketConsumer):
    group_name = 'weather'

    async def connect(self):

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        feeds = await get_actial_hazard_feeds()
        if feeds:
            await self.channel_layer.send(self.channel_name,
                {
                    'type': 'weather.notify',
                    'content': feeds
                }
            )

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from room group
    async def weather_notify(self, event):
        content = event['content']

        # Send message to WebSocket
        await self.send_json(content=content)