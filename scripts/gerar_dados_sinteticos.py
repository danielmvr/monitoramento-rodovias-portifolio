"""
Gera TODOS os dados do painel de portfolio, de forma reprodutivel (seed fixa).

Nada aqui e lido de base real: cidades e coordenadas sao publicas, e linhas,
carros, placas, horarios, atrasos, posicoes GPS e noticias sao inventados por
regras simples definidas neste arquivo.

Saidas (pasta data/):
  cidades.json               cidades da malha ficticia
  coords_builtin.json        {CIDADE: [lat, lon, UF]}
  linhas_rotas.json          linhas ficticias com paradas e coordenadas
  atrasos.txt                relatorio de pontualidade (TAB, 19 colunas)
  gps_ultimas_posicoes.csv   ultimas posicoes GPS (layout do exportador)
  noticias.json              noticias ficticias ja processadas pelo pipeline
  meta.json                  horario do snapshot e resumo da geracao

Uso (na raiz do projeto):
    python scripts/gerar_dados_sinteticos.py
"""
import datetime as dt
import json
import math
import os
import random
import sys

SEED = 42
AGORA = dt.datetime(2026, 10, 15, 15, 40, 0)   # "agora" simulado do snapshot
DIA = AGORA.replace(hour=0, minute=0, second=0)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RAIZ, "data")
sys.path.insert(0, RAIZ)

rnd = random.Random(SEED)

# --------------------------------------------------------------------------
# Cidades (coordenadas publicas aproximadas). Codigo de 3 letras ficticio.
# --------------------------------------------------------------------------
CIDADES = {
    "RIO": ("RIO DE JANEIRO", "RJ", -22.9068, -43.1729),
    "PET": ("PETROPOLIS", "RJ", -22.5050, -43.1786),
    "TRR": ("TRES RIOS", "RJ", -22.1165, -43.2085),
    "JDF": ("JUIZ DE FORA", "MG", -21.7642, -43.3496),
    "BAR": ("BARBACENA", "MG", -21.2214, -43.7703),
    "CLF": ("CONSELHEIRO LAFAIETE", "MG", -20.6603, -43.7861),
    "BHZ": ("BELO HORIZONTE", "MG", -19.9167, -43.9345),
    "SET": ("SETE LAGOAS", "MG", -19.4658, -44.2467),
    "CVL": ("CURVELO", "MG", -18.7561, -44.4303),
    "MOC": ("MONTES CLAROS", "MG", -16.7282, -43.8578),
    "VRD": ("VOLTA REDONDA", "RJ", -22.5232, -44.1041),
    "RES": ("RESENDE", "RJ", -22.4686, -44.4509),
    "TAU": ("TAUBATE", "SP", -23.0264, -45.5553),
    "SJC": ("SAO JOSE DOS CAMPOS", "SP", -23.1896, -45.8841),
    "SPO": ("SAO PAULO", "SP", -23.5505, -46.6333),
    "CAM": ("CAMPINAS", "SP", -22.9099, -47.0626),
    "RPO": ("RIBEIRAO PRETO", "SP", -21.1775, -47.8103),
    "UBA": ("UBERABA", "MG", -19.7472, -47.9392),
    "UDI": ("UBERLANDIA", "MG", -18.9186, -48.2772),
    "CAT": ("CATALAO", "GO", -18.1659, -47.9463),
    "BSB": ("BRASILIA", "DF", -15.7939, -47.8828),
    "ANA": ("ANAPOLIS", "GO", -16.3281, -48.9534),
    "GYN": ("GOIANIA", "GO", -16.6869, -49.2648),
    "RVD": ("RIO VERDE", "GO", -17.7923, -50.9192),
    "JTI": ("JATAI", "GO", -17.8784, -51.7204),
    "LAV": ("LAVRAS", "MG", -21.2453, -44.9998),
    "POU": ("POUSO ALEGRE", "MG", -22.2300, -45.9366),
    "SSA": ("SALVADOR", "BA", -12.9777, -38.5016),
    "FSA": ("FEIRA DE SANTANA", "BA", -12.2664, -38.9663),
    "VDC": ("VITORIA DA CONQUISTA", "BA", -14.8615, -40.8442),
    "REG": ("REGISTRO", "SP", -24.4872, -47.8442),
    "CUR": ("CURITIBA", "PR", -25.4284, -49.2733),
    "JOI": ("JOINVILLE", "SC", -26.3045, -48.8487),
    "FLN": ("FLORIANOPOLIS", "SC", -27.5954, -48.5480),
    "RBO": ("RIO BONITO", "RJ", -22.7085, -42.6094),
    "CBF": ("CABO FRIO", "RJ", -22.8894, -42.0286),
    "MAC": ("MACAE", "RJ", -22.3768, -41.7869),
    "CPS": ("CAMPOS DOS GOYTACAZES", "RJ", -21.7545, -41.3244),
}

