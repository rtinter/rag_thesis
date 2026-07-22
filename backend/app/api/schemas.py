from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=3000)

class Source(BaseModel):
    cite_nr: int
    chunk_id: str
    modul: str
    lecture: str
    title: str
    page_numbers: list[int]
    slide_url: str | None
    page_content: str
    cited: bool
    rerank_score: float

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    cited: list[int]


