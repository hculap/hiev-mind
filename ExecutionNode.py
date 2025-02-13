from config import DEFAULT_MODEL, client
import json

class ExecutionNode:
    def __init__(self, name, description, reputation_score):
        """
        description: A free-text description of this agent’s capabilities.
        Example: "I'm an arithmetic agent specialized in performing complex numerical calculations."
        """
        self.name = name
        self.description = description
        self.reputation_score = reputation_score

    def process_task(self, task, expected_format, context=None):
        # Build a prompt that asks for a detailed chain-of-thought and a final answer in JSON format.
        prompt = f"You are an AI agent. {self.description}\n"
        if context:
            prompt += f"Based on the following previous context:\n{context}\n"
        prompt += (
            "Please perform the following task. First, provide a detailed chain-of-thought that explains your reasoning step-by-step. "
            "Then, provide a final concise answer. "
            "Respond using the following RAW JSON (without 'json' text at the beginning) format:\n"
            '{"chain_of_thought": "<detailed reasoning>", "final_answer": "<final answer>"}\n'
            f"Task: {task}\n"
            "Be clear, thorough, and precise in your explanation."
        )
        print(f"[{self.name}] Processing task: '{task}' (context: {'present' if context else 'none'})")
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": f"You are an AI agent. {self.description}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=12000,
            )
            result = response.choices[0].message.content.strip()
            parsed_result = json.loads(result)
            return parsed_result
        except Exception as e:
            error_msg = f"Error processing task: {e}"
            print(f"[{self.name}] {error_msg}")
            return {"chain_of_thought": "", "final_answer": error_msg}

    def validate_response(self, task, response, context=None):
        """
        Uses the execution node (in validation mode) to evaluate a previously produced answer.
        It uses evaluation criteria such as logical coherence, completeness, correctness, clarity,
        and instruction-following. The response is expected to include a chain-of-thought and final answer.
        Returns a tuple: (node name, evaluation dict, aggregated average score).
        """
        prompt = (
            "You are an AI evaluator. Your task is to assess the following answer to a given task. "
            "Evaluate the answer based on the following criteria:\n"
            "1. Logical Coherence (0-10)\n"
            "2. Completeness (0-10)\n"
            "3. Correctness (0-10)\n"
            "4. Clarity (0-10)\n"
            "5. Instruction-Following (0-10)\n\n"
            f"Task: {task}\n"
            f"Response: {json.dumps(response)}\n"
            f"Context: {context if context else 'None'}\n\n"
            "Return your evaluation as RAW JSON (without the word 'json' at the beginning) with the following keys:\n"
            '{\n'
            '  "logical_coherence": <number>,\n'
            '  "completeness": <number>,\n'
            '  "correctness": <number>,\n'
            '  "clarity": <number>,\n'
            '  "instruction_following": <number>,\n'
            '  "final_verdict": "Accepted" or "Rejected",\n'
            '  "improvement_suggestions": "<brief feedback>"\n'
            '}'
        )
        print(f"[{self.name}] Validating response for task: '{task}'")
        try:
            api_response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI evaluator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500,
            )
            evaluation = json.loads(api_response.choices[0].message.content.strip())
            avg_score = (
                evaluation["logical_coherence"] +
                evaluation["completeness"] +
                evaluation["correctness"] +
                evaluation["clarity"] +
                evaluation["instruction_following"]
            ) / 5
            return (self.name, evaluation, avg_score)
        except Exception as e:
            print(f"[{self.name}] Error during validation: {e}")
            fallback_evaluation = {
                "logical_coherence": 0,
                "completeness": 0,
                "correctness": 0,
                "clarity": 0,
                "instruction_following": 0,
                "final_verdict": "Rejected",
                "improvement_suggestions": "Evaluation failed due to an error."
            }
            return (self.name, fallback_evaluation, 0)