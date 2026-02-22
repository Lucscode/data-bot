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

# Palavras comuns para tentar achar colunas "de valor"
VALUE_HINTS = [
    "valor", "total", "amount", "price", "preco", "preço",
    "custo", "cost", "gasto", "receita", "revenue", "salario", "salário",
    "quantidade", "qtd", "litros", "horas", "tempo"
]

# Colunas que geralmente são boas para agrupar
GROUP_HINTS = [
    "categoria", "tipo", "posto", "loja", "cliente", "motorista",
    "veiculo", "veículo", "produto", "setor", "departamento", "mes", "mês", "ano"
]

def _norm(s: str) -> str:
    return s.strip().lower()

def _find_column_by_mention(question: str, columns: list[str]) -> str | None:
    """
    Se o usuário mencionar explicitamente uma coluna (ou parte do nome),
    tentamos casar com alguma coluna.
    """
    q = _norm(question)
    for c in columns:
        c_norm = _norm(c)
        # match por palavra inteira ou substring razoável
        if c_norm in q or re.search(rf"\b{re.escape(c_norm)}\b", q):
            return c
    return None

def _pick_best_value_column(columns: list[str]) -> str | None:
    cols = list(columns)
    # 1) preferir colunas com pistas de valor
    for hint in VALUE_HINTS:
        for c in cols:
            if hint in _norm(c):
                return c
    # 2) fallback: nenhuma pista → não arriscar
    return None

def _pick_best_group_column(columns: list[str]) -> str:
    cols = list(columns)
    # 1) preferir colunas com pistas de grupo
    for hint in GROUP_HINTS:
        for c in cols:
            if hint in _norm(c):
                return c
    # 2) fallback: primeira coluna
    return cols[0] if cols else "coluna"

def _extract_top_n(question: str) -> int:
    """
    Pega o primeiro número da pergunta, ex: "top 5"
    """
    m = re.search(r"\b(\d{1,3})\b", question)
    if not m:
        return 10
    n = int(m.group(1))
    return max(1, min(n, 50))

def route_without_llm(question: str, columns: list[str]) -> dict:
    q = _norm(question)

    if not columns:
        return {"tool": "profile", "args": {}, "explanation": "Dataset sem colunas para analisar."}

    # --- 1) TOP / MAIS FREQUENTES ---
    # (não use "mais" sozinho; muito genérico)
    if "top" in q or "mais frequente" in q or "mais comuns" in q or "mais comum" in q:
        n = _extract_top_n(question)
        col = _find_column_by_mention(question, columns) or _pick_best_group_column(columns)
        return {
            "tool": "top_n",
            "args": {"column": col, "n": n},
            "explanation": f"Mostrando top {n} valores mais frequentes em '{col}'."
        }

    # --- 2) AGREGAÇÕES (somar/média/máximo/mínimo/contar) ---
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
        # tenta achar grupo e valor citados
        group = None
        value = None

        # caso: "por <coluna>"
        if " por " in q:
            # tenta pegar algo depois de "por" e casar com coluna
            mentioned = _find_column_by_mention(question, columns)
            group = mentioned or _pick_best_group_column(columns)
        else:
            group = _pick_best_group_column(columns)

        # para count, podemos contar a própria coluna do grupo (ou a primeira)
        if agg == "count":
            value = _find_column_by_mention(question, columns) or group
        else:
            # value: tenta coluna mencionada; senão tenta pista de valor
            value = _find_column_by_mention(question, columns) or _pick_best_value_column(columns)

            # se não conseguir achar uma coluna de valor, cai no profile (melhor que errar)
            if not value:
                return {
                    "tool": "profile",
                    "args": {},
                    "explanation": "Não identifiquei uma coluna numérica/valor para agregar. Mostrando resumo do dataset."
                }

        return {
            "tool": "groupby_agg",
            "args": {"group": group, "value": value, "agg": agg},
            "explanation": f"Aplicando '{agg}' em '{value}' agrupando por '{group}'."
        }

    # --- 3) PERFIL / RESUMO ---
    if "perfil" in q or "resumo" in q or "colunas" in q or "describe" in q:
        return {"tool": "profile", "args": {}, "explanation": "Gerando perfil do dataset."}

    # fallback seguro
    return {"tool": "profile", "args": {}, "explanation": "Pergunta ampla; retornando perfil."}


async def route_with_groq(question: str, columns: list[str]) -> dict:
    """
    Se não houver GROQ_API_KEY, usa heurística local.
    Se houver, chama Groq e tenta parsear JSON; se falhar, cai no fallback.
    """
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

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # fallback seguro se o modelo não mandar JSON puro
        return route_without_llm(question, columns)