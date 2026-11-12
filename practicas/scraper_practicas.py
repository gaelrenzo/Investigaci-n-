#!/usr/bin/env python3
"""
Scraper de prácticas PRE-profesionales (pagadas) con prioridad geográfica:
  1) Puno (Puno, Juliaca y provincias) -> 2) Arequipa -> 3) Zona norte
     (La Libertad, Lambayeque, Piura, Cajamarca, Tumbes, Áncash, Amazonas)

Filtros:
  - Solo PRE-profesionales: descarta "Modalidad: Profesional" y avisos que piden
    egresado/bachiller/titulado sin aceptar estudiantes.
  - Pago: monto en S/ si aparece; "no indica" si solo dice subvención/a convenir.
    --solo-pagadas descarta los ad honorem / sin subvención.
  - Vigentes (cierre >= hoy) y cierre antes de agosto 2027.
  - --carrera "regex" sobre el texto del aviso (sin tildes, minúsculas).

Fuentes (probadas el 2026-11-12):
  practicas.pe (listado regional + páginas por carrera), perutrabajos.com,
  convocatoriasdetrabajo.com, pe.computrabajo.com (necesita sesión + Referer),
  gob.pe/electropuno. Bumeran es una SPA en JS: no se puede leer con requests.

Uso:
  python3 -m venv ~/.venvs/practicas && ~/.venvs/practicas/bin/pip install requests beautifulsoup4
  ~/.venvs/practicas/bin/python scraper_practicas.py \
      --carrera "mecanica electrica|electrica|mecanica|mecatronica|energ" --solo-pagadas
Genera practicas_auto.csv y practicas_auto.md en esta carpeta.
"""
import argparse, csv, datetime as dt, re, sys, time, unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "es-PE,es;q=0.9"}
LIMITE = dt.date(2027, 8, 1)
HOY = dt.date.today()

# región: (prioridad, id de las webs, slug, palabras para confirmar ubicación)
REGIONES = {
    "Puno":        (1, 21, "puno", "puno|juliaca|azangaro|ilave|ananea|moho|ayaviri|huancane|"
                                   "desaguadero|lampa|melgar|sandia|carabaya|yunguyo|chucuito|macusani|san roman"),
    "Arequipa":    (2, 4,  "arequipa", "arequipa|camana|mollendo|islay|caylloma|castilla|uchumayo|"
                                       "cerro verde|chala|majes|la joya"),
    "La Libertad": (3, 13, "la-libertad", "la libertad|trujillo|pataz|chepen|pacasmayo|huamachuco|"
                                          "otuzco|santiago de chuco|viru|ascope"),
    "Lambayeque":  (3, 14, "lambayeque", "lambayeque|chiclayo|ferrenafe"),
    "Piura":       (3, 20, "piura", "piura|sullana|talara|paita|sechura|morropon|ayabaca"),
    "Cajamarca":   (3, 6,  "cajamarca", "cajamarca|jaen|chota|cutervo|celendin|san ignacio"),
    "Tumbes":      (3, 24, "tumbes", "tumbes|zarumilla|contralmirante villar"),
    "Ancash":      (3, 2,  "ancash", "ancash|huaraz|chimbote|casma|huari|antamina|nuevo chimbote"),
    "Amazonas":    (3, 1,  "amazonas", "amazonas|chachapoyas|bagua|utcubamba"),
}
# carreras de practicas.pe: ing. eléctrica 111, mecánica 40, mecatrónica 41
CARRERAS_PPE = [("ingenieria-electrica", 111), ("ingenieria-mecanica", 40), ("mecatronica", 41)]

def fuentes(region):
    _, rid, slug, _ = REGIONES[region]
    up = slug.upper()
    f = [f"https://www.practicas.pe/preprofesionales-en-{slug}-{rid}.html",
         f"https://www.practicas.pe/pre-profesional-region-{slug}-{rid}.html"]
    f += [f"https://www.practicas.pe/profesionales-preprofesionales-{c}-{slug}-{cid}-{rid}.html"
          for c, cid in CARRERAS_PPE]
    f += [f"https://www.practicas.pe/preprofesionales-de-{c}-departamento-{slug}-{cid}-{rid}.html"
          for c, cid in CARRERAS_PPE]
    f += [f"https://www.perutrabajos.com/empleos-practicas-en-{up}-{rid}.html",
          f"https://www.convocatoriasdetrabajo.com/buscar-trabajos-en-{up}-{rid}.html",
          f"https://www.convocatoriasdetrabajo.com/bolsa-empleos-practicas-para-INGENIERIA-ELECTRICA-{up}-111-{rid}.html",
          f"https://www.convocatoriasdetrabajo.com/bolsa-empleos-practicas-para-MECANICA-{up}-40-{rid}.html",
          f"https://pe.computrabajo.com/trabajo-de-practicante-en-{slug}",
          f"https://pe.computrabajo.com/trabajo-de-practicante-de-ingenieria-en-{slug}"]
    if region == "Puno":
        f.append("https://www.gob.pe/institucion/electropuno/informes-publicaciones")
    return f

