import os
import json
from ExecutionNode import ExecutionNode
from ValidationNode import ValidationNode
from ManagingNode import ManagingNode

def load_execution_nodes(filename="execution_nodes.json"):
    """Load execution nodes from a JSON file."""
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
        return [ExecutionNode(node["name"], node["description"], node["reputation_score"]) for node in data]

def main():
    print("=== AI Agent Network Simulation Using OpenAI API with Enhanced Reasoning ===\n")
    
    # Load execution nodes from JSON
    execution_nodes = load_execution_nodes()

    manager = ManagingNode(execution_nodes)
    
    print("Enter a complex computational task: ")
    complex_task = input().strip()
    if not complex_task:
        print("No task provided. Exiting simulation.")
        return
    
    final_answer = manager.process_complex_task(complex_task)
    
    print("\n=== Final Synthesized Answer ===\n")
    print(final_answer)

if __name__ == "__main__":
    main()