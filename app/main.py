from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ingest import load_dataframe
from storage import save_df, get_df
from schemas import UploadResponse, QueryRequest, QueryResponse
from analysis_tools import profile_df, top_n, groupby_agg
from ia_router import route_with_groq  # se seu arquivo for ai_router.py, troque aqui

app = FastAPI(title="Bot de Análise de Dados + IA")

# ✅ CORS (uma vez só, antes das rotas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://databot1.netlify.app",
        # depois adicione o domínio do Netlify:
        # "https://databot1.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/datasets", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    df = await load_dataframe(file)
    dataset_id = save_df(df)
    return {"dataset_id": dataset_id, "rows": len(df), "cols": len(df.columns)}

@app.get("/datasets/{dataset_id}/profile")
def dataset_profile(dataset_id: str):
    df = get_df(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")
    return profile_df(df)

@app.post("/datasets/{dataset_id}/query", response_model=QueryResponse)
async def dataset_query(dataset_id: str, req: QueryRequest):
    df = get_df(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")

    columns = list(df.columns)
    decision = await route_with_groq(req.question, columns)

    tool = decision.get("tool")
    args = decision.get("args", {})
    explanation = decision.get("explanation", "")

    try:
        if tool == "profile":
            info = profile_df(df)
            return {"tool": tool, "explanation": explanation, "table": None, "profile": info}

        if tool == "top_n":
            out = top_n(df, **args)
            return {"tool": tool, "explanation": explanation, "table": out.to_dict(orient="records"), "profile": None}

        if tool == "groupby_agg":
            out = groupby_agg(df, **args)
            return {"tool": tool, "explanation": explanation, "table": out.to_dict(orient="records"), "profile": None}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha executando tool: {e}")

    raise HTTPException(status_code=400, detail="Tool inválida")