from fastapi import FastAPI
import taskiq_fastapi

from app.modules.stream.infrastructure.broker import stream_broker

app = FastAPI()

taskiq_fastapi.init(stream_broker, "app.api.main:app")