# Corredores: rodovia (nome igual ao config.yaml) -> cidades em ordem.
CORREDORES = {
    "BR-040": ["RIO", "PET", "TRR", "JDF", "BAR", "CLF", "BHZ"],
    "BR-116 (Via Dutra)": ["RIO", "VRD", "RES", "TAU", "SJC", "SPO"],
    "BR-381 (Fernao Dias)": ["BHZ", "LAV", "POU", "SPO"],
    "BR-135": ["BHZ", "SET", "CVL", "MOC"],
    "BR-050": ["BSB", "CAT", "UDI", "UBA"],
    "Anhanguera (SP-330)": ["SPO", "CAM", "RPO", "UBA"],
    "BR-060": ["BSB", "ANA", "GYN", "RVD", "JTI"],
    "BR-116 (Regis Bittencourt)": ["SPO", "REG", "CUR"],
    "BR-101 (Sul)": ["CUR", "JOI", "FLN"],
    "BR-101 (Norte RJ)": ["RIO", "RBO", "MAC", "CPS"],
    "RJ-124 (Via Lagos)": ["RBO", "CBF"],
    "BR-324": ["SSA", "FSA"],
    "BR-116 (Rio-Bahia)": ["FSA", "VDC"],
}

# Linhas (sentido ida); a volta e gerada invertendo as paradas.
LINHAS_IDA = [
    ["RIO", "PET", "TRR", "JDF"],
    ["RIO", "PET", "JDF", "BAR", "CLF", "BHZ"],
    ["JDF", "BAR", "CLF", "BHZ"],
    ["RIO", "VRD", "RES"],
    ["RIO", "VRD", "RES", "TAU", "SJC", "SPO"],
    ["RIO", "RES", "SPO"],
    ["BHZ", "LAV", "POU", "SPO"],
    ["BHZ", "SET", "CVL", "MOC"],
    ["BSB", "CAT", "UDI", "UBA"],
    ["SPO", "CAM", "RPO"],
    ["SPO", "CAM", "RPO", "UBA", "UDI"],
    ["BSB", "ANA", "GYN"],
    ["GYN", "RVD", "JTI"],
    ["BSB", "ANA", "GYN", "RVD"],
    ["SPO", "REG", "CUR"],
    ["CUR", "JOI", "FLN"],
    ["SPO", "REG", "CUR", "JOI", "FLN"],
    ["RIO", "RBO", "CBF"],
    ["RIO", "RBO", "MAC", "CPS"],
    ["SSA", "FSA", "VDC"],
    ["SSA", "FSA"],
    ["JDF", "TRR", "VRD"],
]

EMPRESAS = {"A": "ALFA", "B": "BETA", "C": "GAMA"}
COLUNAS_ATRASOS = [
    "dtoper", "servico", "codigo_linha", "descricao_linha", "local_comercial",
    "horario_sistema", "horario_comercial", "horario_entrada_comercial_real",
    "horario_partida_comercial_real", "tempo_espera_real", "tempo_atraso",
    "tempo_tolerancia", "matricula", "nomeguerra", "nome", "prefixo_veiculo",
    "placa_veiculo", "frota_veiculo", "nomebase",
]
FMT = "%d/%m/%Y %H:%M:%S"


