import yaml
from typing import Dict, Any, List, Optional
from pydantic import ValidationError
from runtime.graph.schemas import WorkflowSpec
from runtime.graph.graph import Graph, GraphError
from runtime.nodes.catalog import NodeRegistry
from runtime.logger import get_logger

logger = get_logger("nexusguard.runtime.graph.builder")

class WorkflowBuilder:
    """Parses workflow configurations, instantiates Nodes, and validates the executable DAG structure."""

    @classmethod
    def from_yaml(cls, yaml_content: str) -> Graph:
        """Parse workflow from a YAML string, validate schema, and build the Graph."""
        try:
            data = yaml.safe_load(yaml_content)
        except Exception as e:
            raise GraphError(f"Invalid YAML syntax: {e}")
        
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, spec_dict: Dict[str, Any]) -> Graph:
        """Validate the workflow dictionary with Pydantic and construct/validate the Graph."""
        try:
            # Validate with Pydantic WorkflowSpec
            spec = WorkflowSpec(**spec_dict)
        except ValidationError as e:
            raise GraphError(f"Workflow configuration schema validation failed: {e}")

        graph = Graph()

        # 1. Instantiate and add all nodes
        for node_spec in spec.nodes:
            # Instantiate via catalog NodeRegistry (avoids singleton assumptions)
            try:
                node_instance = NodeRegistry.create(node_spec.type, **node_spec.config)
            except Exception as e:
                raise GraphError(f"Failed to instantiate node '{node_spec.id}' of type '{node_spec.type}': {e}")
            
            graph.add_node(node_spec.id, node_instance)

        # 2. Add edges (connections)
        for edge_spec in spec.edges:
            graph.add_edge(edge_spec.src, edge_spec.dst)

        # 3. Structural validation (Kahn's topo-sort, types)
        graph.validate()

        # 4. Check for isolated nodes (nodes with no incoming/outgoing connections)
        if len(graph.nodes) > 1:
            connected_nodes = set()
            for edge in graph.edges:
                connected_nodes.add(edge.src_node)
                connected_nodes.add(edge.dst_node)
            
            isolated_nodes = set(graph.nodes.keys()) - connected_nodes
            if isolated_nodes:
                raise GraphError(f"Workflow contains isolated nodes with no connections: {list(isolated_nodes)}")

        return graph
