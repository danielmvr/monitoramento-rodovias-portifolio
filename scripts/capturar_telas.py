"""
Captura as telas do painel para o README (docs/img/).

Uso:
    pip install playwright && python -m playwright install chromium
    python scripts/capturar_telas.py https://USUARIO.github.io/REPOSITORIO/
    python scripts/capturar_telas.py http://localhost:8501/

Tambem roda no GitHub Actions (.github/workflows/capturas.yml).
"""
import os
import sys

from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "docs", "img")


def esperar_texto(pagina, texto, timeout_s=180):
    pagina.get_by_text(texto, exact=False).first.wait_for(timeout=timeout_s * 1000)


def main(url):
    os.makedirs(SAIDA, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(viewport={"width": 1500, "height": 1000})
        pg.goto(url)
        esperar_texto(pg, "MAPA DAS OCORRENCIAS")
        pg.wait_for_timeout(12000)          # mapa e tiles
        pg.screenshot(path=os.path.join(SAIDA, "01_mapa_ocorrencias.png"))

        pg.get_by_role("button", name="Acompanhamento de Atrasos").click()
        esperar_texto(pg, "ACOMPANHAMENTO DE ATRASOS")
        pg.wait_for_timeout(5000)
        pg.screenshot(path=os.path.join(SAIDA, "02_atrasos.png"))
        pg.get_by_text("LOCALIZACAO DOS CARROS ATRASADOS").first.scroll_into_view_if_needed()
        pg.wait_for_timeout(8000)
        pg.screenshot(path=os.path.join(SAIDA, "03_mapa_atrasos.png"))

        pg.get_by_role("button", name="Voltar ao mapa").first.click()
        pg.wait_for_timeout(3000)
        pg.get_by_role("button", name="Abrir tabela de carros").click()
        esperar_texto(pg, "CARROS - GPS")
        pg.wait_for_timeout(3000)
        pg.screenshot(path=os.path.join(SAIDA, "04_carros_gps.png"))
        nav.close()
    print(f"Telas salvas em {SAIDA}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501/")
