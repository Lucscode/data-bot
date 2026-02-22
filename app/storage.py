import uuid
import pandas as pd

_STORE: dict[str, pd.DataFrame] = {}

def save_df(df: pd.DataFrame) -> str:
    dataset_id = str(uuid.uuid4())
    _STORE[dataset_id] = df
    return dataset_id

def get_df(dataset_id: str) -> pd.DataFrame | None:
    return _STORE.get(dataset_id)