# Qué enlaces de cada listado son avisos individuales
ENLACES = {
    "www.practicas.pe": re.compile(r"/oferta-[^/]*-\d+\.html$"),
    "www.perutrabajos.com": re.compile(r"/empleos-para-.*practic.*-\d{5,}\.html$"),
    "www.convocatoriasdetrabajo.com": re.compile(r"/oportunidad-laboral-.*practic.*-\d{5,}\.html$"),
    "pe.computrabajo.com": re.compile(r"/ofertas-de-trabajo/oferta-de-trabajo-de-.*(practic|pasant)"),
    "www.gob.pe": re.compile(r"/informes-publicaciones/\d+-.*practic"),
}
# Dónde termina el cuerpo del aviso (para no leer avisos "relacionados" del costado)
FIN_AVISO = re.compile(r"recomendaciones para postular|ofertas similares|convocatorias similares|"
                       r"te puede interesar|otras convocatorias|empleos relacionados|"
                       r"tambien te puede interesar|ultimas convocatorias")

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).lower().strip()

MESES = {m: i + 1 for i, m in enumerate(
    "enero febrero marzo abril mayo junio julio agosto setiembre octubre noviembre diciembre".split())}
MESES.update({"septiembre": 9, "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
              "jul": 7, "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12})
_M = "|".join(sorted(MESES, key=len, reverse=True))
F_NUM = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
F_TXT = re.compile(r"\b(\d{1,2})(?: de)? (" + _M + r")\.?(?: del?)?,? (\d{4})")
# frase de cierre -> fecha (en ventana corta, en cualquiera de los dos órdenes)
CIERRE_ANTES = re.compile(r"(postular hasta|plazo para postular|fechas? para postular|fecha limite|"
                          r"fecha de cierre|cierre de convocatoria|vence|hasta el|finaliza|postulacion hasta)")
CIERRE_DESPUES = re.compile(r"plazo para postular|fecha limite")

MONTO = re.compile(r"(?:s/\.?|s/ ?\.|soles|subvencion[^0-9]{0,40}|remuneracion[^0-9]{0,40}|"
                   r"estipendio[^0-9]{0,30}|propina[^0-9]{0,30})\s*([0-9]{1}[ .,]?[0-9]{3}(?:[.,][0-9]{2})?|[0-9]{3,4}(?:[.,][0-9]{2})?)"
                   r"|([0-9][ .,]?[0-9]{3}(?:[.,][0-9]{2})?) ?soles")
PAGADA_SIN_MONTO = re.compile(r"subvencion|remunerad|remuneracion|estipendio|propina|pagad[ao]s?\b|"
                              r"a convenir|dl 1401|decreto legislativo n?.? ?1401")
NO_PAGADA = re.compile(r"ad honorem|ad-honorem|sin remuneracion|sin subvencion|no remunerad|voluntariado")
MODALIDAD = re.compile(r"modalidad(?: de (?:las )?practicas?)?:? (pre ?-?profe[sc]ional|profe[sc]ional)")
EGRESADO = re.compile(r"\b(egresad[oa]s?|bachiller(es)?|titulad[oa]s?|recien graduad[oa]s?)\b")
ESTUDIANTE = re.compile(r"\bestudiantes?\b|\bciclo\b|\bsemestre\b|cursando|\bano de estudios|"
                        r"\b(ultimo|ultimos) (anos?|ciclos?)|universitari[oa]s? de [ivx0-9]")
CICLO = re.compile(r"[^.;:]{0,40}\b(ciclo|semestre|ano de estudios|anos? de la carrera)[^.;]{0,40}")
ESTUDIOS = re.compile(r"(formacion academica|nivel de estudios|pueden postular|perfil|grado academico|"
                      r"requisitos?(?: del puesto)?)\s*:?\s*(.{10,260}?)(?= requisitos:| funciones| conocimientos|$)")
INICIO = re.compile(r"(fecha de inicio|inicio de (?:las )?practicas|duracion|periodo de practicas|"
                    r"vigencia del convenio)[^.;]{0,70}")
CARRERAS = ["mecanica electrica", "electromecanica", "electrica", "mecanica", "mecatronica",
            "electronica", "energia", "energias renovables", "industrial", "sistemas", "civil",
            "minas", "metalurgica", "quimica", "ambiental", "geologica", "seguridad", "administracion",
            "contabilidad", "economia", "derecho"]

def get(url, ses, ref=None):
    h = dict(UA)
    if ref:
        h["Referer"] = ref
    try:
        r = ses.get(url, headers=h, timeout=30)
        if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
            return r.text, 200
        return None, r.status_code
    except requests.RequestException as e:
        return None, e.__class__.__name__

def a_numero(m):
    """'1,130.00' / '1.130,00' / '1 130' / '1130' -> 1130.0"""
    m = re.sub(r"[.,](\d{2})$", "", m.strip())
    return float(re.sub(r"[ .,]", "", m))

def _fechas(txt):
    out = []
    for d, m, y in F_NUM.findall(txt):
        y = int(y) + (2000 if len(y) == 2 else 0)
        try: out.append(dt.date(y, int(m), int(d)))
        except ValueError: pass
    for d, m, y in F_TXT.findall(txt):
        try: out.append(dt.date(int(y), MESES[m], int(d)))
        except ValueError: pass
    return [f for f in out if dt.date(2025, 1, 1) <= f <= dt.date(2028, 12, 31)]

FUERTE = re.compile(r"(postular hasta el|oferta finalizo el|finaliza el|plazo para postular: hasta el)")

def fecha_cierre(t):
    # 1) frases explícitas de practicas.pe/perutrabajos ("puede postular hasta el 12/11/26")
    for m in FUERTE.finditer(t[:1500]):
        f = _fechas(t[m.end(): m.end() + 30])
        if f:
            return f[0]
    # 2) campo "<fecha> Plazo para postular" de convocatoriasdetrabajo
    for m in CIERRE_DESPUES.finditer(t[:1500]):
        f = _fechas(t[max(0, m.start() - 16): m.start()])
        if f:
            return f[-1]
    cand = []
    for m in CIERRE_ANTES.finditer(t):
        cand += _fechas(t[m.end(): m.end() + 45])
    for m in CIERRE_DESPUES.finditer(t):
        cand += _fechas(t[max(0, m.start() - 16): m.start()])
    return max(cand) if cand else None

def cuerpo(soup, host):
    """Texto normalizado del aviso: desde el H1 hasta el final del cuerpo."""
    for x in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        x.decompose()
    h1 = soup.find("h1")
    titulo = (h1 or soup.title or soup).get_text(" ", strip=True)[:200]
    if host == "www.gob.pe" and soup.title:
        titulo = soup.title.get_text(" ", strip=True).split(" - Informes")[0][:200]
    t = norm(soup.get_text(" ", strip=True))
    i = t.find(norm(titulo)[:40]) if h1 else 0
    t = t[max(i, 0):]
    f = FIN_AVISO.search(t, 1200)
    return titulo, t[: f.start() if f else 9000][:9000]

def entidad_de(titulo, t, host):
    m = re.match(r"(.+?)\s+convocatoria\b", titulo, re.I)          # practicas.pe
    if m and len(m.group(1)) < 70:
        return m.group(1).strip()
    m = re.match(r"convocatoria\s+(.+?)\s+para\b", titulo, re.I)   # convocatoriasdetrabajo
    if m:
        return m.group(1).strip()
    if host == "pe.computrabajo.com":   # "puesto - ciudad [volver al listado] puesto EMPRESA - lugar, región"
        seg = t[: t.find("ya aplicaste")] if "ya aplicaste" in t else t[:400]
        for base in (norm(titulo), norm(titulo).rsplit(" - ", 1)[0]):
            i = seg.rfind(base)
            if i >= 0:
                return seg[i + len(base):].strip(" -").split(" - ")[0].upper()[:60]
    m = re.search(r"\b(practicas|empleos?) [a-z ]*?20\d\d ([a-z ]+?) (ingenieria|derecho|economia)", norm(titulo))
    return m.group(2).upper() if m else ""

def analizar(url, html, region, carrera_re):
    host = urlparse(url).netloc
    soup = BeautifulSoup(html, "html.parser")
    titulo, t = cuerpo(soup, host)
    if not re.search(r"practicant|practicas?\b|pre.?profesional|pasant", t):
        return None, "no es práctica"
    # ¿está en la región?
    _, _, _, lugares = REGIONES[region]
    if not re.search(lugares, t[:4000]) and not re.search(lugares.replace(" ", "-"), url.lower()):
        return None, "otra región"
    # pre vs profesional
    mod = MODALIDAD.search(t)
    # el campo "formación académica / nivel de estudios" manda sobre la etiqueta "modalidad"
    # (practicas.pe pone "preprofesional" a avisos que piden egresado)
    est_m = ESTUDIOS.search(t)
    campo = est_m.group(2) if est_m else ""
    if campo and EGRESADO.search(campo) and not ESTUDIANTE.search(campo):
        return None, "pide egresado/bachiller (formación)"
    egr = bool(EGRESADO.search(t))
    est = bool(ESTUDIANTE.search(t))
    tit = norm(titulo + " " + (soup.title.get_text(" ") if soup.title else ""))
    if re.search(r"practic\w* profesional", tit) and not re.search(r"pre ?-?profesional", tit):
        return None, "profesional (título)"
    if mod and not mod.group(1).startswith("pre"):
        if not (est and re.search(r"pre ?-?profesional", t)):
            return None, "profesional (modalidad)"
    if egr and not est and not (mod and mod.group(1).startswith("pre")):
        return None, "pide egresado/bachiller"
    tipo = "pre" if (mod and mod.group(1).startswith("pre")) or (est and not egr) else "pre/prof"
    if re.search(r"carreras? tecnicas|estudiantes? .{0,40}(instituto|tecnic[oa]s?\b)", t[:4000]):
        tipo += " (técnico)"
    if carrera_re and not carrera_re.search(t):
        return None, "otra carrera"
    # pago
    montos = []
    for a, b in MONTO.findall(t):
        try: montos.append(a_numero(a or b))
        except ValueError: pass
    montos = [m for m in montos if 500 <= m <= 6000]
    if montos:
        pagada, monto = "si", max(montos)
    elif NO_PAGADA.search(t):
        pagada, monto = "no", ""
    elif PAGADA_SIN_MONTO.search(t.replace("no especifica remuneracion", "")):
        pagada, monto = "si (monto no indica)", ""
    else:
        pagada, monto = "no indica", ""
    cierre = fecha_cierre(t)
    if cierre and cierre >= LIMITE:
        return None, "cierra después de ago-2027"
    if re.search(r"\b(concluid[oa]|finalizad[oa]|cerrad[oa]|vencid[oa])\b", t[:600]) or (cierre and cierre < HOY):
        estado = "cerrada"
    else:
        estado = "vigente" if cierre else "sin fecha (verificar)"
    ciclo_m = CICLO.search(t)
    ini_m = INICIO.search(t)
    carreras = [c for c in CARRERAS if re.search(r"\b" + c, t)]
    carreras = [c for c in carreras if not any(c != o and c in o for o in carreras)]
    return {
        "prioridad": REGIONES[region][0], "region": region,
        "entidad": entidad_de(titulo, t, host), "puesto": titulo,
        "tipo": tipo, "carreras": ", ".join(carreras[:6]),
        "ciclo": ciclo_m.group(0).strip()[:90] if ciclo_m else "",
        "estudios": est_m.group(2).strip()[:200] if est_m else "",
        "pagada": pagada, "monto_S/": monto,
        "cierre": cierre.isoformat() if cierre else "", "estado": estado,
        "inicio_duracion": ini_m.group(0).strip()[:90] if ini_m else "",
        "publicado": (re.search(r"hace (mas de )?\d+ (dias?|horas?|minutos?)|publicad[oa] (el )?[0-9/ a-z]{6,20}", t) or [""])[0],
        "url": url,
    }, "ok"

def enlaces_aviso(base, html):
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(base).netloc
    patron = ENLACES.get(host)
    vistos = []
    for a in soup.find_all("a", href=True):
        u = urljoin(base, a["href"]).split("#")[0].split("&")[0]
        if urlparse(u).netloc != host or u == base or u in vistos:
            continue
        if patron and patron.search(u):
            vistos.append(u)
    return vistos

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrera", default="", help="regex, ej. 'mecanica electrica|electrica'")
    ap.add_argument("--solo-pagadas", action="store_true", help="descarta ad honorem / sin subvención")
    ap.add_argument("--incluir-cerradas", action="store_true")
    ap.add_argument("--max-por-fuente", type=int, default=60)
    ap.add_argument("--pausa", type=float, default=0.8, help="segundos entre peticiones")
    ap.add_argument("--regiones", default="", help="ej. 'Puno,Arequipa' (por defecto todas)")
    ap.add_argument("--salida", default="practicas_auto")
    ap.add_argument("-v", "--verbose", action="store_true", help="muestra por qué se descarta cada aviso")
    a = ap.parse_args()
    carrera_re = re.compile(norm(a.carrera)) if a.carrera else None
    regiones = [r.strip() for r in a.regiones.split(",") if r.strip()] or list(REGIONES)

    ses, res, vistos, fallos = requests.Session(), [], set(), []
    for region in regiones:
        print(f"== {region}")
        for fuente in fuentes(region):
            html, st = get(fuente, ses)
            if not html:
                print(f"   ! {fuente} -> {st}")
                fallos.append((region, fuente, st))
                continue
            links = enlaces_aviso(fuente, html)
            # paginación tipo perutrabajos: ?page=2&sort=1-id (hasta 4 páginas)
            paginas = sorted({int(n) for n in re.findall(r"\?page=(\d+)", html) if 1 < int(n) <= 4})
            for n in paginas:
                time.sleep(a.pausa)
                hp, _ = get(f"{fuente}?page={n}&sort=1-id", ses, ref=fuente)
                if hp:
                    links += [u for u in enlaces_aviso(fuente, hp) if u not in links]
            links = links[: a.max_por_fuente]
            print(f"   {fuente} -> {len(links)} avisos")
            if not links:
                fallos.append((region, fuente, "0 avisos"))
            for u in links:
                if u in vistos:
                    continue
                vistos.add(u)
                time.sleep(a.pausa)
                h, st = get(u, ses, ref=fuente)
                if not h:
                    print(f"      ! {u} -> {st}")
                    continue
                r, motivo = analizar(u, h, region, carrera_re)
                if r and a.solo_pagadas and r["pagada"] == "no":
                    r, motivo = None, "no pagada"
                if r and r["estado"] == "cerrada" and not a.incluir_cerradas:
                    r, motivo = None, f"cerrada ({r['cierre']})"
                if a.verbose:
                    print(f"      {motivo:28s} {u}")
                if r:
                    res.append(r)

    # dedup por (entidad, puesto, cierre): el mismo aviso sale en varias webs
    uniq = {}
    for r in res:
        k = (norm(r["entidad"]), norm(r["puesto"])[:60], r["cierre"])
        uniq.setdefault(k, r)
    res = list(uniq.values())
    res.sort(key=lambda r: (r["prioridad"], r["monto_S/"] == "", -(r["monto_S/"] or 0),
                            r["cierre"] or "9999"))
    out = Path(__file__).resolve().parent / a.salida
    campos = list(res[0].keys()) if res else ["region"]
    with open(out.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos); w.writeheader(); w.writerows(res)
    with open(out.with_suffix(".md"), "w", encoding="utf-8") as f:
        f.write(f"# Prácticas pre-profesionales — salida automática ({HOY})\n\n")
        f.write("| Región | Entidad | Puesto | Carreras | Ciclo | Pago S/ | Cierre | Estado |\n"
                "|---|---|---|---|---|---|---|---|\n")
        for r in res:
            f.write(f"| {r['region']} | {r['entidad']} | [{r['puesto'][:70]}]({r['url']}) | "
                    f"{r['carreras']} | {r['ciclo'][:40]} | {r['monto_S/'] or r['pagada']} | "
                    f"{r['cierre']} | {r['estado']} |\n")
        if fallos:
            f.write("\n## Fuentes con error o sin avisos\n")
            for reg, u, st in fallos:
                f.write(f"- {reg}: {u} → {st}\n")
    print(f"\n{len(res)} avisos -> {out}.csv / .md ; fuentes con problema: {len(fallos)}")

if __name__ == "__main__":
    main()
