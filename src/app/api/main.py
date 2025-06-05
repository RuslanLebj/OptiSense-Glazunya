from fastapi import FastAPI
import taskiq_fastapi

from app.modules.stream.infrastructure.broker import stream_broker
from app.modules.stream.application.tasks.process_stream import start_processing_stream

app = FastAPI()

taskiq_fastapi.init(stream_broker, "app.api.main:app")
