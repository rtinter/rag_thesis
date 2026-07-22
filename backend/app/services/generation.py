import re
from openai import OpenAI
from app.core.prompts import system_prompt_generation

def build_context(chunks: list[dict]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(f"[{i}] {chunk['title']}\n{chunk['page_content']}")
    return "\n\n".join(blocks)

def build_message(question: str, context: str) -> list[dict]:
    message = f"Kontext:\n{context}\n\nFrage: {question}"
    return [
        {"role": "system", "content": system_prompt_generation},
        {"role": "user", "content": message},
    ]

def generate(question: str,
             chunks: list[dict],
             gateway: OpenAI,
             model: str,
             temperature: float = 0.0,
             max_tokens: int = 8192
) -> str:
    context = build_context(chunks)
    message  = build_message(question, context)
    response = gateway.chat.completions.create(
        model=model,
        messages=message,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

def find_cited_markers(answer: str) -> list[int]:
    found = {int(marker) for marker in re.findall(r"\[(\d+)\]", answer)}
    return sorted(found)