def dist_km(a, b):
    """Distancia rodoviaria aproximada: haversine x 1,25."""
    la1, lo1 = math.radians(a[2]), math.radians(a[3])
    la2, lo2 = math.radians(b[2]), math.radians(b[3])
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(h)) * 1.25


def cid(cod):
    nome, uf, lat, lon = CIDADES[cod]
    return (nome, uf, lat, lon)


def fmt(t):
    return t.strftime(FMT) if t else ""


def placa():
    letras = "ABCDEFGHJKLMNPRSTUVWXY"
    return f"ZZZ{rnd.randint(0, 9)}{rnd.choice(letras)}{rnd.randint(0, 99):02d}"


# --------------------------------------------------------------------------
# 1) Cidades, coordenadas e linhas
# --------------------------------------------------------------------------
def gerar_malha():
    cidades = sorted(v[0] for v in CIDADES.values())
    coords = {v[0]: [v[2], v[3], v[1]] for v in CIDADES.values()}
    linhas = []
    num = 101
    for paradas in LINHAS_IDA:
        for sentido in (paradas, list(reversed(paradas))):
            codigo = f"L{num:03d}"
            num += 1
            label = f"{sentido[0]}x{sentido[-1]}"
            linhas.append({
                "codigo": codigo,
                "desc": f"{codigo} - {sentido[0]} X {sentido[-1]}",
                "label": label,
                "stops": [[c, cid(c)[0], cid(c)[2], cid(c)[3]] for c in sentido],
            })
    return cidades, coords, linhas


# --------------------------------------------------------------------------
# 2) Viagens do dia: horarios previstos e reais, um carro por viagem
# --------------------------------------------------------------------------
def horarios_previstos(stops, partida):
    """Lista de horarios previstos por parada (70 km/h + 10 min por parada)."""
    t = partida
    out = [t]
    for a, b in zip(stops, stops[1:]):
        km = dist_km((None, None, a[2], a[3]), (None, None, b[2], b[3]))
        t = t + dt.timedelta(minutes=round(km / 70.0 * 60 / 5) * 5 + 10)
        out.append(t)
    return out


def perfil_atraso():
    """Sorteia o perfil da viagem (distribuicao definida a mao)."""
    r = rnd.random()
    if r < 0.80:
        return "normal"
    if r < 0.92:
        return "moderado"
    if r < 0.98:
        return "severo"
    return "anomalia"


def gerar_viagens(linhas):
    """Cada carro faz uma ida e, se couber no dia, a volta da mesma linha."""
    pares = [(linhas[i], linhas[i + 1]) for i in range(0, len(linhas), 2)]
    viagens = []
    carro_n = 0
    servico_n = 30100000
    for ida, volta in pares:
        n_carros = rnd.randint(4, 8)
        for _ in range(n_carros):
            carro_n += 1
            emp = rnd.choice("AAABBC")
            carro = {
                "prefixo": f"{9100 + carro_n * 3}.{emp}",
                "placa": placa(),
                "frota": f"FROTA-{EMPRESAS[emp]}",
                "base": f"BASE {cid(ida['stops'][0][0])[0]} {EMPRESAS[emp]}",
                "empresa": emp,
            }
            partida = DIA + dt.timedelta(minutes=rnd.randrange(4 * 60, 15 * 60, 15))
            for linha in (ida, volta):
                prev = horarios_previstos(linha["stops"], partida)
                servico_n += rnd.randint(7, 97)
                viagens.append({"carro": carro, "linha": linha, "prev": prev,
                                "servico": str(servico_n),
                                "perfil": perfil_atraso()})
                partida = prev[-1] + dt.timedelta(minutes=rnd.randrange(60, 181, 15))
                if partida.date() != DIA.date():
                    break
    return viagens


