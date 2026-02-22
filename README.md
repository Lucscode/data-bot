# Data Bot – Análise de dados com IA

Aplicação simples para subir arquivos CSV/XLSX, analisar dados com Pandas e fazer perguntas em linguagem natural usando uma API (Groq) como roteador de ferramentas.

## Funcionalidades

- Upload de arquivos `.csv` ou `.xlsx` via API
- Armazenamento do dataset em memória
- Geração de **perfil do dataset** (linhas, colunas, tipos, nulos, valores únicos)
- Consultas do tipo **"top N"** (valores mais frequentes)
- Consultas de **agrupamento + agregação** (soma, média, min, max, count)
- Roteamento das perguntas:
  - Heurística local (sem IA) ou  Groq (via variável de ambiente `GROQ_API_KEY`)
- Front-end web simples em `web/` para conversar com o bot

## Requisitos

- Python 3.10+ (testado em 3.13)
- pip
