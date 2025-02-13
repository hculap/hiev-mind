import json
from config import DEFAULT_MODEL, client

class ValidationNode:
    def __init__(self, name):
        self.name = name

    def agent_as_a_judge(self, task, response):
        """
        Implements the Agent-as-a-Judge framework for evaluating agentic responses.
        - Provides intermediate feedback.
        - Evaluates both chain-of-thought and final response.
        - Uses compare-based and metrics-based evaluations.
        """

        prompt = (
            "You are an advanced AI judge evaluating AI-generated responses. Your task is to analyze the reasoning steps, "
            "identify strengths and weaknesses, and provide a fair and detailed assessment. "
            "You will evaluate both the chain-of-thought and the final answer based on the following criteria:\n"
            "1. Logical Coherence: Is the reasoning step-by-step and logically sound?\n"
            "2. Completeness: Does it fully address the task?\n"
            "3. Correctness: Is the final answer factually accurate?\n"
            "4. Clarity: Is the explanation clear and understandable?\n"
            "5. Instruction-Following: Does the response adhere to the given prompt?\n"
            "\n"
            f"Task: {task}\n"
            f"Response: {json.dumps(response, indent=2)}\n\n"
            "### Evaluation Output:\n"
            "Return a structured RAW JSON TEXT (without the word 'json' at the beginning)  with the following fields:\n"
            "{\n"
            '  "logical_coherence": <score from 0 to 10>,\n'
            '  "completeness": <score from 0 to 10>,\n'
            '  "correctness": <score from 0 to 10>,\n'
            '  "clarity": <score from 0 to 10>,\n'
            '  "instruction_following": <score from 0 to 10>,\n'
            '  "final_verdict": "Accepted" or "Rejected",\n'
            '  "improvement_suggestions": "<brief feedback on how to improve the response>"\n'
            "}"
        )

        print(f"[{self.name}] Evaluating response...")

        try:
            api_response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI Judge."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500,
            )

            evaluation = json.loads(api_response.choices[0].message.content.strip())

            return evaluation

        except Exception as e:
            print(f"    [{self.name}] Error during validation: {e}")
            return {
                "logical_coherence": 0,
                "completeness": 0,
                "correctness": 0,
                "clarity": 0,
                "instruction_following": 0,
                "final_verdict": "Rejected",
                "improvement_suggestions": "Evaluation failed due to an error."
            }

    def validate_answer(self, task, response):
        """
        Uses the Agent-as-a-Judge framework to validate an answer.
        Returns a structured assessment with scores and improvement feedback.
        """
        evaluation = self.agent_as_a_judge(task, response)

        # Compute an aggregated score based on all evaluation metrics
        avg_score = (
            evaluation["logical_coherence"] +
            evaluation["completeness"] +
            evaluation["correctness"] +
            evaluation["clarity"] +
            evaluation["instruction_following"]
        ) / 5

        return (self.name, evaluation, avg_score)