def reais(viagem):
    """Horarios reais (entrada, partida) por parada, cortados no AGORA."""
    prev = viagem["prev"]
    perfil = viagem["perfil"]
    n = len(prev)
    if perfil == "normal":
        alvo = [rnd.gauss(3, 4) + i * rnd.gauss(1, 2) for i in range(n)]
        alvo = [min(max(a, -5), 14) for a in alvo]
    elif perfil == "moderado":
        fim = rnd.uniform(15, 58)
        alvo = [fim * (i + 1) / n for i in range(n)]
    elif perfil == "severo":
        fim = rnd.uniform(65, 180)
        alvo = [fim * (0.5 + 0.5 * (i + 1) / n) for i in range(n)]
    else:
        alvo = [rnd.gauss(4, 3) for _ in range(n)]

    corte = n
    if perfil == "anomalia":
        # Parou de transmitir apos a 1a parada, ou nunca transmitiu.
        corte = rnd.choice([0, 1])

    saida = []
    for i, t in enumerate(prev):
        if i >= corte:
            saida.append((None, None))
            continue
        partida = t + dt.timedelta(minutes=round(alvo[i]), seconds=rnd.randint(0, 59))
        espera = rnd.randint(5, 40) if i == 0 else rnd.randint(2, 12)
        entrada = partida - dt.timedelta(minutes=espera)
        if entrada > AGORA:
            saida.append((None, None))
            continue
        if i == n - 1:          # destino: so registra a entrada
            partida = None
        elif partida > AGORA:
            partida = None
        saida.append((entrada, partida))
    return saida, alvo


def gerar_atrasos(viagens):
    linhas_txt = ["\t".join(COLUNAS_ATRASOS)]
    estado = {}   # prefixo -> (lat, lon, horario) da ultima transmissao
    for v in viagens:
        c, ln = v["carro"], v["linha"]
        tol = rnd.choice([5, 9, 10])
        rs, alvo = reais(v)
        for i, (stop, t_prev) in enumerate(zip(ln["stops"], v["prev"])):
            entrada, partida = rs[i]
            real = partida or entrada
            atraso = ""
            espera = ""
            if real is not None:
                atraso = str(round((real - t_prev).total_seconds() / 60))
                if entrada and partida:
                    espera = str(round((partida - entrada).total_seconds() / 60))
                ult = estado.get(c["prefixo"])
                if ult is None or real > ult[2]:
                    estado[c["prefixo"]] = (stop[2], stop[3], real, i, v)
            linhas_txt.append("\t".join([
                DIA.strftime(FMT), v["servico"], ln["codigo"], ln["desc"],
                stop[0], fmt(t_prev) if i == 0 else "", fmt(t_prev),
                fmt(entrada), fmt(partida), espera, atraso, str(tol),
                "XXXX", "XXXX", "XXXX",          # colunas pessoais (descartadas)
                c["prefixo"], c["placa"], c["frota"], c["base"],
            ]))
    # Algumas linhas DUPLICADO (o motor descarta).
    for _ in range(6):
        base = rnd.choice(linhas_txt[1:]).split("\t")
        base[17] = "DUPLICADO"
        linhas_txt.append("\t".join(base))
    return linhas_txt, estado


# --------------------------------------------------------------------------
# 3) GPS: ultima posicao de cada carro (interpolada na rota)
# --------------------------------------------------------------------------
def _dec(x, casas):
    """Numero com virgula decimal, como o exportador original."""
    s = f"{x:.{casas}f}"
    inteiro, frac = s.split(".")
    return inteiro, frac


