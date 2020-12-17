import json
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from .utils import get_actial_hazard_feeds

class TestConsumer(AsyncWebsocketConsumer):
    group_name = 'weather_hazard'

    async def connect(self):

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        content = await get_actial_hazard_feeds()

        await self.channel_layer.send(self.channel_name,
            {
                'type': 'ch.message',
                'message': 'start'
            }
        )

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            'weather_hazard',
            {
                'type': 'ch.message',
                'message': message
            }
        )

    # Receive message from room group
    async def ch_message(self, event):
        message = event['message']
        print("EVENT TRIGERED")

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class TestJsonConsumer(AsyncJsonWebsocketConsumer):
    group_name = 'weather'

    async def connect(self):

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        feeds = await get_actial_hazard_feeds()

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
        print("EVENT TRIGERED")

        # Send message to WebSocket
        await self.send_json(content=content)