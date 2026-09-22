"""API 路由：健康、接入、问答、检索、评测。

作者：晨星
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from novamind.api.schemas import (
    AskRequest,
    AskResponse,
    HealthOut,
    IngestRequest,
    SearchRequest,
    SourceOut,
    StepOut,
)
from novamind.core.errors import NovaMindError
from novamind.core.models import Document
from novamind.eval.golden import GOLDEN_CASES
from novamind.ingest.loader import Loader

router = APIRouter()


def _get_system(request: Request):
    return request.app.state.system


@router.get("/health", response_model=HealthOut)
async def health(request: Request):
    sys = _get_system(request)
    return HealthOut(
        status="ok",
        backends={
            "llm": sys.settings.llm_backend,
            "embed": sys.settings.embed_backend,
            "vector": sys.settings.vector_backend,
            "rerank": sys.settings.rerank_backend,
        },
    )


@router.post("/ingest")
async def ingest(request: Request, body: IngestRequest):
    sys = _get_system(request)
    try:
        doc = Loader.from_text(body.text, body.doc_id) if body.doc_id else Loader.from_text(body.text)
        n = await sys.ingest([doc])
    except NovaMindError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ingested_chunks": n, "doc_id": doc.id}


@router.post("/ask", response_model=AskResponse)
async def ask(request: Request, body: AskRequest):
    sys = _get_system(request)
    try:
        result = await sys.agent.run(body.query)
    except NovaMindError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AskResponse(
        answer=result.answer,
        sources=[
            SourceOut(
                chunk_id=h.chunk_id, doc_id=h.doc_id, text=h.text, score=h.score
            )
            for h in result.sources
        ],
        steps=[StepOut(action=s.action, detail=s.detail, tool=s.tool) for s in result.steps],
    )


@router.post("/search")
async def search(request: Request, body: SearchRequest):
    sys = _get_system(request)
    hits = await sys.retriever.retrieve(body.query, top_k=body.top_k)
    return {
        "hits": [
            {"chunk_id": h.chunk_id, "doc_id": h.doc_id, "text": h.text, "score": h.score}
            for h in hits
        ]
    }


@router.post("/evaluate")
async def evaluate(request: Request):
    sys = _get_system(request)
    reports = []
    for case in GOLDEN_CASES:
        m = await sys.evaluator.evaluate(case)
        reports.append(
            {
                "query": case.query,
                "context_recall": m.context_recall,
                "context_precision": m.context_precision,
                "faithfulness": m.faithfulness,
                "answered": m.answered,
            }
        )
    avg_recall = sum(r["context_recall"] for r in reports) / max(1, len(reports))
    avg_faith = sum(r["faithfulness"] for r in reports) / max(1, len(reports))
    return {"cases": reports, "avg_context_recall": avg_recall, "avg_faithfulness": avg_faith}
