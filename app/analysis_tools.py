import pandas as pd


def profile_df(df: pd.DataFrame) -> dict:
    """Retorna informações de perfil do DataFrame."""

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
        "describe_numeric": df.select_dtypes("number").describe().to_dict(),
    }


def top_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    """Retorna os n valores mais frequentes de uma coluna."""

    return (
        df[column]
        .value_counts(dropna=False)
        .head(n)
        .reset_index()
        .rename(columns={"index": column, column: "count"})
    )


def groupby_agg(
    df: pd.DataFrame,
    group: str,
    value: str,
    agg: str = "sum",
) -> pd.DataFrame:
    """Agrupa por `group` e aplica agregação em `value`."""

    if agg not in {"sum", "mean", "min", "max", "count"}:
        raise ValueError("agg inválido")

    out = df.groupby(group, dropna=False)[value].agg(agg).reset_index()
    out = out.sort_values(by=value, ascending=False)
    return out