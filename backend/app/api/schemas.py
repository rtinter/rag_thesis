from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str

class Source(BaseModel):
    cite_nr: int
    chunk_id: str
    modul: str
    lecture: str
    title: str
    page_numbers: list[int]
    slide_url: str | None
    cited: bool
    rerank_score: float

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    cited: list[int]


