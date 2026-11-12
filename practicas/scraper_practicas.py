#!/usr/bin/env python3
"""
Scraper de prácticas PRE-profesionales (pagadas) con prioridad geográfica:
  1) Puno (Puno, Juliaca)  ->  2) Arequipa  ->  3) Zona norte
     (La Libertad, Lambayeque, Piura, Cajamarca, Tumbes, Áncash, Amazonas)

Filtros:
  - Solo PRE-profesionales (descarta avisos que piden egresado/bachiller/titulado).
  - Prioriza las pagadas (subvención/remuneración en S/). Con --solo-pagadas descarta el resto.
  - Fecha de cierre (o publicación) anterior a agosto de 2027.
  - Opcional: --carrera "mecanica electrica" para filtrar por carrera.

Uso (en tu PC, con internet):
  pip install requests beautifulsoup4
  python3 scraper_practicas.py --carrera "mecanica electrica|electrica|mecanica|energ" --solo-pagadas
Genera practicas_resultados.csv y practicas_resultados.md en esta carpeta.

Nota: las webs cambian su HTML; el parser es genérico (busca enlaces de avisos
y lee la página de cada aviso), por eso es tolerante a cambios de maquetación.
"""
import argparse, csv, datetime as dt, re, sys, time, unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept-Language": "es-PE,es;q=0.9"}
LIMITE = dt.date(2027, 8, 1)          # prácticas antes de agosto 2027
HOY = dt.date.today()

# Prioridad 1 = Puno, 2 = Arequipa, 3 = norte
REGIONES = {
    "Puno":        (1, 21, "puno"),
    "Arequipa":    (2, 4,  "arequipa"),
    "La Libertad": (3, 13, "la-libertad"),
    "Lambayeque":  (3, 14, "lambayeque"),
    "Piura":       (3, 20, "piura"),
    "Cajamarca":   (3, 6,  "cajamarca"),
    "Tumbes":      (3, 24, "tumbes"),
    "Ancash":      (3, 2,  "ancash"),
    "Amazonas":    (3, 1,  "amazonas"),
}

def fuentes(region):
    _, rid, slug = REGIONES[region]
    return [
        f"https://www.practicas.pe/preprofesionales-en-{slug}-{rid}.html",
        f"https://www.practicas.pe/pre-profesional-region-{slug}-{rid}.html",
        f"https://www.perutrabajos.com/empleos-practicas-en-{slug.upper()}-{rid}.html",
        f"https://www.convocatoriasdetrabajo.com/buscar-empleos-en-{slug.upper()}-{rid}.html",
        f"https://pe.computrabajo.com/trabajo-de-practicante-en-{slug}",
        f"https://pe.computrabajo.com/trabajo-de-practicas-pre-profesionales-en-{slug}",
        f"https://www.bumeran.com.pe/en-{slug}/empleos-busqueda-practicante.html",
    ]

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).lower().strip()

ENLACE_AVISO = re.compile(r"practic|oferta|convocatoria|empleo|trabajo", re.I)
ES_PRACTICA = re.compile(r"practicant|practicas?\b|pre.?profesional", re.I)
SOLO_EGRESADO = re.compile(r"\b(egresad[oa]s?|bachiller(es)?|titulad[oa]s?|practicas? profesionales)\b")
PRE = re.compile(r"pre.?profesional|estudiantes? (de|del|desde|cursando)|ciclo|semestre|\bano\b de estudios")
MONTO = re.compile(r"(?:s/\.?|soles|subvencion[^0-9]{0,40}|remuneracion[^0-9]{0,40}|"
                   r"sueldo[^0-9]{0,40}|propina[^0-9]{0,40})\s*([0-9]{1,2}[.,]?[0-9]{3}(?:[.,][0-9]{2})?)")
MESES = {m: i + 1 for i, m in enumerate(
    "enero febrero marzo abril mayo junio julio agosto setiembre octubre noviembre diciembre".split())}
MESES["septiembre"] = 9
F_NUM = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
F_TXT = re.compile(r"\b(\d{1,2}) de (" + "|".join(MESES) + r")(?: del?)? (\d{4})")
CIERRE = re.compile(r"(finaliza|hasta|cierre|vence|plazo|vigente|postular)")

def get(url, ses):
    try:
        r = ses.get(url, headers=UA, timeout=25)
        if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
            return r.text
    except requests.RequestException as e:
        print(f"   ! {url}: {e.__class__.__name__}", file=sys.stderr)
    return None

def a_numero(m):
    """'1,130.00' / '1.130,00' / '1130' -> 1130.0"""
    m = re.sub(r"[.,](\d{2})$", "", m)
    return float(re.sub(r"[.,]", "", m))

def fechas(txt):
    out = []
    for d, m, y in F_NUM.findall(txt):
        y = int(y) + (2000 if len(y) == 2 else 0)
        try: out.append((dt.date(y, int(m), int(d)), txt))
        except ValueError: pass
    for d, m, y in F_TXT.findall(txt):
        try: out.append((dt.date(int(y), MESES[m], int(d)), txt))
        except ValueError: pass
    return out

