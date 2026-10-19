"""Run from repository root: python -m uvicorn backend.main:app."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from . import retrieval
from .catalog import SECTIONS, empty_intake
from .comparison import compare_cases
from .data_store import load_cases
from .models import CaseInput, RetrievedCase, SampleCase
from .samples import sample_cases


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_cases()
    yield


app = FastAPI(title="AICS Case Reference — research prototype", version="2.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Do not echo submitted intake data in errors or application logs.
    return JSONResponse(status_code=422, content={"detail": [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]})


@app.middleware("http")
async def no_store(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/form-schema")
def form_schema():
    return {"sections": SECTIONS, "empty_case": empty_intake()}


@app.get("/api/sample-cases", response_model=list[SampleCase])
def get_sample_cases():
    return sample_cases()


@app.post("/api/similar-cases", response_model=list[RetrievedCase])
def similar_cases(new_case: CaseInput):
    current = new_case.model_dump()
    results = retrieval.retrieve_similar_cases(current)
    # Only allow the documented contract through. Comparison logic remains
    # independent of the retrieval method; no frontend matching rules.
    return [RetrievedCase.model_validate({**case, "comparison": compare_cases(current, case)}) for case in results]

