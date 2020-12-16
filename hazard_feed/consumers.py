import json
from channels.generic.websocket import AsyncWebsocketConsumer
import datetime
import requests
from django.urls import reverse
from urllib.parse import urlunsplit


class TestConsumer(AsyncWebsocketConsumer):
    group_name = 'weather_hazard'

    async def connect(self):

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
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