def fecha_cierre(t):
    """Busca la fecha que aparece cerca de palabras de cierre; si no, la mayor."""
    cand = []
    for m in CIERRE.finditer(t):
        cand += [f for f, _ in fechas(t[m.start(): m.start() + 80])]
    if not cand:
        cand = [f for f, _ in fechas(t)]
    cand = [f for f in cand if dt.date(2025, 1, 1) <= f <= dt.date(2028, 12, 31)]
    return max(cand) if cand else None

def analizar(url, html, region, carrera_re):
    soup = BeautifulSoup(html, "html.parser")
    for x in soup(["script", "style", "nav", "footer", "header"]):
        x.decompose()
    titulo = (soup.find("h1") or soup.title or soup).get_text(" ", strip=True)[:160]
    texto = soup.get_text(" ", strip=True)
    t = norm(texto)[:15000]
    if not ES_PRACTICA.search(t):
        return None
    pre = bool(PRE.search(t))
    solo_egr = bool(SOLO_EGRESADO.search(t)) and not pre
    if solo_egr:
        return None                      # prácticas profesionales -> fuera
    if carrera_re and not carrera_re.search(t):
        return None
    montos = [a_numero(m) for m in MONTO.findall(t)]
    montos = [m for m in montos if 500 <= m <= 6000]
    cierre = fecha_cierre(t)
    if cierre and cierre >= LIMITE:
        return None
    if "concluid" in t[:3000] or (cierre and cierre < HOY):
        estado = "cerrada"
    else:
        estado = "vigente" if cierre else "sin fecha (verificar)"
    return {
        "prioridad": REGIONES[region][0], "region": region, "titulo": titulo,
        "pagada": "si" if montos else "no indica",
        "monto_S/": max(montos) if montos else "",
        "cierre": cierre.isoformat() if cierre else "", "estado": estado,
        "url": url,
    }

def enlaces_aviso(base, html):
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(base).netloc
    vistos = set()
    for a in soup.find_all("a", href=True):
        u = urljoin(base, a["href"]).split("#")[0]
        txt = norm(a.get_text(" "))
        if urlparse(u).netloc != host or u == base or u in vistos:
            continue
        if ENLACE_AVISO.search(u) and (ES_PRACTICA.search(txt) or ES_PRACTICA.search(norm(u))):
            # descartar páginas de listado/paginación
            if re.search(r"(region|departamento|buscar|busqueda|-en-[a-z-]+-\d+\.html$)", u):
                continue
            vistos.add(u)
            yield u

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrera", default="", help="regex sobre el texto, ej. 'mecanica electrica|electrica'")
    ap.add_argument("--solo-pagadas", action="store_true")
    ap.add_argument("--incluir-cerradas", action="store_true")
    ap.add_argument("--max-por-fuente", type=int, default=40)
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre peticiones")
    a = ap.parse_args()
    carrera_re = re.compile(norm(a.carrera)) if a.carrera else None

    ses, res, vistos = requests.Session(), [], set()
    for region in REGIONES:
        print(f"== {region}")
        for fuente in fuentes(region):
            html = get(fuente, ses)
            if not html:
                continue
            links = list(enlaces_aviso(fuente, html))[: a.max_por_fuente]
            print(f"   {fuente} -> {len(links)} avisos")
            for u in links:
                if u in vistos:
                    continue
                vistos.add(u)
                time.sleep(a.pausa)
                h = get(u, ses)
                r = h and analizar(u, h, region, carrera_re)
                if not r:
                    continue
                if a.solo_pagadas and r["pagada"] != "si":
                    continue
                if r["estado"] == "cerrada" and not a.incluir_cerradas:
                    continue
                res.append(r)
        # Si ya hay vigentes en Puno, Arequipa sigue siendo útil como respaldo,
        # pero el orden final respeta la prioridad Puno > Arequipa > Norte.

    res.sort(key=lambda r: (r["prioridad"], r["pagada"] != "si",
                            -(r["monto_S/"] or 0), r["cierre"] or "9999"))
    out = Path(__file__).with_name("practicas_resultados")
    campos = ["prioridad", "region", "titulo", "pagada", "monto_S/", "cierre", "estado", "url"]
    with open(out.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos); w.writeheader(); w.writerows(res)
    with open(out.with_suffix(".md"), "w", encoding="utf-8") as f:
        f.write(f"# Prácticas pre-profesionales (generado {HOY})\n\n")
        f.write("| Región | Aviso | Pagada | S/ | Cierre | Estado |\n|---|---|---|---|---|---|\n")
        for r in res:
            f.write(f"| {r['region']} | [{r['titulo'][:80]}]({r['url']}) | {r['pagada']} | "
                    f"{r['monto_S/']} | {r['cierre']} | {r['estado']} |\n")
    print(f"\n{len(res)} avisos -> {out}.csv / .md")

if __name__ == "__main__":
    main()