def gerar_gps(viagens, estado):
    linhas = ["Veiculo,Placa,UF,Frota,DataHora,Lat,Lon,Local,Dist,SR,DR,SN,DN"]
    vistos = set()
    for v in viagens:
        c = v["carro"]
        if c["prefixo"] in vistos:
            continue
        vistos.add(c["prefixo"])
        st = estado.get(c["prefixo"])
        if st is None:
            continue          # nunca transmitiu: sem posicao no GPS
        lat, lon, t_real, idx, viagem = st
        stops = viagem["linha"]["stops"]
        prev = viagem["prev"]
        t_gps = t_real
        perfil = viagem["perfil"]
        if idx < len(stops) - 1 and perfil != "anomalia":
            # Em viagem: avanca pela rota ate perto do AGORA.
            t_gps = AGORA - dt.timedelta(minutes=rnd.randint(1, 25))
            prox = stops[idx + 1]
            dur = max((prev[idx + 1] - prev[idx]).total_seconds(), 60)
            frac = min(max((t_gps - t_real).total_seconds() / dur, 0.0), 0.95)
            lat = lat + (prox[2] - lat) * frac + rnd.uniform(-0.02, 0.02)
            lon = lon + (prox[3] - lon) * frac + rnd.uniform(-0.02, 0.02)
        perto = min(stops, key=lambda s: dist_km((0, 0, lat, lon), (0, 0, s[2], s[3])))
        d = dist_km((0, 0, lat, lon), (0, 0, perto[2], perto[3])) / 1.25
        uf = cid(perto[0])[1]
        la_i, la_f = _dec(lat, 5)
        lo_i, lo_f = _dec(lon, 5)
        d_i, d_f = _dec(d, 1)
        linhas.append(",".join([
            f"{c['prefixo']:<9}", c["placa"], uf, c["frota"], fmt(t_gps),
            la_i, la_f, lo_i, lo_f, perto[1], d_i, d_f, "X", "Y", "Z", "W",
        ]))
    # Carros parados na garagem (sem posicao) e de outras frotas: ignorados.
    for k in range(5):
        linhas.append(f"{8000 + k}.X    ,{placa()},,FROTA-APOIO,,,,,,SR,DR,SN,DN")
    return linhas


# --------------------------------------------------------------------------
# 4) Noticias ficticias, processadas pelo mesmo pipeline do projeto
# --------------------------------------------------------------------------
EVENTOS = [
    ("Acidente entre carreta e carro deixa transito lento na {rod}{em}",
     "Uma colisao entre uma carreta e um carro de passeio provocou lentidao na "
     "{rod}{km_txt}. Equipes da concessionaria atuam no local. Nao ha "
     "informacao sobre feridos."),
    ("{rod} tem pista interditada apos tombamento de caminhao{em}",
     "Um caminhao tombou e a pista ficou totalmente interditada{km_txt}. O "
     "desvio e feito pelo acostamento e a previsao de liberacao e de duas horas."),
    ("Queda de barreira bloqueia faixa da {rod}{em}",
     "A chuva forte causou queda de barreira e deslizamento de terra{km_txt}. "
     "Uma faixa segue bloqueada para limpeza da pista."),
    ("Obras de recapeamento causam lentidao na {rod}{em}",
     "Obras de manutencao com pare e siga provocam congestionamento{km_txt}. "
     "Os trabalhos seguem ate o fim da semana, das 8h as 17h."),
    ("Neblina reduz visibilidade e motoristas enfrentam lentidao na {rod}{em}",
     "Neblina intensa e chuva fina exigem atencao{km_txt}. A recomendacao e "
     "manter farois acesos e distancia do veiculo da frente."),
    ("Protesto bloqueia parcialmente a {rod}{em}",
     "Manifestantes fazem protesto e bloqueio parcial{km_txt}. A policia "
     "rodoviaria acompanha a manifestacao e orienta o transito."),
    ("Congestionamento chega a 8 km na {rod}{em} no fim da tarde",
     "O transito intenso provoca congestionamento{km_txt}. O fluxo deve "
     "normalizar a noite, segundo a concessionaria."),
    ("Colisao entre dois carros deixa feridos na {rod}{em}",
     "Um acidente com dois carros deixou feridos{km_txt}. As vitimas foram "
     "levadas a um hospital da regiao e a pista foi parcialmente interditada."),
    ("Alagamento interdita acesso as margens da {rod}{em}",
     "O alagamento apos temporal interditou um acesso{km_txt}. O trafego na "
     "pista principal segue com lentidao."),
]
FONTES = ["Portal Ficticio de Noticias", "Radio Exemplo FM",
          "Jornal Modelo Regional", "TV Demonstracao"]


