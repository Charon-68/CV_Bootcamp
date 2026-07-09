import yaml
import sys
import vision  # To trigger node registration
from runtime.graph.graph import Graph, build

def main():
    print("Loading workflow from config/workflow.yaml...")
    try:
        with open("config/workflow.yaml", "r") as f:
            workflow = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config/workflow.yaml not found.")
        sys.exit(1)
        
    try:
        graph = build(workflow)
        print("✅ Graph validation successful! No cycles found, all edges match port schemas.")
    except Exception as e:
        print(f"❌ Graph validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
