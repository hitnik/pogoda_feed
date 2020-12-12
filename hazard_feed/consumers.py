# chat/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class TestConsumer(WebsocketConsumer):
    group_name = 'weather_hazard'

    def connect(self):
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'ch_message',
                'message': message
            }
        )

    # Receive message from room group
    def ch_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))