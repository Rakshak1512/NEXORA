import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class CollectorConfig(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    COLLECTOR_ID: str = "col-prod-core-01"
    COLLECTOR_NAME: str = "Primary Cluster Collector 01"
    TENANT_ID: str = "11111111-1111-1111-1111-111111111111"
    BACKEND_URL: str = "http://127.0.0.1:8000"
    COLLECTOR_CREDENTIAL: str = "secret-collector-token-01"
    COLLECTION_INTERVAL_SECONDS: int = 5
    HEARTBEAT_INTERVAL_SECONDS: int = 15
    LOCAL_QUEUE_PATH: str = os.path.join(os.path.dirname(__file__), "..", "data", "local_buffer.db")
    MAX_RETRY_ATTEMPTS: int = 5
    BACKOFF_FACTOR: float = 1.5
    VERSION: str = "1.4.2"
    SIMULATED_MODE: bool = False

config = CollectorConfig()
