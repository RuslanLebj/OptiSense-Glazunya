from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from app.modules.stream.infrastructure.broker import stream_broker

scheduler = TaskiqScheduler(
    broker=stream_broker,
    sources=[
        LabelScheduleSource(stream_broker),
    ],
)
