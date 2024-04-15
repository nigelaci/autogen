from __future__ import annotations

import logging
import time
import threading
import queue
import uuid


from typing import TYPE_CHECKING, Any, Dict, TypedDict, Union

from azure.cosmos import CosmosClient, exceptions
from openai import AzureOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from autogen.logger.base_logger import BaseLogger
from autogen.logger.logger_utils import get_current_ts, to_dict

if TYPE_CHECKING:
    from autogen import ConversableAgent, OpenAIWrapper

__all__ = ("CosmosDBLogger",)

logger = logging.getLogger(__name__)


class CosmosDBConfig(TypedDict):
    connection_string: str
    database_id: str  # Optional key, hence not enforcing it as mandatory
    container_id: str  # Optional key, hence not enforcing it as mandatory


class CosmosDBLogger(BaseLogger):
    def __init__(self, config: CosmosDBConfig):
        self.config = config
        self.client = CosmosClient.from_connection_string(config["connection_string"])
        self.database_id = config.get("database_id", "AutogenLogging")
        self.database = self.client.get_database_client(self.database_id)
        self.container_id = config.get("container_id", "Logs")
        self.container = self.database.get_container_client(self.container_id)
        self.session_id = str(uuid.uuid4())
        self.log_queue = queue.Queue()
        self.logger_thread = threading.Thread(target=self._process_log_queue)
        
        self.logger_thread.daemon = True
        
        self.logger_thread.start()

    def start(self) -> str:
        try:
            self.database.create_container_if_not_exists(id=self.container_id, partition_key="/session_id")
        except Exception as e:
            logger.error(f"Failed to create or access container {self.container_id}: {e}")
        return self.session_id

    def _worker(self):
        while True:
            try:
                item = self.log_queue.get()
                if item is None:
                    break  # None is a signal to stop the worker thread
                self._process_log_entry(item)
            finally:
                self.log_queue.task_done()

    def _process_log_entry(self, document: Dict[str, Any]):
        try:
            self.container.upsert_item(document)
        except Exception as e:
            logger.error(f"Failed to upsert document: {e}")

    def log_chat_completion(
        self,
        invocation_id: uuid.UUID,
        client_id: int,
        wrapper_id: int,
        request: Dict[str, Any],
        response: Union[str, ChatCompletion],
        is_cached: int,
        cost: float,
        start_time: str,
    ) -> None:
        document = {
            "type": "chat_completion",
            "invocation_id": str(invocation_id),
            "client_id": client_id,
            "wrapper_id": wrapper_id,
            "session_id": self.session_id,
            "request": to_dict(request),
            "response": to_dict(response),
            "is_cached": is_cached,
            "cost": cost,
            "start_time": start_time,
            "end_time": get_current_ts(),
        }
        self.log_queue.put(document)

    def log_new_agent(self, agent: ConversableAgent, init_args: Dict[str, Any]) -> None:
        document = {
            "type": "new_agent",
            "session_id": self.session_id,
            "agent_id": id(agent),
            "agent_name": agent.name,
            "init_args": to_dict(init_args),
            "timestamp": get_current_ts(),
        }
        self.container.upsert_item(document)

    def log_new_wrapper(self, wrapper: OpenAIWrapper, init_args: Dict[str, Any]) -> None:
        document = {
            "type": "new_wrapper",
            "session_id": self.session_id,
            "wrapper_id": id(wrapper),
            "init_args": to_dict(init_args),
            "timestamp": get_current_ts(),
        }
        self.log_queue.put(document)

    def log_new_client(self, client: Any, wrapper: OpenAIWrapper, init_args: Dict[str, Any]) -> None:
        document = {
            "type": "new_client",
            "session_id": self.session_id,
            "client_id": id(client),
            "wrapper_id": id(wrapper),
            "client_class": type(client).__name__,
            "init_args": to_dict(init_args),
            "timestamp": get_current_ts(),
        }
        self.log_queue.put(document)

    def stop(self) -> None:
        self.log_queue.put(None)  # Signal to stop the worker thread
        self.worker_thread.join()  # Wait for the worker thread to finish

    def get_connection(self) -> None:
        # Cosmos DB connection management is handled by the SDK.
        return None
