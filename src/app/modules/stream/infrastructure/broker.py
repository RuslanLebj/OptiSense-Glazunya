from taskiq_redis import ListQueueBroker

from src.app.config import settings

stream_broker = (
    ListQueueBroker(url=settings.REDIS_URL, queue_name=settings.QUEUE_NAME)
)