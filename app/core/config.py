import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
HF_MODEL_ID = os.getenv(
    "HF_MODEL_ID",
    "Qwen/Qwen2.5-7B-Instruct",
)
