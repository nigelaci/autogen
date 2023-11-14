import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Union
from pydantic.dataclasses import dataclass
from dataclasses import field


@dataclass
class Message(object):
    user_id: str
    role: str
    content: str
    root_msg_id: Optional[str] = None
    msg_id: Optional[str] = None
    timestamp: Optional[datetime] = None 
    personalize: Optional[bool] = False
    ra: Optional[str] = None
    code: Optional[str] = None
    metadata: Optional[Any] = None

    def __post_init__(self):
        if self.msg_id is None:
            self.msg_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def dict(self):
        return {
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "root_msg_id": self.root_msg_id,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp, 
            "personalize": self.personalize,
            "ra": self.ra,
            "code": self.code,
            "metadata": self.metadata,
        }

# web api data models

@dataclass
class DeleteMessageModel(object):
    user_id: str
    msg_id: str


@dataclass
class ClearDBModel(object):
    user_id: str

# autogenflow data models
@dataclass
class ModelConfig:
    """Data model for Model Config item in LLMConfig for Autogen"""

    model: str
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    api_base: Optional[str] = None

@dataclass
class LLMConfig:
    """Data model for LLM Config for Autogen"""

    seed: int = 42
    config_list: List[ModelConfig] = field(default_factory=List)   
    temperature: float = 0 
    request_timeout: Optional[int] = None


@dataclass
class AgentConfig:
    """Data model for Agent Config for Autogen"""

    name: str
    llm_config: LLMConfig
    human_input_mode: str = "NEVER"
    max_consecutive_auto_reply: int = 10
    system_message: Optional[str] = None
    is_termination_msg: Optional[Union[bool, str, Callable]] = None
    code_execution_config: Optional[Union[bool, str, Dict[str, Any]]] = None


@dataclass
class AgentFlowSpec:
    """Data model to help flow load agents from config"""

    type: Literal["assistant", "userproxy", "groupchat"]
    config: AgentConfig = field(default_factory=AgentConfig)


@dataclass
class FlowConfig:
    """Data model for Flow Config for Autogen"""

    name: str
    sender: AgentFlowSpec
    receiver: Union[AgentFlowSpec, List[AgentFlowSpec]]
    type: Literal["default", "groupchat"] = "default"



