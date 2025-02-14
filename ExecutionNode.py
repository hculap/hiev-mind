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
        print(f"[{self.name}] Processing task...")
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