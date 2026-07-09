#!/usr/bin/env python3
import sys
import os
import argparse
import yaml
from runtime.plugins import plugin_registry
from runtime.graph.builder import WorkflowBuilder
from runtime.graph.executor import run_graph
from runtime.logger import get_logger

logger = get_logger("nexusguard.cli")

def list_plugins():
    plugin_registry.discover_and_load()
    plugins = plugin_registry.query_plugins()
    if not plugins:
        print("No pluggable extensions loaded.")
        return
    print("--- Loaded Extensions/Plugins ---")
    for p in plugins:
        print(f"Name: {p['name']} | Version: {p['version']} | Author: {p['author']}")
        print(f"  Description: {p['description']}")
        print(f"  Supported Inputs: {p['supported_inputs']}")
        print(f"  Supported Outputs: {p['supported_outputs']}\n")

def list_workflows():
    config_dir = "config"
    if not os.path.exists(config_dir):
        print(f"No config directory found at './{config_dir}'.")
        return
    print("--- Configured Workflows ---")
    for file in os.listdir(config_dir):
        if file.endswith((".yaml", ".yml")):
            print(f"- config/{file}")

def validate_workflow(filepath: str) -> bool:
    # Discover plugins first so custom nodes register
    plugin_registry.discover_and_load()
    
    print(f"Validating workflow spec: '{filepath}'...")
    try:
        with open(filepath, "r") as f:
            content = f.read()
        graph = WorkflowBuilder.from_yaml(content)
        print("✅ Workflow structure is valid! (Cycle-free, compatible port types)")
        return True
    except Exception as e:
        print(f"❌ Workflow validation failed: {e}")
        return False

def run_workflow(filepath: str):
    if not validate_workflow(filepath):
        sys.exit(1)
    
    # Load and execute workflow
    with open(filepath, "r") as f:
        content = f.read()
    graph = WorkflowBuilder.from_yaml(content)
    
    print("Executing single-pass traversal...")
    try:
        # Load vision packages so standard nodes register
        import vision
        results = run_graph(graph)
        print("--- Execution Complete ---")
        for nid, res in results.items():
            print(f"Node '{nid}' execution output ports: {list(res.outputs.keys())}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="NexusGuard CV Workflow Framework CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-plugins", help="List all dynamically loaded extensions.")
    subparsers.add_parser("list-workflows", help="List configured YAML workflows.")
    
    val_parser = subparsers.add_parser("validate-workflow", help="Validate workflow structure and ports.")
    val_parser.add_argument("filepath", type=str, help="Path to the workflow YAML file.")

    run_parser = subparsers.add_parser("run-workflow", help="Execute single-pass graph workflow.")
    run_parser.add_argument("filepath", type=str, help="Path to the workflow YAML file.")

    args = parser.parse_args()

    if args.command == "list-plugins":
        list_plugins()
    elif args.command == "list-workflows":
        list_workflows()
    elif args.command == "validate-workflow":
        validate_workflow(args.filepath)
    elif args.command == "run-workflow":
        run_workflow(args.filepath)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
