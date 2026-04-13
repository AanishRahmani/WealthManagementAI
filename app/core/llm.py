from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from app.core.config import HF_TOKEN, HF_MODEL_ID


def get_llm():
    llm = HuggingFaceEndpoint(
        model=HF_MODEL_ID,
        huggingfacehub_api_token=HF_TOKEN,
        max_new_tokens=512,
        temperature=0.2,
        task="conversational",
    )

    return ChatHuggingFace(llm=llm)
