"""
PROCV — Comparador de Listas + Toolkit de Texto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Instalação:
    pip install nicegui httpx

Execução:
    python procv_app.py

Acesso:
    Ferramenta  →  http://localhost:8080
    Histórico   →  http://localhost:8080/admin  (senha abaixo)

Nomes inteligentes com IA (opcional):
    Defina a variável de ambiente ANTHROPIC_API_KEY
    para ativar geração automática de nomes com gênero correto em PT-BR.
    Sem ela, o sistema usa um template padrão limpo.

Abas disponíveis:
    ⚡  PROCV        — Comparador de listas
    ✂️  Extrator     — Extrai valor entre vírgulas (ex: 99999,0319,99999 → 0319)
    0   Zero         — Adiciona ou remove o 0 inicial de números
    📵  DDI 55       — Remove o prefixo 55 de números brasileiros
"""

import json
import os
import httpx
from datetime import datetime
from nicegui import ui, app

# ╔══════════════════════════════════════════════╗
# ║  CONFIGURAÇÃO — edite antes de distribuir    ║
# ╚══════════════════════════════════════════════╝
ADMIN_PASSWORD    = "procv@admin2024"          # ← MUDE ESTA SENHA
HISTORY_FILE      = "procv_historico.json"
STORAGE_SECRET    = "procv-chave-secreta-001"  # ← pode mudar também
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# ══════════════════════════════════════════════
#  UTILITÁRIOS — histórico
# ══════════════════════════════════════════════

def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def append_history(entry: dict):
    history = load_history()
    history.insert(0, entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════
#  UTILITÁRIOS — comparação (PROCV)
# ══════════════════════════════════════════════

def parse_list(text: str) -> list:
    return list(dict.fromkeys(
        line.strip() for line in text.splitlines() if line.strip()
    ))


def comparar(text_a: str, text_b: str) -> dict:
    lista_a = parse_list(text_a)
    lista_b = parse_list(text_b)
    set_a = {i.lower() for i in lista_a}
    set_b = {i.lower() for i in lista_b}
    return {
        "lista_a": lista_a,
        "lista_b": lista_b,
        "apenas_em_a": [i for i in lista_a if i.lower() not in set_b],
        "apenas_em_b": [i for i in lista_b if i.lower() not in set_a],
    }


# ══════════════════════════════════════════════
#  UTILITÁRIOS — ferramentas de texto/número
# ══════════════════════════════════════════════

def extrair_virgula(text: str) -> tuple[list, list]:
    """
    Extrai o valor entre vírgulas de cada linha.
    Ex: "99999,0319,99999" → "0319"
    Retorna (resultados, linhas_com_erro).
    """
    resultados = []
    erros = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) >= 2:
            resultados.append(parts[1].strip())
        else:
            erros.append(line)
    return resultados, erros


def processar_zero(text: str, modo: str) -> list:
    """
    modo='add' → adiciona 0 no início de cada número.
    modo='rem' → remove o 0 inicial (se houver).
    """
    resultados = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if modo == "add":
            resultados.append("0" + line)
        else:
            resultados.append(line[1:] if line.startswith("0") else line)
    return resultados


def remover_ddi55(text: str) -> tuple[list, int]:
    """
    Remove o prefixo 55 de números brasileiros.
    Retorna (resultados, qtd_sem_55).
    """
    resultados = []
    sem_55 = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("55"):
            resultados.append(line[2:])
        else:
            resultados.append(line)
            sem_55 += 1
    return resultados, sem_55


# ══════════════════════════════════════════════
#  GERAÇÃO INTELIGENTE DE TÍTULOS (PROCV)
# ══════════════════════════════════════════════

async def gerar_titulos(nome_a: str, nome_b: str) -> tuple:
    """
    Usa Claude para gerar títulos com gênero/número correto em PT-BR.
    Fallback automático se a chave não estiver disponível.
    """
    if ANTHROPIC_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 200,
                        "messages": [{
                            "role": "user",
                            "content": (
                                f'Gere dois títulos curtos e naturais em português brasileiro.\n'
                                f'Coluna A: "{nome_a}"\n'
                                f'Coluna B: "{nome_b}"\n\n'
                                f'Regras:\n'
                                f'- Use gênero gramatical correto\n'
                                f'- col_a: itens que existem em A mas não em B. Formato: "[itens] que [estão/têm/etc] em [A], mas não [em B / fisicamente / no sistema / etc]"\n'
                                f'- col_b: itens que existem em B mas não em A. Mesmo padrão invertido.\n'
                                f'- Seja direto e natural. Evite "sem correspondência".\n'
                                f'- Exemplo: "Placas MGI" + "Placas Físico" → col_a: "Placas que têm no MGI, mas não fisicamente" / col_b: "Placas que têm fisicamente, mas não no MGI"\n'
                                f'- Responda SOMENTE com JSON válido: {{"col_a": "...", "col_b": "..."}}'
                            ),
                        }],
                    },
                )
                data = resp.json()
                raw = data["content"][0]["text"].strip()
                parsed = json.loads(raw)
                return parsed["col_a"], parsed["col_b"]
        except Exception:
            pass

    # Fallback simples e natural
    return (
        f"{nome_a}, mas não em {nome_b}",
        f"{nome_b}, mas não em {nome_a}",
    )


# ══════════════════════════════════════════════
#  ESTILOS GLOBAIS
# ══════════════════════════════════════════════

