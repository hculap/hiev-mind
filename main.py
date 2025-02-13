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

    # Create validation nodes
    validation_nodes = [
        ValidationNode("Validator_1"),
        ValidationNode("Validator_2"),
        ValidationNode("Validator_3"),
        ValidationNode("Validator_4"),
        ValidationNode("Validator_5"),
        ValidationNode("Validator_6"),
        ValidationNode("Validator_7"),
    ]
    
    manager = ManagingNode(execution_nodes, validation_nodes)
    
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