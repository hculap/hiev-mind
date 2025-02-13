import json
import string
from config import DEFAULT_MODEL, client
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------
# Agent Manager
# ---------------------------
class ManagingNode:
    def __init__(self, execution_nodes, validation_nodes):
        self.execution_nodes = execution_nodes
        self.validation_nodes = validation_nodes

    def analyze_task(self, complex_task):
        """
        Decomposes the complex task into subtasks with dependency information.
        Returns a JSON array of objects with keys: "id", "task", and "dependencies".
        """
        prompt = (
            "Decompose the following complex task into clear, base-level tasks that can be solved by specialized AI agents. "
            "For each task, provide an 'id' (e.g., T1, T2, ...), a 'task' description, and a list of 'dependencies' (other task IDs that must be completed first). "
            "Tasks that can be performed concurrently should have an empty dependencies list. "
            "Return only a RAW JSON TEXT (without 'json' text at the beginning) array of objects with keys 'id', 'task', and 'dependencies'.\n\n"
            f"Complex Task: {complex_task}"
        )
        print("\n[Manager] Decomposing the complex task into dependent subtasks...\n")
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert in task decomposition."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=12000,
            )
            output = response.choices[0].message.content.strip()
            subtasks = json.loads(output)
            if not isinstance(subtasks, list):
                subtasks = [subtasks]
        except Exception as e:
            print(f"Error in task decomposition: {e}")
            subtasks = [{"id": "T1", "task": complex_task, "dependencies": []}]
        print(f"[Manager] Identified subtasks (with dependencies): {subtasks}\n")
        return subtasks

    def compute_match_score(self, subtask, description):
        """
        Computes a match score (from 1 to 10) indicating how well the agent's description fits the subtask.
        """
        prompt = (
            "You are an expert evaluator. Please rate on a scale of 1 to 10 how well the following "
            "agent description matches the given subtask. Provide only the number as your answer.\n\n"
            f"Subtask: {subtask}\n\n"
            f"Agent Description: {description}\n"
            "Answer (number only):"
        )
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of task-agent compatibility."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1200,
            )
            result = response.choices[0].message.content.strip()
            score = int(''.join(filter(str.isdigit, result)))
            print(f"[Manager] LLM computed match score: {score} for agent description: '{description}'")
            return score
        except Exception as e:
            print(f"[Manager] LLM failed to compute match score: {e}. Falling back to simple matching.")
            translator = str.maketrans('', '', string.punctuation)
            subtask_words = set(subtask.translate(translator).lower().split())
            desc_words = set(description.translate(translator).lower().split())
            fallback_score = len(subtask_words.intersection(desc_words))
            print(f"[Manager] Fallback match score: {fallback_score} for agent description: '{description}'")
            return fallback_score

    def assign_execution_nodes(self, subtask):
        """
        Uses LLM reasoning to decide which agents to assign for a given subtask.
        Prioritizes agents based on their description match and reputation score.
        Returns a tuple (list of chosen nodes, expected response format).
        """
        agents_info = "\n".join(
            [f"{node.name}: {node.description} (Reputation score: {node.reputation_score})" for node in self.execution_nodes]
        )

        prompt = (
            "You are an expert in delegating tasks to AI agents. Given the subtask and the list of available agents with their capabilities and reputation scores, "
            "decide which agents are best suited to handle the subtask. Prioritize agents that are highly relevant to the subtask and have a high reputation score. "
            "For example, if the subtask is about numerical calculations, choose agents whose description mentions 'arithmetic' or 'mathematical', "
            "and among them, prioritize those with a higher reputation score.\n\n"
            f"Subtask: {subtask}\n\n"
            "Agents:\n" + agents_info + "\n\n"
            "Return your answer as a RAW JSON TEXT (without the word 'json' at the beginning) array of agent names (e.g., [\"Node_A\", \"Node_C\"]). Only return the JSON array."
        )

        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert in AI agent task delegation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=12000,
            )
            output = response.choices[0].message.content.strip()
            print(f"[Manager] LLM delegation response: {output}")
            
            chosen_names = json.loads(output)
            chosen_nodes = [node for node in self.execution_nodes if node.name in chosen_names]
            
            if not chosen_nodes:
                raise ValueError("LLM did not return any valid agent names.")
            
            expected_format = "json"
            return chosen_nodes, expected_format

        except Exception as e:
            print(f"[Manager] LLM failed to assign agents: {e}. Falling back to heuristic assignment.")
            
            # Compute scores based on description match and reputation score
            word_count = len(subtask.split())
            num_agents = 1 if word_count < 20 else (2 if word_count < 40 else 3)

            scored_nodes = []
            for node in self.execution_nodes:
                match_score = self.compute_match_score(subtask, node.description)
                reputation_weight = node.reputation_score / 100  # Normalize reputation (0-1 range)
                final_score = (match_score * 0.7) + (reputation_weight * 0.3)  # Weighted scoring
                scored_nodes.append((final_score, node))

            # Sort nodes by final weighted score and select the top agents
            scored_nodes.sort(key=lambda x: x[0], reverse=True)
            chosen_nodes = [node for _, node in scored_nodes[:num_agents]]
            expected_format = "json"
            return chosen_nodes, expected_format

    def process_single_task(self, task_obj, context):
        """
        Processes a single subtask with immediate validation and iterative self-critique if needed.
        It uses validators’ scores as votes: each validator’s score is counted and averaged.
        If no response (or improved response) obtains an average score above the threshold,
        the task is reattempted (up to max_attempts).
        Returns a tuple: (agent_name, final_response, average_validation_score).
        """
        max_attempts = 3
        threshold = 7  # Acceptance threshold for average validation score
        best_response = None
        best_avg_score = -1
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"[Manager] Processing subtask {task_obj['id']} (attempt {attempt})")
            nodes, expected_format = self.assign_execution_nodes(task_obj["task"])

            # Execute the subtask concurrently across the chosen execution nodes.
            responses = []  # List of tuples: (agent_node, response)
            with ThreadPoolExecutor(max_workers=len(nodes)) as executor:
                future_to_node = {
                    executor.submit(node.process_task, task_obj["task"], expected_format, context): node
                    for node in nodes
                }
                for future in as_completed(future_to_node):
                    node = future_to_node[future]
                    try:
                        resp = future.result()
                        responses.append((node, resp))
                    except Exception as e:
                        print(f"[Manager] Error processing task {task_obj['id']} by {node.name}: {e}")

            # Validate each response concurrently using all validators.
            validated_results = []  # List of tuples: (agent_node, response, avg_score)
            for node, resp in responses:
                votes = []
                with ThreadPoolExecutor(max_workers=len(self.validation_nodes)) as executor:
                    future_to_validator = {
                        executor.submit(validator.validate_answer, task_obj["task"], resp, context): validator
                        for validator in self.validation_nodes
                    }
                    for future in as_completed(future_to_validator):
                        validator = future_to_validator[future]
                        try:
                            # Expecting each validator to return a tuple where the third element is the score.
                            result_tuple = future.result()
                            score = result_tuple[2] if len(result_tuple) >= 3 else result_tuple[1]
                            votes.append(score)
                        except Exception as e:
                            print(f"[Manager] Validation error for task {task_obj['id']} by {validator.name}: {e}")
                            votes.append(0)
                if votes:
                    avg_score = sum(votes) / len(votes)
                    validated_results.append((node, resp, avg_score))
                    print(f"[Manager] Agent {node.name} obtained average validation score: {avg_score}")
                    if avg_score > best_avg_score:
                        best_avg_score = avg_score
                        best_response = (node, resp, avg_score)

            if validated_results:
                best_candidate = max(validated_results, key=lambda x: x[2])
                if best_candidate[2] >= threshold:
                    print(f"[Manager] Best candidate for subtask {task_obj['id']} on attempt {attempt}: "
                          f"Agent {best_candidate[0].name} with average score {best_candidate[2]}")
                    return best_candidate[0].name, best_candidate[1], best_candidate[2]
                else:
                    print(f"[Manager] None of the responses for subtask {task_obj['id']} met the threshold of {threshold}.")
                    # Instruct the best candidate to reprocess with self-critique instructions.
                    node = best_candidate[0]
                    improved_context = context + "\nPlease review your previous reasoning and final answer, identify any weaknesses, and provide an improved version."
                    improved_resp = node.process_task(task_obj["task"], expected_format, improved_context)
                    # Validate the improved response.
                    votes = []
                    with ThreadPoolExecutor(max_workers=len(self.validation_nodes)) as executor:
                        future_to_validator = {
                            executor.submit(validator.validate_answer, task_obj["task"], improved_resp, context): validator
                            for validator in self.validation_nodes
                        }
                        for future in as_completed(future_to_validator):
                            try:
                                result_tuple = future.result()
                                score = result_tuple[2] if len(result_tuple) >= 3 else result_tuple[1]
                                votes.append(score)
                            except Exception as e:
                                print(f"[Manager] Validation error for improved response for task {task_obj['id']}: {e}")
                                votes.append(0)
                    if votes:
                        avg_score = sum(votes) / len(votes)
                        print(f"[Manager] Improved response got average validation score: {avg_score}")
                        if avg_score >= threshold:
                            return node.name, improved_resp, avg_score
                        else:
                            print(f"[Manager] Improved response still did not meet threshold. Retrying...")
            else:
                print(f"[Manager] No valid responses received for subtask {task_obj['id']} on attempt {attempt}.")

        # After exhausting attempts, return the best available response (even if below threshold)
        if best_response:
            print(f"[Manager] Returning best available response for subtask {task_obj['id']} with average score {best_avg_score}")
            return best_response[0].name, best_response[1], best_avg_score
        else:
            print(f"[Manager] No valid response obtained for subtask {task_obj['id']}.")
            return "NoAgent", {"chain_of_thought": "", "final_answer": "No valid response obtained"}, 0

    def analyze_additional_steps(self, subtask_id, subtask_text, result):
        """
        After obtaining and validating a subtask result, determine if additional steps are needed.
        Returns a JSON array of additional steps (each with "id", "task", and "blocking" flag).
        """
        prompt = (
            "You are an expert analyst. Based on the validated result of a subtask, determine whether any additional steps are required "
            "to ensure the overall solution is complete and correct. If additional steps are needed, return a RAW JSON TEXT (without 'json' text at the beginning) array of objects, "
            "each with the keys: 'id' (a unique identifier, e.g., 'A1'), 'task' (description of the additional step), and 'blocking' (a boolean indicating if the step is crucial). "
            "If no additional steps are needed, return an empty array.\n\n"
            f"Subtask ID: {subtask_id}\n"
            f"Subtask: {subtask_text}\n"
            f"Validated Result: {json.dumps(result)}\n\n"
            "Return only the RAW JSON TEXT (without 'json' text at the beginning) array."
        )
        print(f"[Manager] Analyzing additional steps for subtask {subtask_id}...")
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert analyst for additional task identification."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=12000,
            )
            output = response.choices[0].message.content.strip()
            additional_steps = json.loads(output)
            if not isinstance(additional_steps, list):
                additional_steps = [additional_steps]
            print(f"[Manager] Additional steps suggested for {subtask_id}: {additional_steps}")
            return additional_steps
        except Exception as e:
            print(f"[Manager] Failed to analyze additional steps for subtask {subtask_id}: {e}")
            return []

    def delegate_tasks(self, subtasks):
        """
        Schedules and executes subtasks based on dependencies.
        Validates each subtask's result and checks for additional steps.
        Returns a dictionary mapping task IDs to their results.
        """
        completed_tasks = {}  # { task_id: {"task": <subtask>, "result": <result>, "agents": [agent_name], "validation_score": score} }
        remaining_tasks = {task["id"]: task for task in subtasks}

        while remaining_tasks:
            # Find tasks whose dependencies have been completed.
            ready_tasks = [
                task for task in remaining_tasks.values()
                if all(dep in completed_tasks for dep in task.get("dependencies", []))
            ]
            if not ready_tasks:
                print("No tasks ready to execute; possible circular dependency detected.")
                break

            futures = {}
            with ThreadPoolExecutor(max_workers=len(ready_tasks)) as executor:
                for task_obj in ready_tasks:
                    context = ""
                    if task_obj.get("dependencies"):
                        dep_results = [
                            f"{dep}: {completed_tasks[dep]['result']['final_answer']}"
                            for dep in task_obj["dependencies"] if dep in completed_tasks
                        ]
                        context = "\n".join(dep_results)
                    futures[executor.submit(self.process_single_task, task_obj, context)] = task_obj["id"]

            for future in as_completed(futures):
                tid = futures[future]
                try:
                    agent_name, result, score = future.result()
                    completed_tasks[tid] = {
                        "task": remaining_tasks[tid]["task"],
                        "result": result,
                        "agents": [agent_name],
                        "validation_score": score
                    }
                    # Analyze if any additional steps are needed.
                    additional_steps = self.analyze_additional_steps(tid, remaining_tasks[tid]["task"], result)
                    for step in additional_steps:
                        # Ensure additional step has a dependencies list.
                        if "dependencies" not in step:
                            step["dependencies"] = []
                        # If blocking, add dependency on the parent task.
                        if step.get("blocking", False):
                            step["dependencies"].append(tid)
                        # Add the additional step if not already processed.
                        if step["id"] not in completed_tasks and step["id"] not in remaining_tasks:
                            remaining_tasks[step["id"]] = step
                except Exception as e:
                    print(f"Error processing task {tid}: {e}")
            # Remove executed tasks.
            for task_obj in ready_tasks:
                tid = task_obj["id"]
                if tid in remaining_tasks:
                    del remaining_tasks[tid]
        return completed_tasks

    def compile_final_answer(self, completed_tasks, complex_task):
        """
        Synthesizes a final answer by combining all validated subtask responses.
        """
        valid_responses = []
        for tid, info in completed_tasks.items():
            valid_responses.append(f"Task {tid} ({info['task']}): {info['result']['final_answer']}")
        synthesis_prompt = (
            "You are an expert synthesizer. Given the following responses for various subtasks of a complex task, "
            "please produce a coherent, unified final answer that integrates all the information into a well-organized and comprehensive response.\n\n"
            "Responses:\n" + "\n\n".join(valid_responses) + "\n\n"
            f"Complex Task: {complex_task}\n\n"
            "Please provide the final answer in a clear and coherent manner."
        )
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert synthesizer."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3,
                max_tokens=12000,
            )
            final_answer = response.choices[0].message.content.strip()
            return final_answer
        except Exception as e:
            print(f"Error synthesizing final answer: {e}")
            return "\n".join(valid_responses)

    def process_complex_task(self, complex_task):
        subtasks = self.analyze_task(complex_task)
        completed_tasks = self.delegate_tasks(subtasks)
        final_answer = self.compile_final_answer(completed_tasks, complex_task)
        return final_answer