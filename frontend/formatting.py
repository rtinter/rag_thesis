import re


def normalize_math(text: str) -> str:
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.DOTALL)
    return text


def highlight_citations(text: str) -> str:
    return re.sub(r"\[(\d+)\]", r":primary[[\1]]", text)
