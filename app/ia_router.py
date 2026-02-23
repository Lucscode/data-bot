import os
import json
import re
import httpx

SYSTEM = """Você é um roteador de ferramentas de análise de dados.
Escolha UMA ferramenta e retorne JSON puro no formato:
{"tool":"profile" | "top_n" | "groupby_agg",
 "args": {...},
 "explanation":"..."}
Regras:
- Use apenas colunas existentes.
- Se a pergunta for geral sobre o dataset, use "profile".
- Para "top", "mais frequentes", use top_n com column e n.
- Para agregações tipo "somar por", "média por", use groupby_agg com group, value, agg.
"""

VALUE_HINTS = [
    "valor", "total", "amount", "price", "preco", "preço",
    "custo", "cost", "gasto", "receita", "revenue", "salario", "salário",
    "quantidade", "qtd", "litros", "horas", "tempo"
]

GROUP_HINTS = [
    "categoria", "tipo", "posto", "loja", "cliente", "motorista",
    "veiculo", "veículo", "produto", "setor", "departamento", "mes", "mês", "ano"
]

def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _simplify(s: str) -> str:
    # remove múltiplos espaços e deixa minúsculo
    return re.sub(r"\s+", " ", _norm(s))

def _find_column_by_mention(question: str, columns: list[str]) -> str | None:
    """
    Tenta casar menção de coluna com base em substring e palavra inteira.
    Ex: pergunta menciona 'valor total' e coluna é 'Valor_Total' ou 'valor total'.
    """
    q = _simplify(question)

    # tenta match por forma simplificada
    for c in columns:
        c_simple = _simplify(c)
        if not c_simple:
            continue
        if c_simple in q:
            return c
        # palavra inteira (evita match parcial estranho)
        if re.search(rf"\b{re.escape(c_simple)}\b", q):
            return c

    return None

def _pick_best_value_column(columns: list[str]) -> str | None:
    for hint in VALUE_HINTS:
        for c in columns:
            if hint in _norm(c):
                return c
    return None

def _pick_best_group_column(columns: list[str]) -> str:
    for hint in GROUP_HINTS:
        for c in columns:
            if hint in _norm(c):
                return c
    return columns[0] if columns else "coluna"

def _extract_top_n(question: str) -> int:
    m = re.search(r"\b(\d{1,3})\b", question)
    if not m:
        return 10
    n = int(m.group(1))
    return max(1, min(n, 50))

def route_without_llm(question: str, columns: list[str]) -> dict:
    q = _norm(question)

    if not columns:
        return {"tool": "profile", "args": {}, "explanation": "Dataset sem colunas para analisar."}

    # TOP
    if "top" in q or "mais frequente" in q or "mais comuns" in q or "mais comum" in q:
        n = _extract_top_n(question)
        col = _find_column_by_mention(question, columns) or _pick_best_group_column(columns)
        return {
            "tool": "top_n",
            "args": {"column": col, "n": n},
            "explanation": f"Mostrando top {n} valores mais frequentes em '{col}'."
        }

    # AGG
    agg = None
    if "média" in q or "media" in q:
        agg = "mean"
    elif "somar" in q or "soma" in q or "total" in q:
        agg = "sum"
    elif "máximo" in q or "maximo" in q or "maior" in q:
        agg = "max"
    elif "mínimo" in q or "minimo" in q or "menor" in q:
        agg = "min"
    elif "contar" in q or "quantos" in q or "count" in q:
        agg = "count"

    if agg:
        group = _pick_best_group_column(columns)
        mentioned = _find_column_by_mention(question, columns)

        # se tiver "por", tentamos tratar a menção como group
        if " por " in _simplify(question):
            group = mentioned or group

        # value
        if agg == "count":
            # para count, usamos o próprio group como value (tool vai contar)
            value = group
        else:
            value = mentioned or _pick_best_value_column(columns)
            if not value:
                return {
                    "tool": "profile",
                    "args": {},
                    "explanation": "Não identifiquei uma coluna de valor para agregar. Mostrando resumo do dataset."
                }

        return {
            "tool": "groupby_agg",
            "args": {"group": group, "value": value, "agg": agg},
            "explanation": f"Aplicando '{agg}' em '{value}' agrupando por '{group}'."
        }

    # PERFIL
    if "perfil" in q or "resumo" in q or "colunas" in q or "describe" in q:
        return {"tool": "profile", "args": {}, "explanation": "Gerando perfil do dataset."}

    return {"tool": "profile", "args": {}, "explanation": "Pergunta ampla; retornando perfil."}

def _extract_json_from_text(text: str) -> dict | None:
    """
    Alguns modelos retornam texto extra. Tentamos extrair o primeiro bloco JSON.
    """
    if not text:
        return None
    text = text.strip()

    # tenta direto
    try:
        return json.loads(text)
    except Exception:
        pass

    # tenta achar um objeto {...} no meio
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

async def route_with_groq(question: str, columns: list[str]) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return route_without_llm(question, columns)

    user = f"Pergunta: {question}\nColunas disponíveis: {columns}"

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]

    parsed = _extract_json_from_text(content)
    if parsed is None:
        return route_without_llm(question, columns)

    return parsed