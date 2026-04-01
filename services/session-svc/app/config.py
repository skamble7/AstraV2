from __future__ import annotations
import os
from pydantic import BaseModel


class Settings(BaseModel):
    # App
    app_name: str = "ASTRA Session Service"
    host: str = "0.0.0.0"
    port: int = 9029

    # Mongo
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "astra")

    # RabbitMQ
    rabbitmq_uri: str = os.getenv("RABBITMQ_URI", "amqp://raina:raina@localhost:5672/")
    rabbitmq_exchange: str = os.getenv("RABBITMQ_EXCHANGE", "raina.events")

    events_org: str = os.getenv("EVENTS_ORG", "astra")
    service_name: str = os.getenv("SERVICE_NAME", "session-svc")


settings = Settings()
