import io
import pandas as pd
from fastapi import UploadFile, HTTPException


async def load_dataframe(file: UploadFile) -> pd.DataFrame:
    """Carrega o arquivo enviado (CSV ou Excel) em um DataFrame pandas."""

    name = (file.filename or "").lower()
    content = await file.read()

    try:
        if name.endswith(".csv"):
            # tenta utf-8-sig (muito comum), se falhar tenta latin-1
            try:
                return pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
            except Exception:
                # tenta separador ; (export do Excel)
                try:
                    return pd.read_csv(io.BytesIO(content), encoding="latin-1", sep=";")
                except Exception:
                    return pd.read_csv(io.BytesIO(content), encoding="latin-1")

        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(io.BytesIO(content), engine="openpyxl")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro lendo arquivo: {e}")

    raise HTTPException(status_code=400, detail="Envie um arquivo .csv ou .xlsx")