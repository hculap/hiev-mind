import os
import openai

# Ensure your API key is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable.")

openai.api_key = openai_api_key

# Use the newest available model.
DEFAULT_MODEL = "gpt-4o"

# In our code, we refer to the openai module as our client.
client = openai

VALIDATORS_COUNT = 5