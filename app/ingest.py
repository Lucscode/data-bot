import io
import pandas as pd
from fastapi import UploadFile, HTTPException


async def load_dataframe(file: UploadFile) -> pd.DataFrame:
    """Carrega o arquivo enviado (CSV ou Excel) em um DataFrame pandas."""

    name = (file.filename or "").lower()
    content = await file.read()

    try:
        if name.endswith(".csv"):
            return pd.read_csv(io.BytesIO(content))
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro lendo arquivo: {e}")

    # Se chegou aqui, a extensão não é suportada
    raise HTTPException(status_code=400, detail="Envie um arquivo .csv ou .xlsx")