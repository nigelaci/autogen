import json
import uuid
from unittest.mock import Mock, patch

import pytest
from openai import AzureOpenAI

from autogen.logger.logger_factory import LoggerFactory
from autogen.logger.logger_utils import get_current_ts, to_dict
from autogen.runtime_logging import log_chat_completion, start, stop

# Sample data for testing
SAMPLE_CHAT_REQUEST = json.loads(
    """
{
    "messages": [
        {
            "content": "Can you explain the difference between eigenvalues and singular values again?",
            "role": "assistant"
        }
    ],
    "model": "gpt-4"
}
"""
)

SAMPLE_CHAT_RESPONSE = json.loads(
    """
{
    "id": "chatcmpl-8k57oSg1fz2JwpMcEOWMqUvwjf0cb",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "Eigenvalues are...",
                "role": "assistant"
            }
        }
    ],
    "model": "gpt-4"
}
"""
)

@pytest.fixture(scope="function")
def cosmos_db_setup():
    autogen_logger = Mock()
    autogen_logger.log_queue.put = Mock()

    config = {
        "connection_string": "AccountEndpoint=https://example.documents.azure.com:443/;AccountKey=dGVzdA==",
        "database_id": "TestDatabase",
        "container_id": "TestContainer",
    }

    # Patch the get_logger method of the LoggerFactory object
    with patch.object(LoggerFactory, 'get_logger', return_value=autogen_logger):
        start(logger_type="cosmos", config=config)
        yield autogen_logger
        stop()

class TestCosmosDBLogging:
    def get_sample_chat_completion(self, response):
        return {
            "invocation_id": str(uuid.uuid4()),
            "client_id": 140609438577184,
            "wrapper_id": 140610167717744,
            "request": SAMPLE_CHAT_REQUEST,
            "response": response,
            "is_cached": 0,
            "cost": 0.347,
            "start_time": get_current_ts(),
        }

    @pytest.mark.usefixtures("cosmos_db_setup")
    def test_log_completion_cosmos(self, cosmos_db_setup):
        sample_completion = self.get_sample_chat_completion(SAMPLE_CHAT_RESPONSE)
        print("Testing log_chat_completion with sample data:", sample_completion) # For debugging
        log_chat_completion(**sample_completion)
        print("log_chat_completion should have been called") # For debugging

        assert cosmos_db_setup.log_chat_completion.called, "log_chat_completion was not called"

        print("About to check queue.put call") # For debugging
        cosmos_db_setup.log_queue.put.assert_called_once_with({
            "type": "chat_completion",
            "invocation_id": sample_completion["invocation_id"],
            "client_id": sample_completion["client_id"],
            "wrapper_id": sample_completion["wrapper_id"],
            "session_id": cosmos_db_setup.session_id,  # Ensure session_id is handled correctly
            "request": sample_completion["request"],
            "response": SAMPLE_CHAT_RESPONSE,
            "is_cached": sample_completion["is_cached"],
            "cost": sample_completion["cost"],
            "start_time": sample_completion["start_time"],
            "end_time": get_current_ts(),
        })
        print("Queue.put call check completed") # For debugging
