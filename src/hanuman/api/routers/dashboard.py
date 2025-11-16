from __future__ import annotations

from typing import Any, Dict, cast

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from hanuman.services.orchestrations.run_log_service import make_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary() -> Dict[str, Any]:
    """
    Résumé des orchestrations + leurs derniers runs.
    """
    data = make_summary()
    return cast(Dict[str, Any], data)


@router.get("", response_class=HTMLResponse)
def dashboard_page() -> str:
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>Hanuman Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #111; color: #eee; margin: 0; padding: 1.5rem; }
    h1 { margin-top: 0; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
    .card { background: #1b1b1b; border-radius: 12px; padding: 1rem; box-shadow: 0 0 8px rgba(0,0,0,.5); }
    .card h2 { margin: 0 0 .5rem; font-size: 1.1rem; }
    .tag { display: inline-block; padding: .1rem .5rem; border-radius: 999px; font-size: .8rem; }
    .tag.ok { background: #14532d; color: #bbf7d0; }
    .tag.error { background: #7f1d1d; color: #fecaca; }
    .tag.warn { background: #78350f; color: #fed7aa; }
    table { width: 100%; border-collapse: collapse; font-size: .85rem; }
    th, td { padding: .25rem .4rem; border-bottom: 1px solid #333; text-align: left; }
    th { font-weight: 600; color: #ccc; }
    .small { font-size: .8rem; color: #aaa; }
    button { background: #2563eb; border: none; border-radius: 999px; padding: .25rem .7rem; color: #fff; font-size: .8rem; cursor: pointer; }
    button:hover { background: #1d4ed8; }
  </style>
</head>
<body>
  <h1>Hanuman Dashboard</h1>
  <p class="small">Vue d'ensemble des services et orchestrations détectées automatiquement.</p>

  <div class="grid">
    <div class="card">
      <h2>Services</h2>
      <div id="services-status" class="small">Chargement...</div>
    </div>

    <div class="card" style="grid-column: 1 / -1;">
      <h2>Orchestrations</h2>
      <div id="orch-list">Chargement...</div>
    </div>
  </div>

<script>
async function fetchJSON(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  return await resp.json();
}

function renderServicesStatus(data) {
  const el = document.getElementById("services-status");
  if (!data || !data.services) {
    el.textContent = "Aucune donnée.";
    return;
  }
  const services = data.services;
  const rows = Object.keys(services).map(name => {
    const s = services[name];
    const ok = s.ok === true;
    const cls = ok ? "ok" : "error";
    const label = ok ? "OK" : "KO";
    const detail = s.detail || "";
    return `<tr>
      <td>${name}</td>
      <td><span class="tag ${cls}">${label}</span></td>
      <td>${detail}</td>
    </tr>`;
  }).join("");
  el.innerHTML = `
    <table>
      <thead><tr><th>Service</th><th>État</th><th>Détail</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderOrchestrations(data) {
  const el = document.getElementById("orch-list");
  const list = (data && data.orchestrations) || [];
  if (list.length === 0) {
    el.textContent = "Aucune orchestration détectée.";
    return;
  }

  const cards = list.map(item => {
    const name = item.name;
    const runs = item.runs || [];
    const last = runs[0];

    let statusCls = "warn";
    let statusLabel = "Jamais lancée";
    if (last) {
      statusCls = last.status === "success" ? "ok" : "error";
      statusLabel = last.status === "success" ? "Succès" : "Erreur";
    }

    const rows = runs.map(r => `
      <tr>
        <td>${r.started_at}</td>
        <td><span class="tag ${r.status === "success" ? "ok" : "error"}">${r.status}</span></td>
        <td>${(r.duration_seconds || 0).toFixed(2)} s</td>
        <td>${r.items_processed ?? ""}</td>
        <td>${r.error_message ?? ""}</td>
      </tr>
    `).join("");

    return `
      <div class="card">
        <h2>${name} <span class="tag ${statusCls}">${statusLabel}</span></h2>
        ${runs.length === 0
          ? '<p class="small">Jamais lancée (aucun log pour l’instant).</p>'
          : `<table>
               <thead>
                 <tr>
                   <th>Début</th>
                   <th>Statut</th>
                   <th>Durée</th>
                   <th>Items</th>
                   <th>Erreur</th>
                 </tr>
               </thead>
               <tbody>${rows}</tbody>
             </table>`
        }
      </div>
    `;
  }).join("");

  el.innerHTML = `<div class="grid">${cards}</div>`;
}

async function refreshAll() {
  try {
    const [status, summary] = await Promise.all([
      fetchJSON("/status"),
      fetchJSON("/dashboard/summary"),
    ]);
    renderServicesStatus(status);
    renderOrchestrations(summary);
  } catch (err) {
    console.error(err);
    document.getElementById("services-status").textContent = "Erreur de chargement.";
    document.getElementById("orch-list").textContent = "Erreur de chargement.";
  }
}

refreshAll();
setInterval(refreshAll, 15000);
</script>
</body>
</html>
"""
