import argparse
import base64
import json
import re
import time

from pathlib import Path

import pypdfium2 as pdfium
from openai import OpenAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.prompts import system_prompt_parsing

settings = get_settings()
root_dir = Path(__file__).parents[2]
pdf_dir = root_dir / "data" / "raw" / "pdfs"
parsed_dir = root_dir / "data" / "parsed"
reference_dir = Path(settings.slides_dir).resolve()

render_scale = 2
max_retries = 5
max_tokens = 8192

user_prompt = "Beschreibe die folgende Vorlesungsfolie wie im Systemprompt gefordert"
page_num_line = re.compile(r"^\s*(Seite|Folie|Page)\s+\d+\s*$", re.I)


# Pydantic schemas
class VlmSlideOutput(BaseModel):
    title: str = Field(default="")
    page_content: str = Field(default="")


class SlideChunk(BaseModel):
    id: str
    page_numbers: list[int]
    page_reference_path: str
    modul: str
    lecture: str
    title: str
    page_content: str


def get_metadata(question: str) -> str:
    while True:
        answer = input(f"{question} ").strip()
        if answer and answer == Path(answer).name and answer not in {".", ".."}:
            return answer
        print("Please enter a name without / or \\.")


def encode_image(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def parse_slide_by_vlm(image_path: Path, client: OpenAI, system_prompt: str) -> VlmSlideOutput:
    b64 = encode_image(image_path)
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=settings.vl_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ]},
                ],
                response_format={"type": "json_object"},
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                max_tokens=max_tokens,
                temperature=0,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("empty content")
            return VlmSlideOutput.model_validate_json(content)
        except Exception as e:
            print(f"[Retry {attempt + 1}/{max_retries}] {image_path.name}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
    raise RuntimeError("unreachable")


def strip_footer(text: str) -> str:
    kept = [line for line in text.splitlines() if not page_num_line.match(line.strip())]
    return "\n".join(kept).strip()


def is_empty(content: str) -> bool:
    return len(content.strip()) < 30 and "[GRAFIK]" not in content


def clean(chunks: list[dict]) -> list[dict]:
    out = []
    for chunk in chunks:
        chunk = dict(chunk)
        chunk["page_content"] = strip_footer(chunk.get("page_content", ""))
        if not is_empty(chunk["page_content"]):
            out.append(chunk)
    return out


def parse_presentation(
    pdf_path: Path,
    modul: str,
    client: OpenAI,
    system_prompt: str,
    force: bool,
) -> None:
    lecture = pdf_path.stem
    image_dir = reference_dir / modul / lecture
    out_json = parsed_dir / modul / lecture / f"{lecture}_chunks.json"
    image_dir.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict] = {}
    if out_json.exists() and not force:
        existing = {c["id"]: c for c in json.loads(out_json.read_text(encoding="utf-8"))}

    chunks: list[dict] = []
    with pdfium.PdfDocument(pdf_path) as pdf:
        total = len(pdf)
        for i, page in enumerate(pdf, start=1):
            chunk_id = f"{lecture}_page_{i}"
            img_path = image_dir / f"page_{i}.png"

            if force or not img_path.exists():
                page.render(scale=render_scale).to_pil().save(img_path)

            if chunk_id in existing:
                chunks.append(existing[chunk_id])
                print(f"{lecture} [{i:>3}/{total}] skip")
                continue

            print(f"{lecture} [{i:>3}/{total}] -> VLM ...", end=" ", flush=True)
            vlm_data = parse_slide_by_vlm(img_path, client, system_prompt)
            print("ok")

            chunks.append(SlideChunk(
                id=chunk_id,
                page_numbers=[i],
                page_reference_path=img_path.relative_to(root_dir).as_posix(),
                modul=modul,
                lecture=lecture,
                **vlm_data.model_dump(),
            ).model_dump())

            out_json.write_text(
                json.dumps(clean(chunks), indent=2, ensure_ascii=False), encoding="utf-8"
            )

    kept = clean(chunks)
    out_json.write_text(
        json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"done | {lecture}: {total} slides -> {len(kept)} chunks")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="?", help="Name or path of a PDF. Empty = all.")
    parser.add_argument("-force", action="store_true", help="Rebuild everything.")
    args = parser.parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            pdf_path = pdf_dir / f"{Path(args.pdf).stem}.pdf"
        if not pdf_path.exists():
            raise SystemExit(f"No PDF found: {args.pdf}")
        pdfs = [pdf_path]
    else:
        pdfs = sorted(pdf_dir.glob("*.pdf"))
        if not pdfs:
            raise SystemExit(f"No PDFs in {pdf_dir}")

    modul = get_metadata("Which modul do these PDFs belong to?")

    client = OpenAI(base_url=settings.gateway_url, api_key=settings.bearer_token)
    system_prompt = system_prompt_parsing
    print(f"\nVLM: {settings.vl_model} | modul: {modul} | {len(pdfs)} PDF(s)\n")

    for pdf in pdfs:
        parse_presentation(pdf, modul, client, system_prompt, args.force)


if __name__ == "__main__":
    main()
