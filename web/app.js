// ✅ Coloque aqui a URL do seu backend no Render (sem barra no final)
// Ex: https://seu-bot-api.onrender.com
const API_BASE = "https://data-bot-t7tq.onrender.com";

let datasetId = null;

const chat = document.getElementById("chat");
const resultDiv = document.getElementById("result");
const info = document.getElementById("datasetInfo");

function addMsg(who, text) {
  const div = document.createElement("div");
  div.className = "msg";
  div.innerHTML = `<b>${who === "me" ? "Você" : "Bot"}:</b> ${text}`;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function renderTable(rows) {
  if (!rows || rows.length === 0) return "<p class='muted'>Sem dados para mostrar.</p>";
  const cols = Object.keys(rows[0]);

  const thead = `<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
  const tbody = rows.map(r => `
    <tr>${cols.map(c => `<td>${String(r[c] ?? "")}</td>`).join("")}</tr>
  `).join("");

  return `<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
}

function renderProfile(profile) {
  const shape = profile.shape || {};
  const cols = profile.columns || [];

  const colRows = cols.slice(0, 12).map(c => `
    <tr>
      <td>${c.name}</td>
      <td>${c.dtype}</td>
      <td>${c.nulls}</td>
      <td>${c.unique}</td>
    </tr>
  `).join("");

  const more = cols.length > 12
    ? `<p class="muted">Mostrando 12 de ${cols.length} colunas.</p>`
    : "";

  return `
    <div style="margin-top: 12px;">
      <p class="muted"><b>${shape.rows ?? 0}</b> linhas • <b>${shape.cols ?? 0}</b> colunas</p>

      <div style="margin-top: 10px;">
        <p class="muted"><b>Colunas (até 12)</b></p>
        <table>
          <thead>
            <tr>
              <th>Coluna</th>
              <th>Tipo</th>
              <th>Nulos</th>
              <th>Únicos</th>
            </tr>
          </thead>
          <tbody>
            ${colRows}
          </tbody>
        </table>
        ${more}
      </div>
    </div>
  `;
}

// --- Helpers de fetch com timeout + parse seguro ---
async function safeJson(res) {
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await res.json().catch(() => ({}));
  }
  // Se não for JSON, pega como texto (Render às vezes retorna HTML)
  const txt = await res.text().catch(() => "");
  return { detail: txt || `HTTP ${res.status}` };
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 20000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(t);
  }
}

document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) return alert("Selecione um arquivo CSV ou XLSX.");

  const form = new FormData();
  form.append("file", fileInput.files[0]);

  const btn = document.getElementById("uploadBtn");
  btn.disabled = true;
  btn.textContent = "Enviando...";

  try {
    const res = await fetchWithTimeout(`${API_BASE}/datasets`, {
      method: "POST",
      body: form,
    }, 30000);

    const data = await safeJson(res);

    if (!res.ok) {
      addMsg("bot", `Erro no upload: ${data.detail || res.status}`);
      return;
    }

    datasetId = data.dataset_id;
    info.textContent = `Dataset carregado: ${datasetId} | Linhas: ${data.rows} | Colunas: ${data.cols}`;
    addMsg("bot", "Dataset carregado! Pode perguntar.");
  } catch (err) {
    console.error(err);
    addMsg("bot", err.name === "AbortError"
      ? "Timeout no upload (o servidor demorou para responder)."
      : "Falha de rede/servidor no upload."
    );
  } finally {
    btn.disabled = false;
    btn.textContent = "Enviar";
  }
});

document.getElementById("askBtn").addEventListener("click", async () => {
  const qEl = document.getElementById("question");
  const q = qEl.value.trim();

  if (!datasetId) return alert("Faça upload do dataset primeiro.");
  if (!q) return alert("Digite uma pergunta.");

  addMsg("me", q);
  qEl.value = "";
  resultDiv.innerHTML = "";

  const btn = document.getElementById("askBtn");
  btn.disabled = true;
  btn.textContent = "Pensando...";

  try {
    const res = await fetchWithTimeout(`${API_BASE}/datasets/${datasetId}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    }, 25000);

    const data = await safeJson(res);

    if (!res.ok) {
      addMsg("bot", `Erro: ${data.detail || res.status}`);
      return;
    }

    addMsg("bot", data.explanation || `Ok (${data.tool})`);

    if (data.profile) {
      resultDiv.innerHTML = renderProfile(data.profile);
    } else if (data.table) {
      resultDiv.innerHTML = renderTable(data.table);
    } else {
      resultDiv.innerHTML = "<p class='muted'>Sem resultado para mostrar.</p>";
    }
  } catch (err) {
    console.error(err);
    addMsg("bot", err.name === "AbortError"
      ? "Timeout: a API demorou para responder (Render free pode estar acordando)."
      : "Falha de rede/servidor."
    );
  } finally {
    btn.disabled = false;
    btn.textContent = "Perguntar";
  }
});