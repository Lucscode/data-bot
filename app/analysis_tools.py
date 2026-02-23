import pandas as pd


def profile_df(df: pd.DataFrame) -> dict:
    """Retorna informações de perfil do DataFrame."""

    numeric_desc = df.select_dtypes(include="number").describe()
    return {
        "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},
        "columns": [
            {
                "name": c,
                "dtype": str(df[c].dtype),
                "nulls": int(df[c].isna().sum()),
                "unique": int(df[c].nunique(dropna=True)),
            }
            for c in df.columns
        ],
        # Evita quebrar quando não existir coluna numérica (describe fica vazio)
        "describe_numeric": numeric_desc.to_dict() if not numeric_desc.empty else {},
    }


def top_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    """Retorna os n valores mais frequentes de uma coluna."""
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não existe no dataset.")

    n = max(1, min(int(n), 100))

    return (
        df[column]
        .value_counts(dropna=False)
        .head(n)
        .reset_index()
        .rename(columns={"index": column, column: "count"})
    )


def groupby_agg(df: pd.DataFrame, group: str, value: str, agg: str = "sum") -> pd.DataFrame:
    """Agrupa por `group` e aplica agregação em `value`."""
    if group not in df.columns:
        raise ValueError(f"Coluna de grupo '{group}' não existe no dataset.")
    if value not in df.columns:
        raise ValueError(f"Coluna de valor '{value}' não existe no dataset.")

    agg = str(agg).lower().strip()
    if agg not in {"sum", "mean", "min", "max", "count"}:
        raise ValueError("agg inválido. Use: sum, mean, min, max, count")

    # Para count, faz mais sentido contar registros por grupo
    if agg == "count":
        out = df.groupby(group, dropna=False).size().reset_index(name="count")
        out = out.sort_values(by="count", ascending=False)
        return out

    # Tenta converter a coluna value para número quando possível
    s = pd.to_numeric(df[value], errors="coerce")
    tmp = df.copy()
    tmp[value] = s

    out = tmp.groupby(group, dropna=False)[value].agg(agg).reset_index()
    out = out.sort_values(by=value, ascending=False)
    return out