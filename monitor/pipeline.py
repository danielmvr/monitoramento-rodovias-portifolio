"""Orquestracao: coleta -> processamento -> geocodificacao -> cache."""
import json
import os
import datetime as dt

from .config import load_config, data_path
from .coleta import coletar
from .processa import processar_item, linhas_afetadas
from .geocode import GeoCoder, rep_rodovias

# Saida padrao da coleta ao vivo quando rodada localmente (fora do Git).
# Na versao web, o workflow .github/workflows/noticias.yml grava a coleta no
# branch 'dados-noticias', que o index.html le ao abrir o painel.
RESULT_FILE = data_path("noticias_coletadas.json")


def _serial(item):
    it = dict(item)
    p = it.get("publicado")
    it["publicado"] = p.isoformat() if hasattr(p, "isoformat") else None
    it.pop("origem_meta", None)
    return it


def _parse_dt(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def salvar_resultados(itens, meta, saida=None):
    payload = {"meta": meta, "itens": [_serial(i) for i in itens]}
    try:
        with open(saida or RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1, default=str)
    except Exception:
        pass


def carregar_resultados():
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    for it in payload.get("itens", []):
        it["publicado"] = _parse_dt(it.get("publicado"))
    return payload


def executar(cfg=None, fetch_fn=None, usar_nominatim=True, sleep_s=1.0,
             status_cb=None, saida=None):
    """Roda a coleta completa e devolve (itens, meta). Tambem grava o resultado
    em 'saida' (padrao: data/noticias_coletadas.json)."""
    cfg = cfg or load_config()
    crus = coletar(cfg, fetch_fn=fetch_fn, sleep_s=sleep_s,
                   status_cb=status_cb)
    geo = GeoCoder(cfg, usar_nominatim=usar_nominatim)
    rod_rep = rep_rodovias(cfg)
    itens = []
    total_g = len(crus)
    for gi, c in enumerate(crus, 1):
        if status_cb:
            status_cb(gi, total_g, f"Localizando {gi}/{total_g}")
        proc = processar_item(c, cfg)
        proc.update(geo.localizar(proc, rod_rep))
        laf, ltot = linhas_afetadas(
            proc.get("lat"), proc.get("lon"),
            thresh_km=cfg["app"].get("linhas_raio_km", 40))
        proc["linhas"] = laf
        proc["linhas_total"] = ltot
        itens.append(proc)
    geo.salvar()
    itens.sort(key=lambda x: x.get("publicado") or dt.datetime.min,
               reverse=True)
    # Horarios do RSS e da coleta em UTC (sem fuso no texto); o painel
    # converte para o horario de Brasilia na exibicao.
    meta = {"atualizado_em": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None, microsecond=0).isoformat(),
            "total": len(itens), "fonte": "Google Noticias RSS", "fuso": "UTC"}
    salvar_resultados(itens, meta, saida)
    return itens, meta


if __name__ == "__main__":
    # Coleta ao vivo no Google Noticias (requer internet e as dependencias de
    # requirements-coleta.txt). Uso:
    #     python -m monitor.pipeline [arquivo_de_saida]
    # Sai com codigo 2, sem gravar nada, se o Google bloquear ou nada vier,
    # para nao sobrescrever um resultado bom com um vazio.
    import sys
    from .coleta import ColetaBloqueada

    _saida = sys.argv[1] if len(sys.argv) > 1 else RESULT_FILE
    try:
        _itens, _meta = executar(usar_nominatim=False, sleep_s=0.6,
                                 saida=os.devnull)
    except ColetaBloqueada as e:
        print(f"Coleta bloqueada: {e}")
        sys.exit(2)
    if not _itens:
        print("Nenhuma noticia coletada; arquivo anterior mantido.")
        sys.exit(2)
    salvar_resultados(_itens, _meta, _saida)
    print(f"{len(_itens)} noticias salvas em {_saida}")
