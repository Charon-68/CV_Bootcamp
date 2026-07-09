from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator

class NodeSpec(BaseModel):
    id: str = Field(..., description="Unique identifier for the node instance in the workflow.")
    type: str = Field(..., description="The catalog type of the node (e.g. 'capture', 'clean').")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters for the node.")

class ConnectionSpec(BaseModel):
    src: str = Field(..., description="Source node.port string.")
    dst: str = Field(..., description="Destination node.port string.")

    @field_validator("src", "dst")
    @classmethod
    def validate_port_format(cls, v: str) -> str:
        if "." not in v:
            raise ValueError(f"Port connection '{v}' must use format 'node_id.port_name'")
        return v

class WorkflowSpec(BaseModel):
    name: str = Field(default="anonymous_workflow")
    version: int = Field(default=1)
    nodes: List[NodeSpec] = Field(default_factory=list)
    edges: List[ConnectionSpec] = Field(default_factory=list)
    output: Optional[str] = None
