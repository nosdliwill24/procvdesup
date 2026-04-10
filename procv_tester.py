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

BYSAT_LOGO_B64 = "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"


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
#  ESTILOS GLOBAIS — BySat Edition
# ══════════════════════════════════════════════

GLOBAL_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --red:        #E31E24;
    --red-dark:   #B91519;
    --red-glow:   rgba(227,30,36,0.20);
    --red-dim:    rgba(227,30,36,0.08);
    --bg:         #0a0c0f;
    --bg2:        #111418;
    --bg3:        #181c22;
    --bg4:        #1f242c;
    --sidebar:    #0d1017;
    --border:     rgba(255,255,255,0.07);
    --border-red: rgba(227,30,36,0.30);
    --text:       #e8edf5;
    --text2:      #8b95a6;
    --text3:      #4e5a6b;
    --mono:       'JetBrains Mono', monospace;
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
  }
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
      radial-gradient(ellipse 90% 60% at 65% 5%, rgba(227,30,36,0.05) 0%, transparent 55%),
      radial-gradient(ellipse 50% 40% at 95% 95%, rgba(227,30,36,0.03) 0%, transparent 55%);
  }
  .nicegui-content { padding: 0 !important; }

  /* ══ LAYOUT ══ */
  .app-shell {
    display: flex;
    min-height: 100vh;
    position: relative; z-index: 1;
  }

  /* ── SIDEBAR ── */
  .sidebar {
    width: 240px; min-width: 240px;
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    position: sticky; top: 0; height: 100vh;
    overflow: hidden;
  }
  .sidebar-logo {
    padding: 22px 24px 20px;
    border-bottom: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 6px;
  }
  .sidebar-logo img { height: 34px; width: auto; }
  .sidebar-logo-sub {
    font-size: 9px; font-weight: 700; letter-spacing: 3px;
    color: var(--text3); text-transform: uppercase;
  }
  .sidebar-section {
    font-size: 9px; font-weight: 700; letter-spacing: 2.5px;
    color: var(--text3); text-transform: uppercase;
    padding: 20px 24px 8px;
  }
  .nav-item {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 24px;
    border: none; background: transparent;
    color: var(--text2);
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px; font-weight: 500;
    cursor: pointer; width: 100%; text-align: left;
    border-left: 3px solid transparent;
    transition: all 0.18s; position: relative;
  }
  .nav-item .nav-icon {
    width: 30px; height: 30px; border-radius: 7px;
    background: var(--bg4);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; transition: all 0.18s;
  }
  .nav-item:hover { color: var(--text); background: rgba(255,255,255,0.03); border-left-color: var(--border); }
  .nav-item:hover .nav-icon { background: var(--bg3); }

  .nav-item.active-procv { color:#fff; border-left-color:var(--red); background:var(--red-dim); }
  .nav-item.active-procv .nav-icon { background:var(--red); color:#fff; box-shadow:0 4px 14px var(--red-glow); }
  .nav-item.active-ext   { color:#fff; border-left-color:#3b82f6; background:rgba(59,130,246,0.07); }
  .nav-item.active-ext .nav-icon   { background:#1d4ed8; color:#fff; box-shadow:0 4px 14px rgba(59,130,246,0.3); }
  .nav-item.active-zero  { color:#fff; border-left-color:#10b981; background:rgba(16,185,129,0.07); }
  .nav-item.active-zero .nav-icon  { background:#059669; color:#fff; box-shadow:0 4px 14px rgba(16,185,129,0.3); }
  .nav-item.active-ddi   { color:#fff; border-left-color:#f59e0b; background:rgba(245,158,11,0.07); }
  .nav-item.active-ddi .nav-icon   { background:#d97706; color:#fff; box-shadow:0 4px 14px rgba(245,158,11,0.3); }

  .sidebar-footer {
    margin-top: auto; padding: 14px 16px;
    border-top: 1px solid var(--border);
  }
  .admin-link {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 14px; border-radius: 8px;
    border: 1px solid var(--border); background: transparent;
    color: var(--text3); font-family: 'DM Sans', sans-serif;
    font-size: 12px; font-weight: 500;
    cursor: pointer; width: 100%; text-align: left;
    text-decoration: none; transition: all 0.18s;
  }
  .admin-link:hover { color:var(--text2); border-color:var(--border-red); background:var(--red-dim); }

  /* ── MAIN CONTENT ── */
  .main-content { flex: 1; min-width: 0; overflow-y: auto; }

  .page-header {
    padding: 40px 44px 28px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 36px;
  }
  .page-eyebrow {
    font-size: 10px; font-weight: 700; letter-spacing: 3px;
    color: var(--red); text-transform: uppercase; margin-bottom: 8px;
  }
  .page-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 34px; font-weight: 700; color: var(--text);
    line-height: 1.1; margin-bottom: 8px;
  }
  .page-sub { font-size: 13.5px; color: var(--text2); line-height: 1.6; }

  .content-wrap { padding: 0 44px 60px; }

  /* ── CARDS ── */
  .card {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px 28px; transition: border-color 0.2s;
  }
  .card:hover { border-color: rgba(255,255,255,0.12); }
  .card-label {
    font-size: 9px; font-weight: 700; letter-spacing: 2.5px;
    color: var(--text3); text-transform: uppercase; margin-bottom: 16px;
  }

  /* ── INFO BOX ── */
  .info-box {
    background: rgba(227,30,36,0.05);
    border: 1px solid rgba(227,30,36,0.18);
    border-radius: 10px; padding: 13px 16px;
    font-size: 12.5px; color: #fca5a5;
    line-height: 1.7; margin-bottom: 24px;
    display: flex; gap: 10px; align-items: flex-start;
  }
  .info-box b { color: #fecaca; }
  .info-box code {
    background: rgba(255,255,255,0.07); padding: 1px 6px;
    border-radius: 4px; font-family: var(--mono);
  }

  /* ── Quasar field overrides ── */
  .q-field__control { background: var(--bg3) !important; transition: background 0.2s; }
  .q-field--outlined .q-field__control { border-color: var(--border) !important; border-radius: 8px !important; border-width: 1.5px !important; }
  .q-field--outlined .q-field__control:hover { border-color: rgba(227,30,36,0.4) !important; }
  .q-field--outlined.q-field--focused .q-field__control { border-color: rgba(227,30,36,0.65) !important; box-shadow: 0 0 0 3px rgba(227,30,36,0.09) !important; }
  .q-field__native, .q-field__input { font-family: 'DM Sans', sans-serif !important; color: var(--text) !important; }
  .q-field__label { color: var(--text3) !important; }
  .list-area textarea { font-family: var(--mono) !important; font-size: 13px !important; line-height: 1.85 !important; color: #94a3b8 !important; padding-left: 14px !important; }
  .list-area .q-field__control { padding-left: 0 !important; }
  .name-input .q-field__native { padding-left: 12px !important; }

  /* ── Buttons ── */
  .action-btn {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    border-radius: 8px !important; padding: 7px 18px !important;
  }
  .btn-clear { background: var(--bg4) !important; color: var(--text2) !important; border: 1px solid var(--border) !important; }
  .btn-clear:hover { border-color: var(--border-red) !important; color: var(--text) !important; }
  .btn-copy { background: rgba(59,130,246,0.1) !important; color: #93c5fd !important; border: 1px solid rgba(59,130,246,0.2) !important; }
  .btn-copy:hover { background: rgba(59,130,246,0.18) !important; }

  /* ── PROCV main button ── */
  .procv-btn-wrap { display: flex; justify-content: center; margin: 36px 0 4px; }
  .btn-procv {
    background: linear-gradient(135deg, var(--red) 0%, var(--red-dark) 100%) !important;
    color: #fff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important; font-size: 17px !important;
    letter-spacing: 3px !important; text-transform: uppercase !important;
    border-radius: 10px !important; border: none !important;
    padding: 14px 60px !important;
    box-shadow: 0 4px 28px rgba(227,30,36,0.40), inset 0 1px 0 rgba(255,255,255,0.10) !important;
    transition: all 0.2s !important;
  }
  .btn-procv:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 40px rgba(227,30,36,0.55) !important; }
  .btn-procv:active { transform: translateY(0) !important; }

  /* ── Toolkit buttons ── */
  .btn-ext, .btn-add-zero, .btn-rem-zero, .btn-ddi {
    color: #fff !important; border: none !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important; font-weight: 700 !important;
    border-radius: 8px !important; padding: 10px 22px !important;
    transition: all 0.2s !important;
  }
  .btn-ext      { background: linear-gradient(135deg,#1d4ed8,#0891b2) !important; box-shadow: 0 4px 16px rgba(29,78,216,0.3) !important; }
  .btn-add-zero { background: linear-gradient(135deg,#059669,#0891b2) !important; box-shadow: 0 4px 16px rgba(5,150,105,0.3) !important; }
  .btn-rem-zero { background: linear-gradient(135deg,#d97706,var(--red)) !important; box-shadow: 0 4px 16px rgba(217,119,6,0.3) !important; }
  .btn-ddi      { background: linear-gradient(135deg,var(--red),#ea580c) !important; box-shadow: 0 4px 16px rgba(227,30,36,0.35) !important; }
  .btn-ext:hover, .btn-add-zero:hover, .btn-rem-zero:hover, .btn-ddi:hover { transform: translateY(-1px) !important; filter: brightness(1.1) !important; }

  /* ── Result cards ── */
  .res-card { flex: 1; border-radius: 12px; padding: 20px 24px; background: var(--bg2); border: 1px solid var(--border); min-height: 200px; transition: border-color 0.2s; }
  .res-card-a { border-color: rgba(96,165,250,0.20); }
  .res-card-b { border-color: rgba(34,211,238,0.18); }
  .res-title { font-size: 12px; font-weight: 700; margin-bottom: 14px; padding-bottom: 10px; line-height: 1.4; }
  .res-title-a { color: #60a5fa; border-bottom: 1px solid rgba(96,165,250,0.15); }
  .res-title-b { color: #22d3ee; border-bottom: 1px solid rgba(34,211,238,0.15); }
  .res-list { font-family: var(--mono); font-size: 13px; color: #94a3b8; padding-left: 4px; }
  .res-item { display: block; line-height: 2; }

  /* ── Toolkit result ── */
  .toolkit-result { margin-top: 20px; background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; animation: fadeInUp 0.3s ease; }
  .toolkit-result-header { display: flex; align-items: center; justify-content: space-between; padding: 11px 18px; background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border); }
  .toolkit-result-body { padding: 14px 18px; font-family: var(--mono); font-size: 13px; line-height: 1.9; color: #94a3b8; max-height: 320px; overflow-y: auto; word-break: break-all; }
  .toolkit-result-body::-webkit-scrollbar { width: 4px; }
  .toolkit-result-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }

  @keyframes fadeInUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }

  /* ── Badges ── */
  .stat-badge { display: inline-flex; align-items: center; gap: 7px; background: var(--bg4); border: 1px solid var(--border); border-radius: 20px; padding: 5px 14px; font-size: 12px; font-weight: 500; color: var(--text2); }
  .stat-badge b { color: var(--text); font-weight: 700; }
  .count-badge { font-size: 11px; color: var(--text2); background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 20px; padding: 3px 10px; }
  .res-label-ext { font-size: 10px; font-weight: 700; color: #7dd3fc; letter-spacing: 1.5px; text-transform: uppercase; }
  .res-label-add { font-size: 10px; font-weight: 700; color: #6ee7b7; letter-spacing: 1.5px; text-transform: uppercase; }
  .res-label-rem { font-size: 10px; font-weight: 700; color: #fcd34d; letter-spacing: 1.5px; text-transform: uppercase; }
  .res-label-ddi { font-size: 10px; font-weight: 700; color: #fca5a5; letter-spacing: 1.5px; text-transform: uppercase; }
  .warn-tag { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; color: #fcd34d; background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); border-radius: 6px; padding: 4px 10px; margin-top: 8px; }

  .empty-state { color: var(--text3); font-size: 13px; font-style: italic; padding: 8px 0; }
  .loading-row { display: flex; align-items: center; gap: 12px; color: var(--text3); font-size: 14px; padding: 24px 0; }

  /* ── Admin ── */
  .login-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 16px; padding: 40px; max-width: 380px; width: 100%; }
  .hist-row { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 18px 22px; margin-bottom: 10px; transition: border-color 0.2s; }
  .hist-row:hover { border-color: var(--border-red); }
  .hist-date { font-size: 11px; color: var(--text3); letter-spacing: 0.5px; }
  .hist-pair { font-size: 15px; font-weight: 700; color: var(--text); margin: 5px 0 4px; }
  .hist-counts { font-size: 12px; color: var(--text2); }

  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
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

    with ui.element('div').classes("app-shell"):

        # ── SIDEBAR ──────────────────────────────────
        with ui.element('div').classes("sidebar"):
            ui.html(f'''<div class="sidebar-logo">
              <img src="data:image/png;base64,{BYSAT_LOGO_B64}" alt="BySat">
              <div class="sidebar-logo-sub">Toolkit Operacional</div>
            </div>''')
            ui.html('<div class="sidebar-section">Ferramentas</div>')

            tab_procv = ui.button(on_click=lambda: show_tab(0)).classes("nav-item active-procv")
            with tab_procv:
                ui.html('<span class="nav-icon">⚡</span>')
                ui.label("PROCV")

            tab_ext = ui.button(on_click=lambda: show_tab(1)).classes("nav-item")
            with tab_ext:
                ui.html('<span class="nav-icon">✂️</span>')
                ui.label("Extrator")

            tab_zero = ui.button(on_click=lambda: show_tab(2)).classes("nav-item")
            with tab_zero:
                ui.html('<span class="nav-icon" style="font-family:monospace;font-size:12px;font-weight:700;">0±</span>')
                ui.label("+/- Zero")

            tab_ddi = ui.button(on_click=lambda: show_tab(3)).classes("nav-item")
            with tab_ddi:
                ui.html('<span class="nav-icon">📵</span>')
                ui.label("DDI 55")

            with ui.element('div').classes("sidebar-footer"):
                ui.html('<a href="/admin" class="admin-link"><span>🔐</span> Painel Admin</a>')

        # ── MAIN AREA ─────────────────────────────────
        with ui.element('div').classes("main-content"):
            panel_procv = ui.column().classes("w-full")
            panel_ext   = ui.column().classes("w-full")
            panel_zero  = ui.column().classes("w-full")
            panel_ddi   = ui.column().classes("w-full")
            panel_ext.set_visibility(False)
            panel_zero.set_visibility(False)
            panel_ddi.set_visibility(False)

            # ── PROCV ────────────────────────────────
            with panel_procv:
                ui.html('''<div class="page-header">
                  <div class="page-eyebrow">Comparador de Listas</div>
                  <div class="page-title">PROCV</div>
                  <div class="page-sub">Cole duas listas e descubra o que existe em cada uma, mas não na outra.</div>
                </div>''')
                with ui.element('div').classes("content-wrap"):
                    with ui.row().classes("w-full items-start gap-5 mb-2"):
                        with ui.column().classes("flex-1 card gap-5"):
                            ui.html('<div class="card-label">Lista A</div>')
                            nome_a = (ui.input(label="Nome da lista A (ex: MGI)")
                                .classes("w-full name-input").props("outlined dense"))
                            lista_a = (ui.textarea(label="Cole os itens aqui, um por linha")
                                .classes("w-full list-area").props("outlined").style("min-height:260px;"))
                        with ui.column().classes("flex-1 card gap-5"):
                            ui.html('<div class="card-label">Lista B</div>')
                            nome_b = (ui.input(label="Nome da lista B (ex: Físico)")
                                .classes("w-full name-input").props("outlined dense"))
                            lista_b = (ui.textarea(label="Cole os itens aqui, um por linha")
                                .classes("w-full list-area").props("outlined").style("min-height:260px;"))
                    with ui.element('div').classes("procv-btn-wrap w-full"):
                        with ui.row().classes("items-center gap-4"):
                            btn_procv_clear = ui.button("Limpar tudo", icon="close").classes("action-btn btn-clear")
                            btn_procv = ui.button("EXECUTAR PROCV", icon="bolt").classes("btn-procv")
                    procv_result_area = ui.column().classes("w-full")

            # ── EXTRATOR ─────────────────────────────
            with panel_ext:
                ui.html('''<div class="page-header">
                  <div class="page-eyebrow">Manipulação de Texto</div>
                  <div class="page-title">Extrator de Vírgula</div>
                  <div class="page-sub">Extrai o valor entre vírgulas de cada linha dos dados colados.</div>
                </div>''')
                with ui.element('div').classes("content-wrap"):
                    ui.html('<div class="info-box"><span>ℹ️</span><div>'
                        '<b>Como funciona:</b> Cole seus dados abaixo. O sistema extrai o valor entre as vírgulas de cada linha.<br>'
                        'Ex: <code>99999,0319,99999</code> → <b>0319</b></div></div>')
                    with ui.column().classes("card w-full gap-4"):
                        ui.html('<div class="card-label">Dados de Entrada</div>')
                        ext_input = (ui.textarea(label="Cole os dados aqui")
                            .classes("w-full list-area").props("outlined").style("min-height:220px;"))
                        with ui.row().classes("items-center gap-3"):
                            btn_ext_run   = ui.button("Extrair", icon="content_cut").classes("btn-ext")
                            btn_ext_clear = ui.button("Limpar", icon="close").classes("action-btn btn-clear")
                    ext_result_area = ui.column().classes("w-full")

            # ── ZERO ─────────────────────────────────
            with panel_zero:
                ui.html('''<div class="page-header">
                  <div class="page-eyebrow">Manipulação de Números</div>
                  <div class="page-title">Adicionar / Remover Zero</div>
                  <div class="page-sub">Adiciona ou remove o dígito 0 no início de cada número da lista.</div>
                </div>''')
                with ui.element('div').classes("content-wrap"):
                    ui.html('<div class="info-box"><span>ℹ️</span><div>'
                        '<b>Adicionar 0:</b> <code>31996070871</code> → <b>031996070871</b><br>'
                        '<b>Remover 0:</b> <code>031996070871</code> → <b>31996070871</b></div></div>')
                    with ui.column().classes("card w-full gap-4"):
                        ui.html('<div class="card-label">Números</div>')
                        zero_input = (ui.textarea(label="Cole os números aqui, um por linha")
                            .classes("w-full list-area").props("outlined").style("min-height:220px;"))
                        with ui.row().classes("items-center gap-3"):
                            btn_add_zero   = ui.button("Adicionar 0", icon="add").classes("btn-add-zero")
                            btn_rem_zero   = ui.button("Remover 0", icon="remove").classes("btn-rem-zero")
                            btn_zero_clear = ui.button("Limpar", icon="close").classes("action-btn btn-clear")
                    zero_result_area = ui.column().classes("w-full")

            # ── DDI 55 ───────────────────────────────
            with panel_ddi:
                ui.html('''<div class="page-header">
                  <div class="page-eyebrow">Normalização de Telefones</div>
                  <div class="page-title">Remover DDI 55</div>
                  <div class="page-sub">Remove o prefixo 55 de números brasileiros, deixando apenas o DDD e número.</div>
                </div>''')
                with ui.element('div').classes("content-wrap"):
                    ui.html('<div class="info-box"><span>ℹ️</span><div>'
                        '<b>Como funciona:</b> Remove o prefixo 55 do início de números brasileiros.<br>'
                        'Ex: <code>5531996070871</code> → <b>31996070871</b></div></div>')
                    with ui.column().classes("card w-full gap-4"):
                        ui.html('<div class="card-label">Números com DDI 55</div>')
                        ddi_input = (ui.textarea(label="Cole os números aqui, um por linha")
                            .classes("w-full list-area").props("outlined").style("min-height:220px;"))
                        with ui.row().classes("items-center gap-3"):
                            btn_ddi_run   = ui.button("Remover DDI 55", icon="phone_disabled").classes("btn-ddi")
                            btn_ddi_clear = ui.button("Limpar", icon="close").classes("action-btn btn-clear")
                    ddi_result_area = ui.column().classes("w-full")

    # ══════════════════════════════════════════════
    #  LÓGICA — navegação
    # ══════════════════════════════════════════════

    all_panels  = [panel_procv, panel_ext, panel_zero, panel_ddi]
    all_tabs    = [tab_procv, tab_ext, tab_zero, tab_ddi]
    tab_classes = ["active-procv", "active-ext", "active-zero", "active-ddi"]

    def show_tab(idx):
        for i, (panel, tab, cls) in enumerate(zip(all_panels, all_tabs, tab_classes)):
            panel.set_visibility(i == idx)
            if i == idx:
                tab.classes(add=cls)
            else:
                for c in tab_classes:
                    tab.classes(remove=c)

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
            "nome_a":       n_a, "nome_b":       n_b,
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
                with ui.element('div').classes("res-card res-card-a"):
                    with ui.row().classes("items-center justify-between w-full mb-3 gap-3"):
                        ui.html(f'<div class="res-title res-title-a" style="margin-bottom:0;">{titulo_a}</div>')
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
                with ui.element('div').classes("res-card res-card-b"):
                    with ui.row().classes("items-center justify-between w-full mb-3 gap-3"):
                        ui.html(f'<div class="res-title res-title-b" style="margin-bottom:0;">{titulo_b}</div>')
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
        ui.notify("✅ PROCV concluído!", type="positive", position="top")

    def on_procv_clear():
        nome_a.set_value(""); nome_b.set_value("")
        lista_a.set_value(""); lista_b.set_value("")
        procv_result_area.clear()
        ui.notify("Tudo limpo!", position="top")

    btn_procv.on_click(on_procv)
    btn_procv_clear.on_click(on_procv_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — EXTRATOR
    # ══════════════════════════════════════════════

    def on_extrator():
        raw = (ext_input.value or "").strip()
        if not raw:
            ui.notify("Cole os dados primeiro!", type="warning", position="top"); return
        resultados, erros = extrair_virgula(raw)
        ext_result_area.clear()
        with ext_result_area:
            with ui.element('div').classes("toolkit-result"):
                with ui.element('div').classes("toolkit-result-header"):
                    ui.html('<span class="res-label-ext">Valores Extraídos</span>')
                    with ui.row().classes("items-center gap-2"):
                        ui.html(f'<span class="count-badge">{len(resultados)} item(s)</span>')
                        if resultados:
                            btn_copy = ui.button("Copiar tudo", icon="content_copy").classes("action-btn btn-copy").props("dense")
                            btn_copy.on_click(lambda _, r=resultados: (ui.run_javascript(js_copy(r)), ui.notify("Copiado!", type="positive", position="top")))
                with ui.element('div').classes("toolkit-result-body"):
                    for item in resultados: ui.html(f'<div>{item}</div>') if resultados else ui.html('<div class="empty-state">Nenhum valor extraído.</div>')
                if erros:
                    ui.html(f'<div style="padding:8px 18px 12px;"><span class="warn-tag">⚠️ {len(erros)} linha(s) sem vírgula ignoradas</span></div>')
        if resultados: ui.notify(f"✅ {len(resultados)} valor(es) extraído(s)!", type="positive", position="top")

    def on_ext_clear():
        ext_input.set_value(""); ext_result_area.clear(); ui.notify("Tudo limpo!", position="top")

    btn_ext_run.on_click(on_extrator)
    btn_ext_clear.on_click(on_ext_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — ZERO
    # ══════════════════════════════════════════════

    def on_zero(modo: str):
        raw = (zero_input.value or "").strip()
        if not raw:
            ui.notify("Cole os números primeiro!", type="warning", position="top"); return
        resultados = processar_zero(raw, modo)
        zero_result_area.clear()
        label_text  = "Números com 0 Adicionado" if modo == "add" else "Números com 0 Removido"
        label_class = "res-label-add" if modo == "add" else "res-label-rem"
        with zero_result_area:
            with ui.element('div').classes("toolkit-result"):
                with ui.element('div').classes("toolkit-result-header"):
                    ui.html(f'<span class="{label_class}">{label_text}</span>')
                    with ui.row().classes("items-center gap-2"):
                        ui.html(f'<span class="count-badge">{len(resultados)} item(s)</span>')
                        if resultados:
                            btn_copy = ui.button("Copiar tudo", icon="content_copy").classes("action-btn btn-copy").props("dense")
                            btn_copy.on_click(lambda _, r=resultados: (ui.run_javascript(js_copy(r)), ui.notify("Copiado!", type="positive", position="top")))
                with ui.element('div').classes("toolkit-result-body"):
                    for item in resultados: ui.html(f'<div>{item}</div>') if resultados else ui.html('<div class="empty-state">Nenhum número processado.</div>')
        ui.notify(f"✅ 0 {'adicionado' if modo=='add' else 'removido'} em {len(resultados)} número(s)!", type="positive", position="top")

    def on_zero_clear():
        zero_input.set_value(""); zero_result_area.clear(); ui.notify("Tudo limpo!", position="top")

    btn_add_zero.on_click(lambda: on_zero("add"))
    btn_rem_zero.on_click(lambda: on_zero("rem"))
    btn_zero_clear.on_click(on_zero_clear)

    # ══════════════════════════════════════════════
    #  LÓGICA — DDI 55
    # ══════════════════════════════════════════════

    def on_ddi():
        raw = (ddi_input.value or "").strip()
        if not raw:
            ui.notify("Cole os números primeiro!", type="warning", position="top"); return
        resultados, sem_55 = remover_ddi55(raw)
        ddi_result_area.clear()
        with ddi_result_area:
            with ui.element('div').classes("toolkit-result"):
                with ui.element('div').classes("toolkit-result-header"):
                    ui.html('<span class="res-label-ddi">Números sem DDI 55</span>')
                    with ui.row().classes("items-center gap-2"):
                        ui.html(f'<span class="count-badge">{len(resultados)} item(s)</span>')
                        if resultados:
                            btn_copy = ui.button("Copiar tudo", icon="content_copy").classes("action-btn btn-copy").props("dense")
                            btn_copy.on_click(lambda _, r=resultados: (ui.run_javascript(js_copy(r)), ui.notify("Copiado!", type="positive", position="top")))
                with ui.element('div').classes("toolkit-result-body"):
                    for item in resultados: ui.html(f'<div>{item}</div>') if resultados else ui.html('<div class="empty-state">Nenhum número processado.</div>')
                if sem_55:
                    ui.html(f'<div style="padding:8px 18px 12px;"><span class="warn-tag">⚠️ {sem_55} número(s) sem prefixo 55</span></div>')
        if sem_55:
            ui.notify(f"⚠️ {sem_55} número(s) sem o prefixo 55", type="warning", position="top")
        else:
            ui.notify(f"✅ DDI 55 removido de {len(resultados)} número(s)!", type="positive", position="top")

    def on_ddi_clear():
        ddi_input.set_value(""); ddi_result_area.clear(); ui.notify("Tudo limpo!", position="top")

    btn_ddi_run.on_click(on_ddi)
    btn_ddi_clear.on_click(on_ddi_clear)


@ui.page('/admin')
def admin_page():
    ui.add_head_html(GLOBAL_CSS)

    with ui.element('div').classes("app-shell"):

        with ui.element('div').classes("sidebar"):
            ui.html(f'''<div class="sidebar-logo">
              <img src="data:image/png;base64,{BYSAT_LOGO_B64}" alt="BySat">
              <div class="sidebar-logo-sub">Toolkit Operacional</div>
            </div>''')
            ui.html('<div class="sidebar-section">Navegação</div>')
            ui.html('<a href="/" style="display:flex;align-items:center;gap:12px;padding:10px 24px;color:var(--text2);font-size:13.5px;font-weight:500;text-decoration:none;border-left:3px solid transparent;transition:all 0.18s;" onmouseover="this.style.color=\'var(--text)\'" onmouseout="this.style.color=\'var(--text2)\'"><span style="width:30px;height:30px;border-radius:7px;background:var(--bg4);display:flex;align-items:center;justify-content:center;font-size:14px;">⚡</span> PROCV Toolkit</a>')
            ui.html('<div class="sidebar-section">Admin</div>')
            ui.html('<div style="padding:10px 24px;color:var(--red);font-size:13.5px;font-weight:600;border-left:3px solid var(--red);background:var(--red-dim);display:flex;align-items:center;gap:12px;"><span style="width:30px;height:30px;border-radius:7px;background:var(--red);color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;">🔐</span> Histórico</div>')

        with ui.element('div').classes("main-content"):
            ui.html('''<div class="page-header">
              <div class="page-eyebrow">Área Restrita</div>
              <div class="page-title">Painel Admin</div>
              <div class="page-sub">Histórico de comparações realizadas no sistema.</div>
            </div>''')

            with ui.element('div').classes("content-wrap"):
                login_sec   = ui.column().classes("w-full items-center justify-center").style("min-height:55vh;")
                history_sec = ui.column().classes("w-full gap-3")
                history_sec.set_visibility(False)

                def render_history():
                    history_sec.clear()
                    with history_sec:
                        history = load_history()
                        with ui.row().classes("items-center justify-between w-full mb-4"):
                            ui.html('<h2 style="font-family:Rajdhani,sans-serif;font-size:24px;font-weight:700;">Histórico de PROCVs</h2>')
                            ui.html(f'<span class="stat-badge"><b>{len(history)}</b> registros</span>')
                        if not history:
                            ui.html('<div style="text-align:center;padding:60px 0;color:var(--text3);font-size:14px;">Nenhum PROCV realizado ainda.</div>')
                            return
                        for entry in history:
                            with ui.element('div').classes("hist-row w-full"):
                                with ui.row().classes("w-full items-start justify-between gap-4"):
                                    with ui.column().classes("gap-1 flex-1"):
                                        ui.html(f'<div class="hist-date">🕐 {entry["data"]}</div>')
                                        ui.html(f'<div class="hist-pair">{entry["nome_a"]} <span style="color:var(--red);margin:0 8px;">↔</span> {entry["nome_b"]}</div>')
                                        ui.html(f'<div class="hist-counts">Total A: <b>{entry["total_a"]}</b> &nbsp;|&nbsp; Total B: <b>{entry["total_b"]}</b> &nbsp;|&nbsp; Só em A: <b style="color:#93c5fd">{len(entry["apenas_em_a"])}</b> &nbsp;|&nbsp; Só em B: <b style="color:#67e8f9">{len(entry["apenas_em_b"])}</b></div>')
                                    with ui.expansion("Ver itens").props("dense").style("color:var(--red);font-size:12px;font-weight:600;"):
                                        with ui.row().classes("gap-6 w-full mt-3"):
                                            with ui.column().classes("flex-1 gap-1"):
                                                ui.html(f'<div style="font-size:10px;font-weight:700;color:#93c5fd;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">{entry.get("titulo_col_a","Só em A")}</div>')
                                                if entry["apenas_em_a"]:
                                                    for item in entry["apenas_em_a"]:
                                                        ui.html(f'<div style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748b;padding:1px 0;">{item}</div>')
                                                else:
                                                    ui.html('<div class="empty-state" style="font-size:12px;">Nenhum item exclusivo</div>')
                                            with ui.column().classes("flex-1 gap-1"):
                                                ui.html(f'<div style="font-size:10px;font-weight:700;color:#67e8f9;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">{entry.get("titulo_col_b","Só em B")}</div>')
                                                if entry["apenas_em_b"]:
                                                    for item in entry["apenas_em_b"]:
                                                        ui.html(f'<div style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748b;padding:1px 0;">{item}</div>')
                                                else:
                                                    ui.html('<div class="empty-state" style="font-size:12px;">Nenhum item exclusivo</div>')

                def show_login():
                    login_sec.set_visibility(True)
                    history_sec.set_visibility(False)
                    login_sec.clear()
                    with login_sec:
                        with ui.element('div').classes("login-card"):
                            with ui.column().classes("items-center gap-5 w-full"):
                                ui.html('<div style="width:64px;height:64px;border-radius:14px;background:linear-gradient(135deg,var(--red),var(--red-dark));display:flex;align-items:center;justify-content:center;font-size:28px;box-shadow:0 8px 32px var(--red-glow);">🔐</div>')
                                ui.html('<div style="text-align:center;"><div style="font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700;color:var(--text);margin-bottom:6px;">Acesso Admin</div><div style="font-size:13px;color:var(--text2);line-height:1.5;">Área restrita. Insira a senha para continuar.</div></div>')
                                pwd = (ui.input("Senha de acesso", password=True, password_toggle_button=True)
                                    .classes("w-full").props("outlined"))
                                err = ui.label("").style("color:#f87171;font-size:13px;")

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
                                (ui.button("Entrar", icon="lock_open", on_click=do_login)
                                    .classes("w-full")
                                    .style("background:linear-gradient(135deg,var(--red),var(--red-dark));color:white;"
                                           "font-family:Rajdhani,sans-serif;font-weight:700;font-size:16px;"
                                           "letter-spacing:1px;border-radius:10px;padding:12px 0;"
                                           "box-shadow:0 4px 24px var(--red-glow);"))

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
    title="BySat – PROCV Toolkit",
    favicon="⚡",
    dark=True,
    reload=False,
    show=False,
    storage_secret=STORAGE_SECRET,
)
