# Hiev-Mind: AI Agent Network Simulation

Hiev-Mind is a modular AI agent network simulation that leverages the OpenAI API to perform complex computational tasks through enhanced reasoning, task decomposition, and iterative self-improvement. The project demonstrates how multiple specialized AI agents (execution nodes) and evaluation agents (validation nodes) can collaborate to solve challenging tasks by decomposing them into manageable subtasks, processing each with specialized expertise, and synthesizing a final, coherent answer.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Overview

Hiev-Mind simulates an AI agent network in which:
- **Execution Nodes** perform specialized tasks (e.g., arithmetic, reasoning, data analysis).
- **Validation Nodes** assess the quality of responses using an Agent-as-a-Judge framework.
- **Managing Node** orchestrates the task delegation, dependency management, and result synthesis by:
  - Decomposing a complex task into subtasks.
  - Assigning suitable execution nodes based on task requirements.
  - Validating agent responses and iteratively refining outputs.
  - Synthesizing the final answer from validated subtask responses.

---

## Features

- **Task Decomposition:** Automatically splits a complex task into dependent subtasks.
- **Specialized Execution:** Uses multiple execution nodes with domain-specific expertise.
- **Iterative Self-Improvement:** Agents can reprocess tasks with self-critique if initial responses are unsatisfactory.
- **Concurrent Processing:** Uses thread pools to execute tasks and validations concurrently.
- **Integrated Validation:** Evaluates responses using chain-of-thought analysis and provides feedback for improvements.
- **Final Synthesis:** Combines validated responses into a coherent final answer.

---

## Directory Structure

hiev-mind/
─ config.py                # API configuration and default settings
─ ExecutionNode.py         # Defines the ExecutionNode class for processing tasks
─ structure.py             # Utility for scanning directory structure and text files (optional)
─ ManagingNode.py          # Manages task delegation, validation, and synthesis
─ execution_nodes.json     # JSON configuration for available execution nodes
─ main.py                  # Entry point for running the simulation
─ ValidationNode.py        # Defines the ValidationNode class for evaluating responses

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/hiev-mind.git
   cd hiev-mind
   ```

2.	Create and Activate a Virtual Environment:

    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use: venv\Scripts\activate
    ```


3.	Install Dependencies:

    ```bash
    # Hiev-Mind requires the OpenAI Python client. Install it using pip
    pip install openai
    ```

    Usage
	
    1.	Set the OpenAI API Key:

    ```bash
    #  Make sure to set your OpenAI API key as an environment variable
    export OPENAI_API_KEY='your-openai-api-key'
    ```

	2.	Run the Simulation:
    ```bash
    # Execute the main script
    python main.py
    ```

	3.	Enter a Complex Task:
When prompted, input a complex computational or reasoning task. The system will decompose the task, delegate subtasks to specialized agents, validate the responses, and finally synthesize a comprehensive answer.

Configuration
	•	API Key and Model Settings:
In config.py, the OpenAI API key is loaded from the OPENAI_API_KEY environment variable. The default model is set to gpt-4o.
	•	Execution Nodes:
The file execution_nodes.json contains a list of execution nodes with their names, domain-specific descriptions, and reputation scores.
	•	Text File Scanner (Optional):
The script structure.py provides utilities to generate a directory scan and read contents from text files. This functionality can be used for additional project analysis or documentation purposes.

How It Works
	1.	Task Decomposition:
The ManagingNode.analyze_task() method uses the OpenAI API to decompose a complex task into base-level subtasks with dependencies.
	2.	Agent Delegation:
The manager assigns subtasks to the best-suited execution nodes using the assign_execution_nodes() method, which considers both the agent’s description and reputation score.
	3.	Concurrent Task Processing:
Subtasks are processed concurrently by the chosen execution nodes, and responses are validated by multiple validation nodes.
	4.	Iterative Improvement:
If the initial responses do not meet the quality threshold, the agent is prompted to improve its answer through self-critique and reprocessing.
	5.	Final Synthesis:
The validated responses are synthesized into a final answer by the compile_final_answer() method.

Future Improvements
	•	Enhanced Error Handling: Improve resilience against API failures and edge cases.
	•	Dynamic Node Configuration: Allow dynamic addition and removal of agents during runtime.
	•	Advanced Metrics: Incorporate more detailed evaluation metrics and logging for better insight.
	•	User Interface: Develop a web or desktop interface for easier interaction with the system.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Happy Computing!