GLOBAL_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  /* ── DARK (padrão) ── */
  :root {
    --bg:           #060a14;
    --bg-card:      rgba(255,255,255,0.025);
    --bg-top:       rgba(6,10,20,0.80);
    --border:       rgba(255,255,255,0.08);
    --border-hover: rgba(96,165,250,0.25);
    --text:         #dde3ef;
    --text-muted:   #475569;
    --text-soft:    #64748b;
    --input-bg:     rgba(255,255,255,0.04);
    --input-border: rgba(255,255,255,0.1);
    --dot-grid:     rgba(255,255,255,0.04);
    --glow-a:       rgba(30,64,175,0.12);
    --glow-b:       rgba(6,182,212,0.08);
    --field-text:   #cbd5e1;
    --empty-color:  #334155;
    --loading-color:#475569;
    --hist-bg:      rgba(255,255,255,0.02);
    --scrollbar:    rgba(255,255,255,0.08);
    --toggle-bg:    rgba(255,255,255,0.06);
  }

  /* ── LIGHT ── */
  body.light {
    --bg:           #eef2f7;
    --bg-card:      #ffffff;
    --bg-top:       rgba(238,242,247,0.92);
    --border:       rgba(0,0,0,0.15);
    --border-hover: rgba(37,99,235,0.45);
    --text:         #0f172a;
    --text-muted:   #64748b;
    --text-soft:    #94a3b8;
    --input-bg:     #ffffff;
    --input-border: rgba(0,0,0,0.18);
    --dot-grid:     rgba(0,0,0,0.05);
    --glow-a:       rgba(30,64,175,0.05);
    --glow-b:       rgba(6,182,212,0.03);
    --field-text:   #1e293b;
    --empty-color:  #94a3b8;
    --loading-color:#64748b;
    --hist-bg:      rgba(0,0,0,0.03);
    --scrollbar:    rgba(0,0,0,0.14);
    --toggle-bg:    rgba(0,0,0,0.07);
  }

  body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
    transition: background 0.3s, color 0.3s;
  }

  body::before {
    content: '';
    position: fixed; inset: 0;
    background:
      radial-gradient(ellipse 80% 60% at 15% 20%, var(--glow-a) 0%, transparent 60%),
      radial-gradient(ellipse 60% 50% at 85% 75%, var(--glow-b) 0%, transparent 60%);
    pointer-events: none; z-index: 0;
    transition: background 0.3s;
  }

  body::after {
    content: '';
    position: fixed; inset: 0;
    background-image: radial-gradient(circle, var(--dot-grid) 1px, transparent 1px);
    background-size: 32px 32px;
    pointer-events: none; z-index: 0;
  }

  .page-wrap { position: relative; z-index: 1; }

  /* ── TOP BAR ── */
  .top-bar {
    position: sticky; top: 0; z-index: 200;
    backdrop-filter: blur(20px) saturate(1.4);
    background: var(--bg-top);
    border-bottom: 1px solid var(--border);
    padding: 0 40px; height: 60px;
    display: flex; align-items: center; justify-content: space-between;
    transition: background 0.3s, border-color 0.3s;
  }
  .top-logo-icon {
    width: 30px; height: 30px; border-radius: 8px;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
  }
  .top-logo-text { color: var(--text); font-size: 18px; font-weight: 800; letter-spacing: -0.3px; }

  /* ── NAV TABS ── */
  .nav-tabs {
    display: flex; align-items: center; gap: 4px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 12px; padding: 4px;
  }
  body.light .nav-tabs { background: rgba(0,0,0,0.04); }

  .nav-tab {
    display: flex; align-items: center; gap: 6px;
    padding: 7px 14px; border-radius: 8px;
    border: none; background: transparent;
    color: var(--text-muted);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px; font-weight: 700;
    cursor: pointer; white-space: nowrap;
    letter-spacing: 0.3px;
    transition: all 0.2s;
  }
  .nav-tab:hover { color: var(--text); background: rgba(255,255,255,0.05); }
  .nav-tab.active-procv  { background: rgba(59,130,246,0.15);  color: #93c5fd; border: 1px solid rgba(59,130,246,0.25); }
  .nav-tab.active-ext    { background: rgba(96,165,250,0.12);  color: #7dd3fc; border: 1px solid rgba(96,165,250,0.22); }
  .nav-tab.active-zero   { background: rgba(16,185,129,0.13);  color: #6ee7b7; border: 1px solid rgba(16,185,129,0.25); }
  .nav-tab.active-ddi    { background: rgba(239,68,68,0.13);   color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
  body.light .nav-tab:hover { background: rgba(0,0,0,0.05); }

  /* ── Toggle Button ── */
  .theme-toggle {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--toggle-bg) !important;
    border: 1px solid var(--border) !important;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 16px;
    transition: background 0.2s, border-color 0.2s, transform 0.2s;
    min-width: unset !important; padding: 0 !important;
    box-shadow: none !important;
  }
  .theme-toggle:hover { transform: rotate(20deg); border-color: var(--border-hover) !important; }

  /* ── GLASS CARD ── */
  .glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 4px; padding: 28px;
    transition: border-color 0.25s, background 0.3s;
  }
  .glass-card:hover { border-color: var(--border-hover); }

  /* ── INFO BOX ── */
  .info-box {
    background: rgba(59,130,246,0.07);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 10px; padding: 12px 16px;
    font-size: 12px; color: #7dd3fc;
    line-height: 1.6; margin-bottom: 20px;
  }
  .info-box b { color: #93c5fd; }
  .info-box code {
    background: rgba(255,255,255,0.06);
    padding: 1px 6px; border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
  }
  body.light .info-box { background: rgba(37,99,235,0.06); border-color: rgba(37,99,235,0.2); color: #1d4ed8; }
  body.light .info-box b { color: #1e40af; }

  /* ── Quasar field overrides ── */
  .q-field__control { background: var(--input-bg) !important; transition: background 0.3s; }
  .q-field--outlined .q-field__control { border-color: var(--input-border) !important; border-radius: 2px !important; border-width: 1.5px !important; }
  .q-field--outlined .q-field__control:hover { border-color: rgba(96,165,250,0.5) !important; }
  .q-field--outlined.q-field--focused .q-field__control { border-color: rgba(96,165,250,0.7) !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important; }
  .q-field__native, .q-field__input { font-family: 'Plus Jakarta Sans', sans-serif !important; color: var(--text) !important; }
  .q-field__label { color: var(--text-muted) !important; }
  .list-area textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important; line-height: 1.8 !important; color: var(--field-text) !important; padding-left: 6px !important; background: var(--input-bg) !important; }
  .list-area .q-field__control { padding-left: 0 !important; }
  .name-input .q-field__native { padding-left: 6px !important; }

  /* Light mode: stronger borders */
  body.light .q-field--outlined .q-field__control { border-color: #b0bec5 !important; }
  body.light .glass-card { box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

  /* ── Buttons ── */
  .action-btn {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12px !important; font-weight: 600 !important;
    border-radius: 8px !important; padding: 6px 16px !important;
    letter-spacing: 0.5px !important;
  }
  .btn-clear {
    background: var(--toggle-bg) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
  }
  .btn-clear:hover { border-color: var(--border-hover) !important; color: var(--text) !important; }
  .btn-copy {
    background: rgba(59,130,246,0.1) !important;
    color: #93c5fd !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
  }
  .btn-copy:hover { background: rgba(59,130,246,0.18) !important; }

  /* ── PROCV button ── */
  .procv-btn-wrap { display: flex; justify-content: center; margin: 40px 0 4px; }
  .btn-procv {
    background: linear-gradient(135deg, #1d4ed8 0%, #0369a1 50%, #0e7490 100%) !important;
    color: #fff !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 800 !important; font-size: 14px !important;
    letter-spacing: 2.5px !important; text-transform: uppercase !important;
    border-radius: 14px !important; border: none !important;
    padding: 16px 56px !important;
    box-shadow: 0 4px 30px rgba(29,78,216,0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    transition: all 0.2s !important;
  }
  .btn-procv:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 40px rgba(29,78,216,0.55) !important; }
  .btn-procv:active { transform: translateY(0) !important; }

  /* ── TOOLKIT buttons ── */
  .btn-ext {
    background: linear-gradient(135deg, #1d4ed8, #0891b2) !important;
    color: #fff !important; border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12px !important; font-weight: 700 !important;
    border-radius: 10px !important; padding: 10px 22px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 18px rgba(29,78,216,0.3) !important;
    transition: all 0.2s !important;
  }
  .btn-ext:hover { transform: translateY(-1px) !important; filter: brightness(1.1) !important; }

  .btn-add-zero {
    background: linear-gradient(135deg, #059669, #0891b2) !important;
    color: #fff !important; border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12px !important; font-weight: 700 !important;
    border-radius: 10px !important; padding: 10px 22px !important;
    box-shadow: 0 4px 18px rgba(5,150,105,0.3) !important;
    transition: all 0.2s !important;
  }
  .btn-add-zero:hover { transform: translateY(-1px) !important; filter: brightness(1.1) !important; }

  .btn-rem-zero {
    background: linear-gradient(135deg, #d97706, #0891b2) !important;
    color: #fff !important; border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12px !important; font-weight: 700 !important;
    border-radius: 10px !important; padding: 10px 22px !important;
    box-shadow: 0 4px 18px rgba(217,119,6,0.3) !important;
    transition: all 0.2s !important;
  }
  .btn-rem-zero:hover { transform: translateY(-1px) !important; filter: brightness(1.1) !important; }

  .btn-ddi {
    background: linear-gradient(135deg, #dc2626, #ea580c) !important;
    color: #fff !important; border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12px !important; font-weight: 700 !important;
    border-radius: 10px !important; padding: 10px 22px !important;
    box-shadow: 0 4px 18px rgba(220,38,38,0.3) !important;
    transition: all 0.2s !important;
  }
  .btn-ddi:hover { transform: translateY(-1px) !important; filter: brightness(1.1) !important; }

  /* ── Result cards (PROCV) ── */
  .res-card {
    flex: 1; border-radius: 4px; padding: 20px 28px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    min-height: 200px;
    transition: background 0.3s, border-color 0.3s;
  }
  .res-card-a { border-color: rgba(96,165,250,0.25); }
  .res-card-b { border-color: rgba(34,211,238,0.2); }
  .res-title { font-size: 13px; font-weight: 700; margin-bottom: 14px; line-height: 1.4; padding-bottom: 10px; }
  .res-title-a { color: #3b82f6; border-bottom: 1px solid rgba(96,165,250,0.2); }
  .res-title-b { color: #0891b2; border-bottom: 1px solid rgba(34,211,238,0.2); }

  .res-list { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--field-text); padding-left: 6px; }
  .res-item { display: block; line-height: 1.9; padding: 1px 0; }

  /* ── Toolkit result card ── */
  .toolkit-result {
    margin-top: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    animation: fadeInUp 0.3s ease;
  }
  .toolkit-result-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 18px;
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid var(--border);
  }
  .toolkit-result-body {
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px; line-height: 1.9;
    color: var(--field-text);
    max-height: 320px; overflow-y: auto;
    word-break: break-all;
  }
  .toolkit-result-body::-webkit-scrollbar { width: 4px; }
  .toolkit-result-body::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: 2px; }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Badges ── */
  .stat-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--hist-bg); border: 1px solid var(--border);
    border-radius: 22px; padding: 6px 14px; font-size: 12.5px; font-weight: 500; color: var(--text-muted);
  }
  .stat-badge b { color: var(--text); font-weight: 700; }

  .count-badge {
    font-size: 11px; color: var(--text-muted);
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
    border-radius: 20px; padding: 3px 10px;
  }

  .res-label-ext  { font-size: 12px; font-weight: 700; color: #7dd3fc; letter-spacing: 0.8px; }
  .res-label-add  { font-size: 12px; font-weight: 700; color: #6ee7b7; letter-spacing: 0.8px; }
  .res-label-rem  { font-size: 12px; font-weight: 700; color: #fcd34d; letter-spacing: 0.8px; }
  .res-label-ddi  { font-size: 12px; font-weight: 700; color: #fca5a5; letter-spacing: 0.8px; }

  /* ── Warning tag ── */
  .warn-tag {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; color: #fcd34d;
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 6px; padding: 4px 10px;
    margin-top: 8px;
  }

  .empty-state { color: var(--empty-color); font-size: 13px; font-style: italic; display: flex; align-items: center; gap: 8px; padding: 8px 0; }
  .loading-row { display: flex; align-items: center; gap: 12px; color: var(--loading-color); font-size: 14px; padding: 24px 0; }

  /* ── Admin / Login ── */
  .login-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 40px; max-width: 380px; width: 100%; }
  .hist-row { background: var(--hist-bg); border: 1px solid var(--border); border-radius: 12px; padding: 18px 22px; margin-bottom: 10px; transition: border-color 0.2s; }
  .hist-row:hover { border-color: var(--border-hover); }
  .hist-date { font-size: 11px; color: var(--text-muted); letter-spacing: 0.8px; }
  .hist-pair { font-size: 15px; font-weight: 700; color: var(--text); margin: 5px 0 4px; }
  .hist-counts { font-size: 12px; color: var(--text-soft); }

  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: 3px; }
  .nicegui-content { padding: 0 !important; }
</style>
"""


# ══════════════════════════════════════════════
#  HELPERS JS — copiar para clipboard
# ══════════════════════════════════════════════

def js_copy(items: list) -> str:
    text = "\n".join(items)
    return f'navigator.clipboard.writeText({json.dumps(text)})'


# ══════════════════════════════════════════════
#  PÁGINA PRINCIPAL
# ══════════════════════════════════════════════

@ui.page('/')
def main_page():
    ui.add_head_html(GLOBAL_CSS)

    with ui.column().classes("page-wrap w-full"):

        # ── Top Bar ──────────────────────────────────
        with ui.element('div').classes("top-bar w-full"):
            with ui.row().classes("items-center gap-3"):
                ui.html('<div class="top-logo-icon">⚡</div>')
                ui.html('<div class="top-logo-text">PROCV <span style="font-weight:400;color:#475569">Toolkit</span></div>')

            with ui.row().classes("items-center gap-3"):
                # Nav tabs
                with ui.element('div').classes("nav-tabs"):
                    tab_procv = ui.button("PROCV", icon="bolt").classes("nav-tab active-procv")
                    tab_ext   = ui.button("Extrator", icon="content_cut").classes("nav-tab")
                    tab_zero  = ui.button("+/- Zero", icon="exposure_zero").classes("nav-tab")
                    tab_ddi   = ui.button("DDI 55", icon="phone_disabled").classes("nav-tab")
                toggle_btn = ui.button("", icon="light_mode").classes("theme-toggle")

        # ── Panels container ──────────────────────────
        main_content = ui.column().classes("w-full").style(
            "padding: 44px 40px; max-width: 1380px; margin: 0 auto;"
        )

        # ══════════════════════════════════════════════
        #  PANEL — PROCV
        # ══════════════════════════════════════════════
        with main_content:
            panel_procv = ui.column().classes("w-full")
            panel_ext   = ui.column().classes("w-full")
            panel_zero  = ui.column().classes("w-full")
            panel_ddi   = ui.column().classes("w-full")

            panel_ext.set_visibility(False)
            panel_zero.set_visibility(False)
            panel_ddi.set_visibility(False)

        # ── PROCV content ─────────────────────────────
        with panel_procv:
            with ui.row().classes("w-full items-start gap-5 mb-2"):
                with ui.column().classes("flex-1 glass-card gap-5"):
                    nome_a = (
                        ui.input(label=" ")
                        .classes("w-full name-input")
                        .props("outlined dense")
                    )
                    lista_a = (
                        ui.textarea(label=" ")
                        .classes("w-full list-area")
                        .props("outlined")
                        .style("min-height:260px;")
                    )
                with ui.column().classes("flex-1 glass-card gap-5"):
                    nome_b = (
                        ui.input(label=" ")
                        .classes("w-full name-input")
                        .props("outlined dense")
                    )
                    lista_b = (
                        ui.textarea(label=" ")
                        .classes("w-full list-area")
                        .props("outlined")
                        .style("min-height:260px;")
                    )

            with ui.element('div').classes("procv-btn-wrap w-full"):
                with ui.row().classes("items-center gap-4"):
                    btn_procv_clear = ui.button("Limpar tudo", icon="close").classes("action-btn btn-clear")
                    btn_procv = ui.button("PROCV", icon="bolt").classes("btn-procv")

            procv_result_area = ui.column().classes("w-full")

        # ── EXTRATOR content ──────────────────────────
        with panel_ext:
            ui.html(
                '<div class="info-box">'
                '<b>Como funciona:</b> Cole seus dados abaixo. O sistema extrai o valor '
                'entre as vírgulas de cada linha.<br>'
                'Ex: <code>99999,0319,99999</code> → <b>0319</b>'
                '</div>'
            )
            with ui.column().classes("glass-card w-full gap-4"):
                ui.html('<div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:var(--text-muted);text-transform:uppercase;">Dados de entrada</div>')
                ext_input = (
                    ui.textarea(label=" ")
                    .classes("w-full list-area")
                    .props("outlined")
                    .style("min-height:220px;")
                )
                with ui.row().classes("items-center gap-3"):
                    btn_ext_run   = ui.button("Extrair", icon="content_cut").classes("btn-ext")
                    btn_ext_clear = ui.button("Limpar", icon="close").classes("action-btn btn-clear")
            ext_result_area = ui.column().classes("w-full")

        # ── ZERO content ──────────────────────────────
        with panel_zero:
            ui.html(
                '<div class="info-box">'
                '<b>Adicionar 0:</b> <code>31996070871</code> → <b>031996070871</b><br>'
                '<b>Remover 0:</b> <code>031996070871</code> → <b>31996070871</b>'
                '</div>'
            )
            with ui.column().classes("glass-card w-full gap-4"):
                ui.html('<div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:var(--text-muted);text-transform:uppercase;">Números</div>')
                zero_input = (
                    ui.textarea(label=" ")
                    .classes("w-full list-area")
                    .props("outlined")
                    .style("min-height:220px;")
                )
                with ui.row().classes("items-center gap-3"):
                    btn_add_zero  = ui.button("Adicionar 0", icon="add").classes("btn-add-zero")
                    btn_rem_zero  = ui.button("Remover 0", icon="remove").classes("btn-rem-zero")
                    btn_zero_clear = ui.button("Limpar", icon="close").classes("action-btn btn-clear")
            zero_result_area = ui.column().classes("w-full")

        # ── DDI 55 content ────────────────────────────
        with panel_ddi:
            ui.html(
                '<div class="info-box">'
                '<b>Como funciona:</b> Remove o prefixo 55 do início de números brasileiros.<br>'
                'Ex: <code>5531996070871</code> → <b>31996070871</b>'
                '</div>'
            )
            with ui.column().classes("glass-card w-full gap-4"):
                ui.html('<div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:var(--text-muted);text-transform:uppercase;">Números com DDI 55</div>')
                ddi_input = (
                    ui.textarea(label=" ")
                    .classes("w-full list-area")
                    .props("outlined")
                    .style("min-height:220px;")
                )
                with ui.row().classes("items-center gap-3"):
                    btn_ddi_run   = ui.button("Remover DDI 55", icon="phone_disabled").classes("btn-ddi")
                    btn_ddi_clear = ui.button("Limpar", icon="close").classes("action-btn btn-clear")
            ddi_result_area = ui.column().classes("w-full")

    # ══════════════════════════════════════════════
    #  LÓGICA — navegação entre abas
    # ══════════════════════════════════════════════

    all_panels = [panel_procv, panel_ext, panel_zero, panel_ddi]
    all_tabs   = [tab_procv, tab_ext, tab_zero, tab_ddi]
    tab_classes = ["active-procv", "active-ext", "active-zero", "active-ddi"]

    def show_tab(idx):
        for i, (panel, tab, cls) in enumerate(zip(all_panels, all_tabs, tab_classes)):
            panel.set_visibility(i == idx)
            if i == idx:
                tab.classes(add=cls)
            else:
                for c in tab_classes:
                    tab.classes(remove=c)

    tab_procv.on_click(lambda: show_tab(0))
    tab_ext.on_click(lambda: show_tab(1))
    tab_zero.on_click(lambda: show_tab(2))
    tab_ddi.on_click(lambda: show_tab(3))

    # ══════════════════════════════════════════════
    #  LÓGICA — PROCV
    # ══════════════════════════════════════════════

    async def on_procv():
        text_a = (lista_a.value or "").strip()
        text_b = (lista_b.value or "").strip()
        n_a    = (nome_a.value or "Lista A").strip()
        n_b    = (nome_b.value or "Lista B").strip()

        if not text_a and not text_b:
            ui.notify("Insira pelo menos uma lista!", type="warning", position="top")
            return

        btn_procv.disable()
        procv_result_area.clear()
        with procv_result_area:
            ui.html('<div class="loading-row"><div>Processando comparação…</div></div>')

        result = comparar(text_a, text_b)
        titulo_a, titulo_b = await gerar_titulos(n_a, n_b)

        append_history({
            "data":         datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "nome_a":       n_a,
            "nome_b":       n_b,
            "total_a":      len(result["lista_a"]),
            "total_b":      len(result["lista_b"]),
            "apenas_em_a":  result["apenas_em_a"],
            "apenas_em_b":  result["apenas_em_b"],
            "titulo_col_a": titulo_a,
            "titulo_col_b": titulo_b,
        })

        procv_result_area.clear()
        with procv_result_area:
            with ui.row().classes("w-full gap-5"):
                # Card A
                with ui.element('div').classes("res-card res-card-a"):
                    with ui.row().classes("items-center justify-between w-full mb-3 gap-3"):
                        ui.html(f'<div class="res-title res-title-a" style="margin-bottom:0;">{n_a}</div>')
                        copy_a = ui.button("Copiar", icon="content_copy").classes("action-btn btn-copy").props("dense")
                    if result["apenas_em_a"]:
                        itens_html = "".join(f'<div class="res-item">{item}</div>' for item in result["apenas_em_a"])
                        ui.html(f'<div class="res-list">{itens_html}</div>')
                        copy_a.on_click(lambda _, items=result["apenas_em_a"]: (
                            ui.run_javascript(js_copy(items)),
                            ui.notify("Copiado!", type="positive", position="top")
                        ))
                    else:
                        ui.html('<div class="empty-state">✓ Todos os itens estão presentes</div>')
                        copy_a.props("disabled")

                # Card B
                with ui.element('div').classes("res-card res-card-b"):
                    with ui.row().classes("items-center justify-between w-full mb-3 gap-3"):
                        ui.html(f'<div class="res-title res-title-b" style="margin-bottom:0;">{n_b}</div>')
                        copy_b = ui.button("Copiar", icon="content_copy").classes("action-btn btn-copy").props("dense")
                    if result["apenas_em_b"]:
                        itens_html = "".join(f'<div class="res-item">{item}</div>' for item in result["apenas_em_b"])
                        ui.html(f'<div class="res-list">{itens_html}</div>')
                        copy_b.on_click(lambda _, items=result["apenas_em_b"]: (
                            ui.run_javascript(js_copy(items)),
                            ui.notify("Copiado!", type="positive", position="top")
                        ))
                    else:
                        ui.html('<div class="empty-state">✓ Todos os itens estão presentes</div>')
                        copy_b.props("disabled")

        btn_procv.enable()
        ui.notify("✅ PROCV concluído com sucesso!", type="positive", position="top")

    def on_procv_clear():
        nome_a.set_value("")
        nome_b.set_value("")
        lista_a.set_value("")
        lista_b.set_value("")
        procv_result_area.clear()
        ui.notify("Tudo limpo!", position="top")

    btn_procv.on_click(on_procv)
    btn_procv_clear.on_click(on_procv_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — EXTRATOR DE VÍRGULA
    # ══════════════════════════════════════════════

    def on_extrator():
        raw = (ext_input.value or "").strip()
        if not raw:
            ui.notify("Cole os dados primeiro!", type="warning", position="top")
            return

        resultados, erros = extrair_virgula(raw)
        ext_result_area.clear()

        with ext_result_area:
            with ui.element('div').classes("toolkit-result"):
                with ui.element('div').classes("toolkit-result-header"):
                    ui.html(f'<span class="res-label-ext">VALORES EXTRAIDOS</span>')
                    with ui.row().classes("items-center gap-2"):
                        ui.html(f'<span class="count-badge">{len(resultados)} item(s)</span>')
                        if resultados:
                            btn_copy = ui.button("Copiar tudo", icon="content_copy").classes("action-btn btn-copy").props("dense")
                            btn_copy.on_click(lambda _, r=resultados: (
                                ui.run_javascript(js_copy(r)),
                                ui.notify("Copiado!", type="positive", position="top")
                            ))

                with ui.element('div').classes("toolkit-result-body"):
                    if resultados:
                        for item in resultados:
                            ui.html(f'<div>{item}</div>')
                    else:
                        ui.html('<div class="empty-state">Nenhum valor extraído.</div>')

                if erros:
                    ui.html(f'<div style="padding:8px 18px 12px;"><span class="warn-tag">⚠️ {len(erros)} linha(s) sem vírgula foram ignoradas</span></div>')

        if resultados:
            ui.notify(f"✅ {len(resultados)} valor(es) extraído(s)!", type="positive", position="top")
        if erros:
            ui.notify(f"⚠️ {len(erros)} linha(s) sem vírgula ignoradas", type="warning", position="top")

    def on_ext_clear():
        ext_input.set_value("")
        ext_result_area.clear()
        ui.notify("Tudo limpo!", position="top")

    btn_ext_run.on_click(on_extrator)
    btn_ext_clear.on_click(on_ext_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — ADICIONAR / REMOVER ZERO
    # ══════════════════════════════════════════════

    def on_zero(modo: str):
        raw = (zero_input.value or "").strip()
        if not raw:
            ui.notify("Cole os números primeiro!", type="warning", position="top")
            return

        resultados = processar_zero(raw, modo)
        zero_result_area.clear()

        label_text  = "NUMEROS COM 0 ADICIONADO" if modo == "add" else "NUMEROS COM 0 REMOVIDO"
        label_class = "res-label-add" if modo == "add" else "res-label-rem"
        msg_ok      = f"✅ 0 {'adicionado' if modo == 'add' else 'removido'} em {len(resultados)} número(s)!"

        with zero_result_area:
            with ui.element('div').classes("toolkit-result"):
                with ui.element('div').classes("toolkit-result-header"):
                    ui.html(f'<span class="{label_class}">{label_text}</span>')
                    with ui.row().classes("items-center gap-2"):
                        ui.html(f'<span class="count-badge">{len(resultados)} item(s)</span>')
                        if resultados:
                            btn_copy = ui.button("Copiar tudo", icon="content_copy").classes("action-btn btn-copy").props("dense")
                            btn_copy.on_click(lambda _, r=resultados: (
                                ui.run_javascript(js_copy(r)),
                                ui.notify("Copiado!", type="positive", position="top")
                            ))

                with ui.element('div').classes("toolkit-result-body"):
                    if resultados:
                        for item in resultados:
                            ui.html(f'<div>{item}</div>')
                    else:
                        ui.html('<div class="empty-state">Nenhum número processado.</div>')

        ui.notify(msg_ok, type="positive", position="top")

    def on_zero_clear():
        zero_input.set_value("")
        zero_result_area.clear()
        ui.notify("Tudo limpo!", position="top")

    btn_add_zero.on_click(lambda: on_zero("add"))
    btn_rem_zero.on_click(lambda: on_zero("rem"))
    btn_zero_clear.on_click(on_zero_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — REMOVER DDI 55
    # ══════════════════════════════════════════════

    def on_ddi():
        raw = (ddi_input.value or "").strip()
        if not raw:
            ui.notify("Cole os números primeiro!", type="warning", position="top")
            return

        resultados, sem_55 = remover_ddi55(raw)
        ddi_result_area.clear()

        with ddi_result_area:
            with ui.element('div').classes("toolkit-result"):
                with ui.element('div').classes("toolkit-result-header"):
                    ui.html('<span class="res-label-ddi">NUMEROS SEM DDI 55</span>')
                    with ui.row().classes("items-center gap-2"):
                        ui.html(f'<span class="count-badge">{len(resultados)} item(s)</span>')
                        if resultados:
                            btn_copy = ui.button("Copiar tudo", icon="content_copy").classes("action-btn btn-copy").props("dense")
                            btn_copy.on_click(lambda _, r=resultados: (
                                ui.run_javascript(js_copy(r)),
                                ui.notify("Copiado!", type="positive", position="top")
                            ))

                with ui.element('div').classes("toolkit-result-body"):
                    if resultados:
                        for item in resultados:
                            ui.html(f'<div>{item}</div>')
                    else:
                        ui.html('<div class="empty-state">Nenhum número processado.</div>')

                if sem_55:
                    ui.html(f'<div style="padding:8px 18px 12px;"><span class="warn-tag">⚠️ {sem_55} número(s) não tinham o prefixo 55</span></div>')

        if sem_55:
            ui.notify(f"⚠️ {sem_55} número(s) sem o prefixo 55", type="warning", position="top")
        else:
            ui.notify(f"✅ DDI 55 removido de {len(resultados)} número(s)!", type="positive", position="top")

    def on_ddi_clear():
        ddi_input.set_value("")
        ddi_result_area.clear()
        ui.notify("Tudo limpo!", position="top")

    btn_ddi_run.on_click(on_ddi)
    btn_ddi_clear.on_click(on_ddi_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — Tema claro/escuro
    # ══════════════════════════════════════════════

    def toggle_theme():
        ui.run_javascript("""
            const body = document.body;
            const isLight = body.classList.toggle('light');
            document.querySelectorAll('.theme-toggle .q-icon').forEach(b => {
                b.textContent = isLight ? 'dark_mode' : 'light_mode';
            });
        """)

    toggle_btn.on_click(toggle_theme)


# ══════════════════════════════════════════════
#  PÁGINA ADMIN — protegida por senha
# ══════════════════════════════════════════════

@ui.page('/admin')
def admin_page():
    ui.add_head_html(GLOBAL_CSS)

    with ui.column().classes("page-wrap w-full"):

        with ui.element('div').classes("top-bar w-full"):
            with ui.row().classes("items-center gap-3"):
                ui.html('<div class="top-logo-icon">🔐</div>')
                ui.html('<div class="top-logo-text">PROCV <span>Admin</span></div>')
            logout_btn = (
                ui.button("Sair", icon="logout")
                .props("flat dense")
                .style("color:#475569; font-size:12px; font-family:'Plus Jakarta Sans',sans-serif;")
            )

        with ui.column().classes("w-full").style(
            "padding: 44px 40px; max-width: 1200px; margin: 0 auto;"
        ):
            login_sec   = ui.column().classes("w-full items-center justify-center").style("min-height:65vh;")
            history_sec = ui.column().classes("w-full gap-3")
            history_sec.set_visibility(False)

            def render_history():
                history_sec.clear()
                with history_sec:
                    history = load_history()
                    with ui.row().classes("items-center justify-between w-full mb-2"):
                        ui.html('<h2 style="font-size:22px; font-weight:800;">📂 Histórico de PROCVs</h2>')
                        ui.html(
                            f'<span class="stat-badge"><b>{len(history)}</b> registros salvos</span>'
                        )

                    if not history:
                        ui.html(
                            '<div style="text-align:center; padding:60px 0; color:#334155; font-size:14px;">'
                            'Nenhum PROCV realizado ainda.</div>'
                        )
                        return

                    for entry in history:
                        with ui.element('div').classes("hist-row w-full"):
                            with ui.row().classes("w-full items-start justify-between gap-4"):
                                with ui.column().classes("gap-1 flex-1"):
                                    ui.html(f'<div class="hist-date">🕐 {entry["data"]}</div>')
                                    ui.html(
                                        f'<div class="hist-pair">'
                                        f'{entry["nome_a"]}'
                                        f'<span style="color:#1e293b; margin:0 10px;">↔</span>'
                                        f'{entry["nome_b"]}'
                                        f'</div>'
                                    )
                                    ui.html(
                                        f'<div class="hist-counts">'
                                        f'Total A: <b style="color:#94a3b8">{entry["total_a"]}</b> &nbsp;|&nbsp; '
                                        f'Total B: <b style="color:#94a3b8">{entry["total_b"]}</b> &nbsp;|&nbsp; '
                                        f'Só em A: <b style="color:#93c5fd">{len(entry["apenas_em_a"])}</b> &nbsp;|&nbsp; '
                                        f'Só em B: <b style="color:#67e8f9">{len(entry["apenas_em_b"])}</b>'
                                        f'</div>'
                                    )

                                with ui.expansion("Ver itens").props("dense").style(
                                    "color:#3b82f6; font-size:12px; font-weight:600;"
                                ):
                                    with ui.row().classes("gap-6 w-full mt-3"):
                                        with ui.column().classes("flex-1 gap-1"):
                                            ui.html(
                                                f'<div style="font-size:11px; font-weight:700; color:#93c5fd; '
                                                f'letter-spacing:1px; margin-bottom:8px;">'
                                                f'{entry.get("titulo_col_a", "Só em A")}</div>'
                                            )
                                            if entry["apenas_em_a"]:
                                                for item in entry["apenas_em_a"]:
                                                    ui.html(
                                                        f'<div style="font-family:JetBrains Mono,monospace; '
                                                        f'font-size:12px; color:#64748b; padding:1px 0;">{item}</div>'
                                                    )
                                            else:
                                                ui.html('<div class="empty-state" style="font-size:12px;">Nenhum item exclusivo</div>')

                                        with ui.column().classes("flex-1 gap-1"):
                                            ui.html(
                                                f'<div style="font-size:11px; font-weight:700; color:#67e8f9; '
                                                f'letter-spacing:1px; margin-bottom:8px;">'
                                                f'{entry.get("titulo_col_b", "Só em B")}</div>'
                                            )
                                            if entry["apenas_em_b"]:
                                                for item in entry["apenas_em_b"]:
                                                    ui.html(
                                                        f'<div style="font-family:JetBrains Mono,monospace; '
                                                        f'font-size:12px; color:#64748b; padding:1px 0;">{item}</div>'
                                                    )
                                            else:
                                                ui.html('<div class="empty-state" style="font-size:12px;">Nenhum item exclusivo</div>')

            def show_login():
                login_sec.set_visibility(True)
                history_sec.set_visibility(False)
                login_sec.clear()

                with login_sec:
                    with ui.element('div').classes("login-card"):
                        with ui.column().classes("items-center gap-5 w-full"):
                            ui.html(
                                '<div style="width:64px;height:64px;border-radius:16px;'
                                'background:linear-gradient(135deg,#1d4ed8,#0e7490);'
                                'display:flex;align-items:center;justify-content:center;'
                                'font-size:28px;">🔐</div>'
                            )
                            ui.html(
                                '<div style="text-align:center;">'
                                '<div style="font-size:20px;font-weight:800;color:#f1f5f9;margin-bottom:6px;">Acesso Admin</div>'
                                '<div style="font-size:13px;color:#475569;line-height:1.5;">Área restrita ao criador.<br>Insira a senha para ver o histórico.</div>'
                                '</div>'
                            )
                            pwd = (
                                ui.input("Senha de acesso", password=True, password_toggle_button=True)
                                .classes("w-full")
                                .props("dark outlined")
                            )
                            err = ui.label("").style("color:#f87171; font-size:13px;")

                            def do_login():
                                if pwd.value == ADMIN_PASSWORD:
                                    app.storage.user["is_admin"] = True
                                    login_sec.set_visibility(False)
                                    history_sec.set_visibility(True)
                                    render_history()
                                else:
                                    err.set_text("Senha incorreta. Tente novamente.")
                                    pwd.set_value("")

                            pwd.on("keydown.enter", lambda _: do_login())
                            (
                                ui.button("Entrar", icon="lock_open", on_click=do_login)
                                .classes("w-full")
                                .style(
                                    "background:linear-gradient(135deg,#1d4ed8,#0e7490);"
                                    "color:white;font-weight:700;font-size:14px;"
                                    "border-radius:12px;padding:12px 0;"
                                    "font-family:'Plus Jakarta Sans',sans-serif;"
                                    "box-shadow:0 4px 20px rgba(29,78,216,0.35);"
                                )
                            )

            def do_logout():
                app.storage.user["is_admin"] = False
                show_login()

            logout_btn.on_click(do_logout)

            if app.storage.user.get("is_admin", False):
                login_sec.set_visibility(False)
                history_sec.set_visibility(True)
                render_history()
            else:
                show_login()


# ══════════════════════════════════════════════
#  INICIALIZAÇÃO
# ══════════════════════════════════════════════

ui.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    title="PROCV – Toolkit",
    favicon="⚡",
    dark=True,
    reload=False,
    show=False,
    storage_secret=STORAGE_SECRET,
)
