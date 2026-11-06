"""
Monitoramento de Rodovias (versao de portfolio).

Painel Streamlit que cruza noticias de ocorrencias em rodovias com a posicao
GPS dos carros e com o acompanhamento de atrasos das viagens.

Todos os dados sao sinteticos (scripts/gerar_dados_sinteticos.py) e o relogio
do painel fica fixo no horario do snapshot, para os filtros funcionarem.

Execute com:  streamlit run app.py
Na web, o mesmo app roda no navegador via stlite (index.html).
"""
import os
import json
import html
import datetime as dt

import streamlit as st
import streamlit.components.v1 as components

from monitor import config as cfgmod
from monitor import mapa
from monitor import frota
from monitor.processa import CATEGORIAS
from monitor import __version__ as VERSAO

BASE = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Monitoramento de Rodovias", page_icon=None,
                   layout="wide")

CAT_NOMES = [c[0] for c in CATEGORIAS] + ["Outros"]
SEV_COR = {"Alta": "#d23a2e", "Media": "#cf9500", "Baixa": "#2e8b57"}
CHIP_CLARO = {"#f7c01a"}  # fundos claros usam texto escuro


def _txt_chip(cor):
    return "#161a2e" if str(cor).lower() in CHIP_CLARO else "#fff"


MAP_ICON = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
            'stroke="#ffffff" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round">'
            '<path d="M12 21s-6-5.686-6-10a6 6 0 1 1 12 0c0 4.314-6 10-6 10z"/>'
            '<circle cx="12" cy="11" r="2.5"/></svg>')

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
:root{
  --ink:#161a2e; --ink2:#222743; --paper:#f6f3ea; --paperline:#ddd6c2;
  --primary:#46467f; --primaryd:#33335a; --blue:#5e86d6; --yellow:#f7c01a;
  --wine:#9c2742; --green:#2e8b57; --muted:#6b6f86; --line:#0d1024;
  --pix:"Press Start 2P","Courier New",monospace;
  --sans:"Segoe UI",system-ui,Arial,sans-serif;
  --shadow:5px 5px 0 0 var(--line); --shadowsm:3px 3px 0 0 var(--line);
}
.stApp{
  background:
    repeating-linear-gradient(0deg, rgba(255,255,255,.025) 0 2px, transparent 2px 4px),
    radial-gradient(circle at 25% -10%, #2b3160 0%, #161a2e 62%);
  background-attachment:fixed;
}
.block-container{ padding-top:4.5rem; max-width:1800px; }
header[data-testid="stHeader"]{ background:transparent; }
div[data-testid="stToolbar"]{ right:8px; }
img{ image-rendering:auto; }

/* cabecalho */
.gb-header{ display:flex; align-items:center; gap:18px; flex-wrap:wrap;
  background:var(--ink2); border:4px solid var(--line); box-shadow:var(--shadow);
  padding:14px 20px; margin:0 0 18px; }
.gb-mark{ font-family:var(--pix); font-size:16px; color:var(--ink); background:var(--yellow);
  border:3px solid var(--line); box-shadow:var(--shadowsm); padding:12px 10px; }
.gb-brand{ font-family:var(--pix); color:var(--yellow); font-size:17px; line-height:1.55;
  text-shadow:3px 3px 0 var(--wine); letter-spacing:1px; padding-left:16px;
  border-left:3px solid var(--line); margin:0; }
.gb-brand small{ display:block; font-family:var(--sans); font-size:10px;
  color:var(--blue); margin-top:8px; letter-spacing:0; }

/* titulos de secao */
.gb-h2{ font-family:var(--pix); font-size:14px; color:var(--paper);
  margin:20px 0 14px; text-shadow:2px 2px 0 var(--line); }
.gb-upd{ font-size:13px; color:#aab0cc; margin:8px 0 14px; }

/* metricas */
div[data-testid="stMetric"]{ background:var(--paper); border:4px solid var(--line);
  box-shadow:var(--shadowsm); padding:10px 14px; }
div[data-testid="stMetric"] label, div[data-testid="stMetricLabel"]{
  color:var(--primaryd) !important; font-weight:700; }
div[data-testid="stMetricValue"]{ font-family:var(--pix); font-size:20px; color:var(--primary); }

/* botoes */
.stButton>button{ font-family:var(--pix); font-size:11px; color:#fff; background:var(--primary);
  border:3px solid var(--line); border-radius:0; box-shadow:var(--shadowsm); padding:11px 12px; }
.stButton>button:hover{ background:var(--primaryd); color:#fff; border-color:var(--line); }
.stButton>button:active{ transform:translate(2px,2px); box-shadow:1px 1px 0 0 var(--line); }
.stButton>button[kind="primary"]{ background:var(--yellow); color:var(--ink); }

/* sidebar */
section[data-testid="stSidebar"]{ border-right:4px solid var(--line); }
.gb-side-title{ font-family:var(--pix); font-size:14px; color:var(--yellow);
  text-shadow:2px 2px 0 var(--wine); margin:2px 0 8px; }
.gb-side-sub{ font-family:var(--pix); font-size:10px; color:var(--blue); margin:8px 0 4px; }

/* grade de cards */
.gb-grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(360px,1fr)); gap:18px; }
.gb-card{ background:var(--paper); border:4px solid var(--line); box-shadow:var(--shadow);
  display:flex; flex-direction:column; }
.gb-top{ height:10px; border-bottom:2px solid var(--line); }
.gb-cbody{ padding:14px 16px 16px; }
.gb-chip{ display:inline-block; font-family:var(--pix); font-size:9px; color:#fff;
  padding:5px 8px; border:2px solid var(--line); margin:0 6px 9px 0; }
.gb-title{ font-size:16px; font-weight:800; color:var(--primaryd); line-height:1.3; margin:6px 0 8px; }
.gb-title a{ color:var(--primaryd); text-decoration:none; }
.gb-title a:hover{ color:var(--primary); text-decoration:underline; }
.gb-resumo{ font-size:14px; color:#2c3147; line-height:1.5; margin:6px 0; }
.gb-meta{ font-size:13px; color:var(--muted); margin-top:10px;
  border-top:2px dotted var(--paperline); padding-top:8px; line-height:1.55; }
.gb-meta b{ color:var(--primaryd); }
.gb-links{ margin-top:11px; }
.gb-links a{ font-family:var(--pix); font-size:9px; color:#fff; background:var(--blue);
  border:2px solid var(--line); padding:6px 8px; margin-right:8px; text-decoration:none;
  display:inline-block; }
.gb-links a:hover{ filter:brightness(1.12); }
.gb-stack{ display:flex; flex-direction:column; gap:14px; }
.gb-scroll{ max-height:700px; overflow-y:auto; padding-right:8px; }
.gb-scroll::-webkit-scrollbar{ width:10px; }
.gb-scroll::-webkit-scrollbar-thumb{ background:var(--primary); border:2px solid var(--line); }
.gb-scroll::-webkit-scrollbar-track{ background:var(--ink2); }
.gb-footer{ margin:26px 0 8px; padding:12px 16px; background:var(--ink2);
  border:3px solid var(--line); box-shadow:var(--shadowsm); color:#aab0cc;
  font-size:12px; display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.gb-ver{ font-family:var(--pix); font-size:9px; color:#fff; background:var(--blue);
  border:2px solid var(--line); padding:5px 8px; }
.gb-foot-name{ font-family:var(--pix); font-size:9px; color:var(--yellow); }
.gb-row1{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; margin-bottom:9px; }
.gb-row1 .gb-chip{ margin:0; }
.gb-actions{ margin-left:auto; display:inline-flex; gap:6px; align-items:center; }
.gb-btn{ font-family:var(--pix); font-size:9px; color:#fff; background:var(--blue);
  border:2px solid var(--line); padding:6px 8px; text-decoration:none; display:inline-block; }
.gb-btn:hover{ filter:brightness(1.12); }
.gb-iconbtn{ display:inline-flex; align-items:center; justify-content:center;
  width:28px; height:26px; background:var(--blue); border:2px solid var(--line); }
.gb-iconbtn:hover{ filter:brightness(1.12); }
.gb-linhas{ font-size:11px; color:var(--muted); margin-top:9px; line-height:1.55;
  border-top:2px dotted var(--paperline); padding-top:7px; cursor:help; }
.gb-linhas b{ color:var(--primaryd); }
.gb-side-upd{ font-size:11px; color:#aab0cc; margin:8px 0 2px; }
.gb-side-link{ display:inline-block; font-family:var(--pix); font-size:9px; color:#fff !important;
  background:var(--primary); border:2px solid var(--line); padding:7px 9px; margin-top:8px;
  text-decoration:none !important; }
.gb-side-link:hover{ background:var(--primaryd); }
.gb-side-link-top{ width:100%; text-align:center; margin:0 0 12px; }
section[data-testid="stSidebar"] .st-key-abrir_carros button,
section[data-testid="stSidebar"] .st-key-abrir_atrasos button,
section[data-testid="stSidebar"] .st-key-voltar_mapa button{
  font-family:var(--pix); font-size:9px; color:#fff !important;
  background:var(--primary); border:2px solid var(--line); border-radius:0;
  padding:9px 10px; margin-bottom:6px; }
section[data-testid="stSidebar"] .st-key-abrir_carros button p,
section[data-testid="stSidebar"] .st-key-abrir_atrasos button p,
section[data-testid="stSidebar"] .st-key-voltar_mapa button p{ color:#fff !important; }
section[data-testid="stSidebar"] .st-key-abrir_carros button:hover,
section[data-testid="stSidebar"] .st-key-voltar_mapa button:hover{ background:var(--primaryd); }
/* Atrasos: destaque em vinho, diferente do azul do "Abrir tabela de carros" */
section[data-testid="stSidebar"] .st-key-abrir_atrasos button{
  background:var(--wine); border-color:var(--line); }
section[data-testid="stSidebar"] .st-key-abrir_atrasos button:hover{ background:#7d1f34; }
/* esconde a navegacao automatica de paginas (usamos a alternancia por botoes) */
div[data-testid="stSidebarNav"]{ display:none; }
.gb-btn, .gb-iconbtn{ color:#fff !important; text-decoration:none !important; }
.gb-btn:hover, .gb-iconbtn:hover{ text-decoration:none !important; filter:brightness(1.12); }
.gb-aviso{ background:var(--paper); color:var(--ink); border:3px solid var(--line);
  box-shadow:var(--shadowsm); padding:8px 12px; margin:0 0 16px; font-size:13px; }
.gb-aviso b{ color:var(--wine); }
"""

st.markdown("<style>" + CSS + "</style>", unsafe_allow_html=True)


@st.cache_data
def _carregar_config():
    return cfgmod.load_config()


CFG = _carregar_config()
APP = CFG["app"]
DADOS = CFG["dados"]


@st.cache_data
def _carregar_meta():
    try:
        with open(cfgmod.caminho(DADOS["meta"]), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


META = _carregar_meta()
# Relogio simulado: o "agora" do painel e o horario do snapshot sintetico.
AGORA = (dt.datetime.fromisoformat(META["agora"]) if META.get("agora")
         else dt.datetime.now())


def _fmt_dt(t, fmt="%d/%m/%Y %H:%M"):
    return t.strftime(fmt) if isinstance(t, dt.datetime) else "-"


def _parse_dt(s):
    try:
        return dt.datetime.fromisoformat(s) if s else None
    except (TypeError, ValueError):
        return None


TZ_BR_DESLOC = dt.timedelta(hours=-3)


@st.cache_data
def _carregar_noticias():
    try:
        with open(cfgmod.caminho(DADOS["noticias"]), encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, ValueError):
        return [], {}
    itens = payload.get("itens", []) or []
    meta = payload.get("meta", {}) or {}
    # A coleta real grava horarios em UTC; o painel exibe em Brasilia (UTC-3).
    desloc = TZ_BR_DESLOC if meta.get("fuso") == "UTC" else dt.timedelta(0)
    for it in itens:
        p = _parse_dt(it.get("publicado"))
        it["publicado"] = p + desloc if p else None
    ult = _parse_dt(meta.get("atualizado_em"))
    meta["_atualizado_dt"] = ult + desloc if ult else None
    return itens, meta


def mostrar_mapa(m, altura):
    """Renderiza um mapa folium como HTML (funciona no Streamlit e no stlite).
    Usa st.iframe quando disponivel e components.html nas versoes anteriores."""
    doc = m.get_root().render()
    if hasattr(st, "iframe"):
        st.iframe(doc, height=altura)
    else:
        components.html(doc, height=altura)


# ---------- cabecalho ----------
st.markdown(
    '<div class="gb-header"><div class="gb-mark">MR</div>'
    '<div class="gb-brand">MONITORAMENTO RODOVIAS'
    '<small>Interdicoes, transito e ocorrencias cruzadas com a frota</small>'
    '</div></div>', unsafe_allow_html=True)
itens_all, _meta_news = _carregar_noticias()
_ult = _meta_news.get("_atualizado_dt")
NOTICIAS_REAIS = _meta_news.get("fonte") == "Google Noticias RSS"
# Referencia do filtro de periodo das noticias: o horario da coleta.
REF_NOTICIAS = _ult or AGORA

if NOTICIAS_REAIS:
    _aviso = (f'<b>Noticias reais</b>, coletadas no Google Noticias pelo '
              f'pipeline do projeto (GitHub Actions, a cada 30 min; ultima '
              f'coleta {_fmt_dt(_ult)}). <b>Demo de portfolio:</b> linhas, '
              f'carros, placas, GPS e atrasos sao sinteticos, com relogio '
              f'fixo no snapshot de {_fmt_dt(AGORA)}.')
else:
    _aviso = (f'<b>Demo de portfolio.</b> Todos os dados sao sinteticos '
              f'(linhas, carros, placas, horarios, posicoes e noticias). '
              f'Relogio fixo no snapshot de {_fmt_dt(AGORA)}.')
st.markdown(f'<div class="gb-aviso">{_aviso}</div>', unsafe_allow_html=True)

# ---------- navegacao ----------
st.sidebar.markdown(
    '<div style="font-family:var(--pix);font-size:9px;color:var(--yellow);'
    'background:var(--primaryd);border:2px solid var(--line);'
    'box-shadow:2px 2px 0 var(--line);padding:6px 8px;text-align:center;'
    f'letter-spacing:1px;margin:0 0 12px;">v{html.escape(VERSAO)}</div>',
    unsafe_allow_html=True)
_view_atual = st.session_state.get("view", "mapa")
if _view_atual in ("carros", "atrasos"):
    if st.sidebar.button("Voltar ao mapa", key="voltar_mapa",
                         use_container_width=True):
        st.session_state["view"] = "mapa"
        st.rerun()
else:
    if st.sidebar.button("Abrir tabela de carros", key="abrir_carros",
                         use_container_width=True):
        st.session_state["view"] = "carros"
        st.rerun()
    if st.sidebar.button("Acompanhamento de Atrasos", key="abrir_atrasos",
                         use_container_width=True):
        st.session_state["view"] = "atrasos"
        st.rerun()

_fcfg = CFG.get("frota", {})
_gps_path = cfgmod.caminho(DADOS["gps"])
_gps_ok = os.path.exists(_gps_path)

if _view_atual == "atrasos":
    from monitor import atrasos_page
    atrasos_page.render(CFG, AGORA, mostrar_mapa)
    st.stop()


def _tabela_carros(path, ok, fcfg):
    """Visao 'tabela de carros'."""
    if st.button("Voltar ao mapa e noticias", key="voltar_mapa_top",
                 type="primary"):
        st.session_state["view"] = "mapa"
        st.rerun()
    st.markdown('<div class="gb-h2">CARROS - GPS</div>', unsafe_allow_html=True)
    if not ok:
        st.warning("Sem posicoes de GPS disponiveis.")
        return
    janela = int(fcfg.get("janela_min", 60))
    carros, ref = frota.carregar_frota(path, janela_min=janela, hoje=AGORA.date())
    if not carros:
        st.warning("Nenhum carro com posicao valida na janela atual.")
        return
    fc1, fc2 = st.columns([2, 1])
    busca = fc1.text_input("Buscar carro",
                           placeholder="ex.: 9136").strip().upper()
    empresas = ["Todas"] + sorted({c.get("empresa", "") for c in carros
                                   if c.get("empresa")})
    emp = fc2.selectbox("Empresa", empresas)
    linhas = []
    for c in carros:
        if busca and busca not in c.get("veiculo", "").upper():
            continue
        if emp != "Todas" and c.get("empresa") != emp:
            continue
        d = c.get("dist_local")
        linhas.append({
            "Carro": c.get("veiculo", ""),
            "Empresa": c.get("empresa", ""),
            "Ultima transmissao": _fmt_dt(c.get("dh")),
            "Local mais proximo": c.get("local", ""),
            "Dist. do local (km)": (round(d, 1)
                                    if isinstance(d, (int, float)) else None),
        })
    st.caption(f"{len(linhas)} de {len(carros)} carros "
               f"(janela {janela} min, ref {_fmt_dt(ref)})")
    import pandas as pd
    st.dataframe(pd.DataFrame(linhas), use_container_width=True,
                 hide_index=True, height=560)


if _view_atual == "carros":
    _tabela_carros(_gps_path, _gps_ok, _fcfg)
    st.stop()

# ---------- sidebar: filtros ----------
st.sidebar.markdown('<div class="gb-side-title">FILTROS</div>',
                    unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div class="gb-side-upd">Ultima coleta de noticias: {_fmt_dt(_ult)}'
    f'{"<br>Google Noticias, a cada 30 min" if NOTICIAS_REAIS else ""}</div>',
    unsafe_allow_html=True)
rodovias_disp = sorted({i.get("rodovia", "")
                        for i in itens_all if i.get("rodovia")})
cat_default = [c for c in ["Interdicao", "Acidente", "Congestionamento"]
               if c in CAT_NOMES]

f_rod = st.sidebar.multiselect("Rodovia/Corredor", rodovias_disp, key="f_rod")
f_cat = st.sidebar.multiselect("Categoria", CAT_NOMES, default=cat_default,
                               key="f_cat")
f_sev = st.sidebar.multiselect("Severidade", ["Alta", "Media", "Baixa"],
                               default=["Alta", "Media"], key="f_sev")
f_dias = st.sidebar.slider("Periodo (dias)", 1, 7,
                           int(APP.get("periodo_default", 3)), key="f_dias")

st.sidebar.divider()
st.sidebar.caption(f"Rodovias monitoradas: {len(CFG.get('rodovias', []))}  |  "
                   f"Hubs: {len(CFG.get('hubs', []))}")

# ---- controles GPS (carros) ----
st.sidebar.divider()
st.sidebar.markdown('<div class="gb-side-sub">CARROS (GPS)</div>',
                    unsafe_allow_html=True)
if _gps_ok:
    _mostrar_carros = st.sidebar.checkbox(
        "Mostrar carros", value=bool(_fcfg.get("mostrar", True)),
        key="mostrar_carros")
    _so_prox = st.sidebar.checkbox("Apenas proximos a ocorrencias", value=True,
                                   key="so_prox")
    _raio = st.sidebar.number_input(
        "Raio proximidade (km)", min_value=1, max_value=200,
        value=int(_fcfg.get("raio_km", 15)), step=1, key="raio_km")
else:
    _mostrar_carros = False
    _so_prox = False
    _raio = int(_fcfg.get("raio_km", 15))
    st.sidebar.caption("GPS indisponivel (arquivo nao encontrado).")

# ---------- filtragem ----------
limite = REF_NOTICIAS - dt.timedelta(days=int(f_dias))


def no_periodo(it):
    p = it.get("publicado")
    return not (isinstance(p, dt.datetime) and p < limite)


itens_periodo = [i for i in itens_all if no_periodo(i)]


def passa(it):
    if f_rod and it.get("rodovia") not in f_rod:
        return False
    if f_cat and it.get("categoria") not in f_cat:
        return False
    if f_sev and it.get("severidade") not in f_sev:
        return False
    return True


itens = [i for i in itens_periodo if passa(i)]

# ---------- frota (GPS) ----------
_carros = []
_ref_gps = None
_nprox = 0
if _gps_ok and _mostrar_carros:
    _carros, _ref_gps = frota.carregar_frota(
        _gps_path, janela_min=int(_fcfg.get("janela_min", 60)),
        hoje=AGORA.date())
    _nprox = frota.marcar_proximos(_carros, itens, raio_km=float(_raio))

if not itens_all:
    st.info("Sem dados. Rode: python scripts/gerar_dados_sinteticos.py")
    st.stop()


def _card_html(it):
    cor = it.get("cor", "#6b6f86")
    cat = html.escape(it.get("categoria", ""))
    sev = html.escape(it.get("severidade", ""))
    sevcor = SEV_COR.get(it.get("severidade"), "#6b6f86")
    titulo = html.escape(it.get("titulo", "(sem titulo)"))
    local = html.escape(it.get("local", "-"))
    rod = html.escape(it.get("rodovia", "-"))
    fonte = html.escape(it.get("fonte", "-"))
    d = it.get("publicado")
    dtxt = d.strftime("%d/%m %H:%M") if isinstance(d, dt.datetime) else ""
    resumo = (it.get("resumo") or "").strip()
    # No RSS do Google Noticias o resumo costuma repetir o titulo: so exibe
    # quando acrescenta informacao.
    resumo_html = ("" if not resumo or resumo[:40] == it.get("titulo", "")[:40]
                   else f'<div class="gb-resumo">{html.escape(resumo)}</div>')
    link = it.get("link", "")
    titulo_html = (f'<a href="{html.escape(link)}" target="_blank" '
                   f'rel="noopener">{titulo}</a>' if link else titulo)
    acoes = ""
    if link:
        acoes += (f'<a class="gb-btn" href="{html.escape(link)}" '
                  f'target="_blank" rel="noopener">Abrir noticia</a>')
    if it.get("lat") is not None and it.get("lon") is not None:
        acoes += (f'<a class="gb-iconbtn" title="Ver no mapa" '
                  f'aria-label="Ver no mapa" target="_blank" '
                  f'href="https://www.google.com/maps?q={it["lat"]},{it["lon"]}">'
                  f'{MAP_ICON}</a>')
    linhas = it.get("linhas") or []
    ltot = it.get("linhas_total", len(linhas))
    linhas_html = ""
    if ltot:
        tip = "\n".join(linhas)
        if ltot > len(linhas):
            tip += f"\n(+{ltot - len(linhas)} outras)"
        linhas_html = (f'<div class="gb-linhas" title="{html.escape(tip)}">'
                       f'<b>Possiveis Linhas Afetadas</b> ({ltot}): '
                       f'{html.escape(", ".join(linhas[:6]))}'
                       f'{" ..." if ltot > 6 else ""}</div>')
    return (
        f'<div class="gb-card"><div class="gb-top" style="background:{cor}"></div>'
        f'<div class="gb-cbody"><div class="gb-row1">'
        f'<span class="gb-chip" style="background:{cor};color:{_txt_chip(cor)}">{cat}</span>'
        f'<span class="gb-chip" style="background:{sevcor};color:{_txt_chip(sevcor)}">{sev}</span>'
        f'<span class="gb-actions">{acoes}</span></div>'
        f'<div class="gb-title">{titulo_html}</div>'
        f'{resumo_html}'
        f'<div class="gb-meta"><b>Local:</b> {local} &nbsp;|&nbsp; '
        f'<b>Rodovia:</b> {rod}<br><b>Fonte:</b> {fonte} - {dtxt}</div>'
        f'{linhas_html}</div></div>')


col_cards, col_main = st.columns([1, 2], gap="large")

with col_cards:
    st.markdown(f'<div class="gb-h2">OCORRENCIAS ({len(itens)})</div>',
                unsafe_allow_html=True)
    if not itens:
        st.warning("Nenhuma ocorrencia para os filtros selecionados.")
    else:
        MAX = 120
        cards = "".join(_card_html(it) for it in itens[:MAX])
        st.markdown('<div class="gb-scroll"><div class="gb-stack">' + cards
                    + '</div></div>', unsafe_allow_html=True)

with col_main:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Ocorrencias (periodo)", len(itens_periodo))
    m2.metric("Interdicoes",
              sum(1 for i in itens_periodo if i.get("categoria") == "Interdicao"))
    m3.metric("Acidentes",
              sum(1 for i in itens_periodo if i.get("categoria") == "Acidente"))
    m4.metric("Severidade alta",
              sum(1 for i in itens_periodo if i.get("severidade") == "Alta"))
    m5.metric("Carros proximos", _nprox)
    st.markdown(
        f'<div class="gb-upd">Exibindo {len(itens)} de '
        f'{len(itens_periodo)} no periodo</div>', unsafe_allow_html=True)
    if _gps_ok and _mostrar_carros:
        _rtxt = _ref_gps.strftime("%d/%m %H:%M") if _ref_gps else "-"
        st.markdown(
            f'<div class="gb-upd">GPS: {len(_carros)} carros (ref {_rtxt}) '
            f'&nbsp;|&nbsp; {_nprox} proximos (ate {int(_raio)} km)</div>',
            unsafe_allow_html=True)
    st.markdown('<div class="gb-h2">MAPA DAS OCORRENCIAS</div>',
                unsafe_allow_html=True)
    mostrar_mapa(mapa.construir_mapa(itens, usar_cluster=True,
                                     carros=(_carros or None),
                                     so_proximos=_so_prox), 600)

# ---------- rodape ----------
st.markdown(
    f'<div class="gb-footer"><span class="gb-ver">v{html.escape(VERSAO)}</span>'
    f'<span class="gb-foot-name">MONITORAMENTO RODOVIAS</span>'
    f'<span>Demo de portfolio: '
    f'{"noticias reais do Google Noticias; " if NOTICIAS_REAIS else ""}'
    f'linhas, frota e atrasos sinteticos</span></div>',
    unsafe_allow_html=True)
