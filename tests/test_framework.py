import pytest
import os
from runtime.plugins import plugin_registry, PluginRegistry
from runtime.nodes.catalog import NodeRegistry
from runtime.graph.builder import WorkflowBuilder
from runtime.graph.graph import GraphError, build
from runtime.nodes.node import BaseNode, NodeResult, PortSpec

# Define test-specific nodes
class MockInputNode(BaseNode):
    name = "mock_input"
    outputs = (PortSpec("data", str),)
    def run(self, inputs: dict) -> NodeResult:
        return NodeResult(outputs={"data": "test_string"})

class MockProcessingNode(BaseNode):
    name = "mock_processing"
    inputs = (PortSpec("data", str),)
    outputs = (PortSpec("result", str),)
    def run(self, inputs: dict) -> NodeResult:
        return NodeResult(outputs={"result": inputs["data"].upper()})

class MockIncompatibleNode(BaseNode):
    name = "mock_incompatible"
    inputs = (PortSpec("data", int),)  # Int instead of Str
    outputs = (PortSpec("result", int),)
    def run(self, inputs: dict) -> NodeResult:
        return NodeResult(outputs={"result": inputs["data"] * 2})

# Register test-specific nodes to catalog NodeRegistry
NodeRegistry.register("mock_input")(MockInputNode)
NodeRegistry.register("mock_processing")(MockProcessingNode)
NodeRegistry.register("mock_incompatible")(MockIncompatibleNode)


def test_node_registry_registration():
    assert "mock_input" in NodeRegistry.available()
    assert "mock_processing" in NodeRegistry.available()
    assert NodeRegistry.get("mock_input") == MockInputNode


def test_workflow_builder_successful_compilation():
    yaml_config = """
    name: test_successful_dag
    version: 1
    nodes:
      - id: src
        type: mock_input
      - id: proc
        type: mock_processing
    edges:
      - src: src.data
        dst: proc.data
    """
    graph = WorkflowBuilder.from_yaml(yaml_config)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    # Verify topological order is computed cycle-free
    assert graph.topological_order() == ["src", "proc"]


def test_workflow_builder_cycle_detection():
    yaml_config = """
    name: cyclic_dag
    version: 1
    nodes:
      - id: node_a
        type: mock_processing
      - id: node_b
        type: mock_processing
    edges:
      - src: node_a.result
        dst: node_b.data
      - src: node_b.result
        dst: node_a.data
    """
    with pytest.raises(GraphError, match="graph contains a cycle"):
        WorkflowBuilder.from_yaml(yaml_config)


def test_workflow_builder_type_compatibility_checks():
    yaml_config = """
    name: incompatible_ports_dag
    version: 1
    nodes:
      - id: src
        type: mock_input
      - id: proc
        type: mock_incompatible
    edges:
      - src: src.data
        dst: proc.data
    """
    with pytest.raises(GraphError, match="type mismatch"):
        WorkflowBuilder.from_yaml(yaml_config)


def test_workflow_builder_isolated_nodes():
    yaml_config = """
    name: isolated_nodes_dag
    version: 1
    nodes:
      - id: src
        type: mock_input
      - id: proc
        type: mock_processing
      - id: isolated
        type: mock_input
    edges:
      - src: src.data
        dst: proc.data
    """
    with pytest.raises(GraphError, match="isolated nodes"):
        WorkflowBuilder.from_yaml(yaml_config)


def test_reusable_components_across_multiple_graphs():
    # Instantiating the builder multiple times should allow the same type to be instantiated independently
    yaml_1 = """
    nodes:
      - id: src_1
        type: mock_input
    """
    yaml_2 = """
    nodes:
      - id: src_2
        type: mock_input
    """
    g1 = WorkflowBuilder.from_yaml(yaml_1)
    g2 = WorkflowBuilder.from_yaml(yaml_2)
    assert g1.nodes["src_1"].node != g2.nodes["src_2"].node


def test_plugin_registry_and_discovery(tmp_path):
    # Simulate a dynamic plugin file on disk
    plugin_file = tmp_path / "test_dummy_plugin.py"
    plugin_content = """
from runtime.nodes.catalog import register
from runtime.nodes.node import BaseNode, NodeResult, PortSpec

PLUGIN_METADATA = {
    "name": "DummyPlugin",
    "version": "2.1.0",
    "author": "Test",
    "description": "Dummy mock plugin.",
    "supported_inputs": [],
    "supported_outputs": [],
}

@register("dummy_plugin")
class DummyPlugin(BaseNode):
    def run(self, inputs: dict) -> NodeResult:
        return NodeResult(outputs={})
"""
    plugin_file.write_text(plugin_content)
    
    reg = PluginRegistry(plugins_dir=str(tmp_path))
    reg.discover_and_load()
    
    assert "test_dummy_plugin" in reg.loaded_plugins
    assert "dummy_plugin" in NodeRegistry.available()
    
    # Reload/Unload test
    reg.unload_plugin("test_dummy_plugin")
    assert "test_dummy_plugin" not in reg.loaded_plugins
