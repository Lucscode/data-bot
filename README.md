# Data Bot – Análise de dados com IA

Aplicação simples para subir arquivos CSV/XLSX, analisar dados com Pandas e fazer perguntas em linguagem natural usando uma API (Groq) como roteador de ferramentas.

## Funcionalidades

- Upload de arquivos `.csv` ou `.xlsx` via API
- Armazenamento do dataset em memória
- Geração de **perfil do dataset** (linhas, colunas, tipos, nulos, valores únicos)
- Consultas do tipo **"top N"** (valores mais frequentes)
- Consultas de **agrupamento + agregação** (soma, média, min, max, count)
- Roteamento das perguntas:
<<<<<<< HEAD
  - Heurística local (sem IA) ou  Groq (via variável de ambiente `GROQ_API_KEY`)
=======
  - Heurística local (sem IA) **ou**
  - Groq (via variável de ambiente `GROQ_API_KEY`)
>>>>>>> 724f50f (Add project README)
- Front-end web simples em `web/` para conversar com o bot

## Requisitos

- Python 3.10+ (testado em 3.13)
- pip
<<<<<<< HEAD
=======

## Instalação

```bash
# clonar o repositório
git clone https://github.com/Lucscode/data-bot.git
cd data-bot

# criar e ativar ambiente virtual (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar dependências
pip install -r app/requirements.txt
```

## Executando o backend (API)

Na raiz do projeto:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

- Documentação interativa (Swagger): http://127.0.0.1:8000/docs

### Variável de ambiente opcional (Groq)

Se quiser usar a IA da Groq para decidir melhor as ferramentas de análise, defina a variável de ambiente antes de iniciar o servidor:

```bash
# exemplo (PowerShell)
$env:GROQ_API_KEY = "SUA_CHAVE_AQUI"
uvicorn app.main:app --reload
```

Se `GROQ_API_KEY` não estiver definida, o sistema usa apenas o roteador local (`route_without_llm`).

## Executando o front-end

A pasta `web/` contém um front-end estático simples:

- `web/index.html`
- `web/app.js`
- `web/style.css`

Você pode abrir o `index.html` direto no navegador ou usar alguma extensão como **Live Server** do VS Code.

Certifique-se de que o backend esteja rodando em `http://127.0.0.1:8000` (é esse endereço que o `web/app.js` usa).

## Fluxo de uso

1. Acesse o front-end (ou use diretamente o `/docs`).
2. Faça upload de um arquivo CSV/XLSX.
3. Guarde o `dataset_id` retornado ou use o próprio front-end, que já mantém isso em memória.
4. Faça perguntas em linguagem natural sobre o dataset (ex.:
   - "Mostre o top 10 postos com mais registros"
   - "Qual a soma de valor_total por cliente?"
   - "Me dê um resumo do dataset"
5. O backend escolhe a ferramenta adequada e retorna o resultado em formato JSON (e o front-end renderiza tabela/perfil).

## Avisos

- Os datasets são armazenados apenas em memória (não há banco de dados).
- Não committe nenhuma chave real de API ou arquivos `.env` no repositório.
- O `.gitignore` já está configurado para ignorar ambientes virtuais e arquivos sensíveis comuns.
>>>>>>> 724f50f (Add project README)
