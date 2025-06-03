import asyncio
import json
from data_layer.cache.redis_client import redis_client
from fastapi.encoders import jsonable_encoder


class PubSubManager:
    def __init__(self):
        self.tasks = {}  # user_id -> (pubsub, task)

    async def subscribe(self, user_id, callback):
        channel = f"dashboard_updates:{user_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        async def reader():
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    await callback(message['data'])
        task = asyncio.create_task(reader())
        self.tasks[user_id] = (pubsub, task)

    async def unsubscribe(self, user_id):
        if user_id in self.tasks:
            pubsub, task = self.tasks[user_id]
            await pubsub.unsubscribe()
            task.cancel()
            del self.tasks[user_id]

    async def publish(self, user_id, event, data):
        channel = f"dashboard_updates:{user_id}"
        serializable_data = jsonable_encoder(data)
        await redis_client.publish(channel, json.dumps({"event": event, "data": serializable_data}))


pubsub_manager = PubSubManager()