def gerar_noticias(cfg):
    from monitor.processa import processar_item, linhas_afetadas
    from monitor.geocode import GeoCoder, rep_rodovias

    rod_por_nome = {r["nome"]: r for r in cfg["rodovias"]}
    brutos = []
    vistos = set()
    while len(brutos) < 80:
        rod = rnd.choice(list(CORREDORES))
        cidade = None
        if rnd.random() < 0.7:
            cidade = cid(rnd.choice(CORREDORES[rod]))[0].title()
        km = rnd.randint(5, 650) if rnd.random() < 0.6 else None
        tit, desc = rnd.choice(EVENTOS)
        em = f" em {cidade}" if cidade else ""
        km_txt = f" no km {km}" if km else ""
        rotulo = rod.split(" (")[0] if rnd.random() < 0.5 else rod
        titulo = tit.format(rod=rotulo, em=em)
        if titulo in vistos:
            continue
        vistos.add(titulo)
        horas = rnd.expovariate(1 / 30.0)          # mais recentes sao mais comuns
        publicado = AGORA - dt.timedelta(hours=min(horas, 6 * 24),
                                         minutes=rnd.randint(0, 59))
        brutos.append({
            "titulo": titulo,
            "descricao": desc.format(rod=rotulo, km_txt=km_txt),
            "link": "",
            "fonte": rnd.choice(FONTES),
            "publicado": publicado.replace(second=0, microsecond=0),
            "origem_tipo": "rodovia",
            "origem_nome": rod,
            "origem_meta": rod_por_nome[rod],
        })

    geo = GeoCoder(cfg, usar_nominatim=False)
    rep = rep_rodovias(cfg)
    itens = []
    for b in brutos:
        p = processar_item(b, cfg)
        p.update(geo.localizar(p, rep))
        laf, ltot = linhas_afetadas(p.get("lat"), p.get("lon"),
                                    thresh_km=cfg["app"].get("linhas_raio_km", 40))
        p["linhas"], p["linhas_total"] = laf, ltot
        p["publicado"] = p["publicado"].isoformat()
        itens.append(p)
    itens.sort(key=lambda x: x["publicado"], reverse=True)
    return itens


def salvar_json(nome, obj):
    with open(os.path.join(DATA, nome), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    os.makedirs(DATA, exist_ok=True)
    cidades, coords, linhas = gerar_malha()
    salvar_json("cidades.json", cidades)
    salvar_json("coords_builtin.json", coords)
    salvar_json("linhas_rotas.json", linhas)

    viagens = gerar_viagens(linhas)
    txt, estado = gerar_atrasos(viagens)
    with open(os.path.join(DATA, "atrasos.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(txt) + "\n")
    gps = gerar_gps(viagens, estado)
    with open(os.path.join(DATA, "gps_ultimas_posicoes.csv"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("\n".join(gps) + "\n")

    from monitor.config import load_config
    cfg = load_config()
    noticias = gerar_noticias(cfg)
    salvar_json("noticias.json", {
        "meta": {"atualizado_em": AGORA.isoformat(), "total": len(noticias),
                 "aviso": "Noticias ficticias geradas por script."},
        "itens": noticias,
    })
    salvar_json("meta.json", {
        "agora": AGORA.isoformat(), "seed": SEED,
        "linhas": len(linhas), "viagens": len(viagens),
        "carros": len({v["carro"]["prefixo"] for v in viagens}),
        "registros_atrasos": len(txt) - 1, "noticias": len(noticias),
        "aviso": "Todos os dados sao sinteticos.",
    })
    print(f"OK: {len(linhas)} linhas, {len(viagens)} viagens, "
          f"{len(txt) - 1} registros de atrasos, {len(gps) - 1} posicoes GPS, "
          f"{len(noticias)} noticias.")


if __name__ == "__main__":
    main()
