"""Genera los dos PDF (artículo científico e informe de investigación) a partir
de los resultados en analisis/resultados_python.json y las figuras en figuras/.

Uso (desde la raíz del repositorio):
    python3 analisis/analisis_msr.py
    python3 documentos/construir_pdfs.py
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "documentos"
OUT = ROOT / "pdf"
OUT.mkdir(exist_ok=True)
R = json.loads((ROOT / "analisis/resultados_python.json").read_text())


def f(x, d=2):
    return f"{x:.{d}f}".replace("-", "−")


def s(x, d=4):  # con signo
    return ("+ " if x >= 0 else "− ") + f"{abs(x):.{d}f}"


def pv(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


b0, b1, b2, b11, b22, b12 = R["coef"]
c1, h1, c2, h2 = R["c1"], R["h1"], R["c2"], R["h2"]
# Ecuación en variables reales
aWW = b11 / h1**2
aEE = b22 / h2**2
aWE = b12 / (h1 * h2)
aW = b1 / h1 - 2 * b11 * c1 / h1**2 - b12 * c2 / (h1 * h2)
aE = b2 / h2 - 2 * b22 * c2 / h2**2 - b12 * c1 / (h1 * h2)
a0 = b0 - b1 * c1 / h1 - b2 * c2 / h2 + b11 * c1**2 / h1**2 + b22 * c2**2 / h2**2 + b12 * c1 * c2 / (h1 * h2)

D = R["desc"]
BH = R["by_horario"]
lam1, lam2 = R["lam"]

AUT1 = "Renzo Gabriel Mamani Galindo"
AUT2 = "Aquiles Taylor Ramos Yapo"
DOC_ = "Mateo Alejandro Salinas Mena"
EMAIL = "renzomamanigalindo@gmail.com"

TIT_ES = ("Modelado de la temperatura operativa interior de un sistema de calefacción por piso radiante "
          "mediante metodología de superficie de respuesta")
TIT_EN = ("Modelling indoor operative temperature of a radiant floor heating system "
          "using response surface methodology")

# ------------------------------------------------------------------ bloques comunes
EQ_MODEL = (f"<i>ŷ</i> = {f(b0,4)} {s(b1)}<i>x</i><sub>1</sub> {s(b2)}<i>x</i><sub>2</sub> "
            f"{s(b11)}<i>x</i><sub>1</sub><sup>2</sup> {s(b22)}<i>x</i><sub>2</sub><sup>2</sup> "
            f"{s(b12)}<i>x</i><sub>1</sub><i>x</i><sub>2</sub>")
EQ_REAL = (f"<i>T</i><sub>op</sub> = {f(a0,3)} {s(aW,4)}<i>T</i><sub>w</sub> {s(aE,4)}<i>T</i><sub>e</sub> "
           f"{s(aWW,5)}<i>T</i><sub>w</sub><sup>2</sup> {s(aEE,5)}<i>T</i><sub>e</sub><sup>2</sup> "
           f"{s(aWE,5)}<i>T</i><sub>w</sub><i>T</i><sub>e</sub>")

names = ["<i>β</i><sub>0</sub> (intercepto)", "<i>β</i><sub>1</sub> (<i>x</i><sub>1</sub>)",
         "<i>β</i><sub>2</sub> (<i>x</i><sub>2</sub>)", "<i>β</i><sub>11</sub> (<i>x</i><sub>1</sub><sup>2</sup>)",
         "<i>β</i><sub>22</sub> (<i>x</i><sub>2</sub><sup>2</sup>)", "<i>β</i><sub>12</sub> (<i>x</i><sub>1</sub><i>x</i><sub>2</sub>)"]
rows = "".join(
    f"<tr><td class='l'>{n}</td><td>{f(c,4)}</td><td>{f(e,4)}</td><td>{f(t,2)}</td><td>{pv(p)}</td>"
    f"<td>{'Sí' if p < 0.05 else 'No'}</td></tr>"
    for n, c, e, t, p in zip(names, R["coef"], R["se"], R["t"], R["pt"]))
TAB_COEF = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Coeficientes estimados del modelo de segundo orden (variables codificadas).</p>
<table><thead><tr><th class='l'>Término</th><th>Coeficiente</th><th>Error est.</th><th><i>t</i></th><th>Valor <i>p</i></th><th>Signif. (α = 0.05)</th></tr></thead>
<tbody>{rows}</tbody></table><p class="note">gl del error = {R['n']-6}. Estimación por mínimos cuadrados ordinarios.</p></div>"""

TAB_ANOVA = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Análisis de varianza (ANOVA) de la regresión.</p>
<table><thead><tr><th class='l'>Fuente</th><th>gl</th><th>SC</th><th>CM</th><th><i>F</i><sub>0</sub></th><th>Valor <i>p</i></th></tr></thead>
<tbody>
<tr><td class='l'>Regresión</td><td>5</td><td>{f(R['SSR'],3)}</td><td>{f(R['SSR']/5,3)}</td><td>{f(R['F'],2)}</td><td>{pv(R['pF'])}</td></tr>
<tr><td class='l'>&nbsp;&nbsp;Lineal (<i>x</i><sub>1</sub>, <i>x</i><sub>2</sub>)</td><td>2</td><td>{f(R['SST']*R['R2_lin'],3)}</td><td>{f(R['SST']*R['R2_lin']/2,3)}</td><td>{f(R['SST']*R['R2_lin']/2/R['MSE'],2)}</td><td>&lt; 0.001</td></tr>
<tr><td class='l'>&nbsp;&nbsp;Cuadrático + interacción</td><td>3</td><td>{f(R['SSR']-R['SST']*R['R2_lin'],3)}</td><td>{f((R['SSR']-R['SST']*R['R2_lin'])/3,3)}</td><td>{f(R['F_2o'],2)}</td><td>{pv(R['p_2o'])}</td></tr>
<tr><td class='l'>Error residual</td><td>{R['n']-6}</td><td>{f(R['SSE'],3)}</td><td>{f(R['MSE'],3)}</td><td></td><td></td></tr>
<tr><td class='l'>Total</td><td>{R['n']-1}</td><td>{f(R['SST'],3)}</td><td></td><td></td><td></td></tr>
</tbody></table>
<p class="note"><i>R</i><sup>2</sup> = {f(R['R2'],4)}; <i>R</i><sup>2</sup><sub>aj</sub> = {f(R['R2a'],4)}; <i>R</i><sup>2</sup><sub>pred</sub> (PRESS) = {f(R['R2pred'],4)}; RMSE = {f(R['RMSE'],3)} °C; MAE = {f(R['MAE'],3)} °C.</p></div>"""

TAB_DESC = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Estadística descriptiva de las variables (n = {R['n']}).</p>
<table><thead><tr><th class='l'>Variable</th><th>Media</th><th>DE</th><th>Mín.</th><th>Q1</th><th>Mediana</th><th>Q3</th><th>Máx.</th></tr></thead><tbody>
""" + "".join(
    f"<tr><td class='l'>{lab}</td><td>{f(D[k]['mean'])}</td><td>{f(D[k]['std'])}</td><td>{f(D[k]['min'],1)}</td>"
    f"<td>{f(D[k]['25%'],1)}</td><td>{f(D[k]['50%'],1)}</td><td>{f(D[k]['75%'],1)}</td><td>{f(D[k]['max'],1)}</td></tr>"
    for k, lab in [("Tw", "<i>T</i><sub>w</sub>, entrada de agua (°C)"), ("Te", "<i>T</i><sub>e</sub>, aire exterior (°C)"),
                   ("To", "<i>T</i><sub>op</sub>, operativa interior (°C)")]) + """</tbody></table></div>"""

TAB_HOR = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Media ± desviación estándar por franja horaria de medición.</p>
<table><thead><tr><th class='l'>Franja</th><th>Horario</th><th>n</th><th><i>T</i><sub>w</sub> (°C)</th><th><i>T</i><sub>e</sub> (°C)</th><th><i>T</i><sub>op</sub> (°C)</th></tr></thead><tbody>
""" + "".join(
    f"<tr><td class='l'>{h}</td><td>{hr}</td><td>{R['counts'][f'1-{h}'] + R['counts'][f'2-{h}']}</td>"
    f"<td>{f(BH[h]['Tw_mean'])} ± {f(BH[h]['Tw_std'])}</td><td>{f(BH[h]['Te_mean'])} ± {f(BH[h]['Te_std'])}</td>"
    f"<td>{f(BH[h]['To_mean'])} ± {f(BH[h]['To_std'])}</td></tr>"
    for h, hr in [("Mañana", "05:00–07:00"), ("Tarde", "12:30–14:30"), ("Noche", "20:00–22:00")]) + "</tbody></table></div>"

TAB_COD = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Factores, niveles observados y codificación.</p>
<table><thead><tr><th>Factor</th><th class='l'>Variable real</th><th>Mín. (−1)</th><th>Centro (0)</th><th>Máx. (+1)</th><th class='l'>Codificación</th></tr></thead><tbody>
<tr><td><i>x</i><sub>1</sub></td><td class='l'>Temperatura de entrada del agua, <i>T</i><sub>w</sub> (°C)</td><td>11.9</td><td>{f(c1)}</td><td>48.1</td><td class='l'><i>x</i><sub>1</sub> = (<i>T</i><sub>w</sub> − {f(c1,1)})/{f(h1,1)}</td></tr>
<tr><td><i>x</i><sub>2</sub></td><td class='l'>Temperatura del aire exterior, <i>T</i><sub>e</sub> (°C)</td><td>−5.3</td><td>{f(c2)}</td><td>15.3</td><td class='l'><i>x</i><sub>2</sub> = (<i>T</i><sub>e</sub> − {f(c2,1)})/{f(h2,1)}</td></tr>
<tr><td><i>y</i></td><td class='l'>Temperatura operativa interior, <i>T</i><sub>op</sub> (°C)</td><td colspan="3">5.7 – 20.2 (respuesta)</td><td class='l'>—</td></tr>
</tbody></table></div>"""

TAB_CANON = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Resultados del análisis canónico y de la búsqueda del óptimo.</p>
<table><thead><tr><th class='l'>Indicador</th><th>Codificado</th><th>Real</th></tr></thead><tbody>
<tr><td class='l'>Punto estacionario <i>x</i><sub>1,s</sub> (<i>T</i><sub>w</sub>)</td><td>{f(R['xs'][0],3)}</td><td>{f(R['T1s'],1)} °C</td></tr>
<tr><td class='l'>Punto estacionario <i>x</i><sub>2,s</sub> (<i>T</i><sub>e</sub>)</td><td>{f(R['xs'][1],3)}</td><td>{f(R['T2s'],2)} °C</td></tr>
<tr><td class='l'>Respuesta estimada en el punto estacionario <i>ŷ</i><sub>s</sub></td><td colspan="2">{f(R['ys'],2)} °C</td></tr>
<tr><td class='l'>Valores propios de <b>B</b> (<i>λ</i><sub>1</sub>, <i>λ</i><sub>2</sub>)</td><td colspan="2">{f(lam1,4)}; {f(lam2,4)} → punto silla</td></tr>
<tr><td class='l'>Mejor condición en la región (−1 ≤ <i>x<sub>i</sub></i> ≤ 1)</td><td>(1.00; 1.00)</td><td><i>T</i><sub>w</sub> = {f(R['T1m'],1)} °C; <i>T</i><sub>e</sub> = {f(R['T2m'],1)} °C</td></tr>
<tr><td class='l'>Respuesta máxima estimada en la región</td><td colspan="2">{f(R['ymax'],2)} °C</td></tr>
</tbody></table></div>"""

TAB_DIAG = f"""<div class="tbl"><p class="cap"><b>Tabla {{n}}.</b> Diagnóstico de supuestos del modelo.</p>
<table><thead><tr><th class='l'>Supuesto / prueba</th><th>Estadístico</th><th class='l'>Interpretación</th></tr></thead><tbody>
<tr><td class='l'>Colinealidad (<i>r</i> entre <i>T</i><sub>w</sub> y <i>T</i><sub>e</sub>; VIF)</td><td>{f(R['r12'],3)}; {f(R['VIF'],3)}</td><td class='l'>Factores prácticamente ortogonales</td></tr>
<tr><td class='l'>Normalidad: Kolmogórov–Smirnov</td><td>D = {f(R['KS'],3)}; <i>p</i> = {f(R['KS_p'],3)}</td><td class='l'>No se rechaza normalidad</td></tr>
<tr><td class='l'>Normalidad: Anderson–Darling</td><td>A² = {f(R['AD'],3)} (crít. 5 %: {f(R['AD_crit5'],3)})</td><td class='l'>Desviación leve en colas</td></tr>
<tr><td class='l'>Asimetría; curtosis en exceso</td><td>{f(R['skew'],3)}; {f(R['kurt'],3)}</td><td class='l'>Cercanas a la normal</td></tr>
<tr><td class='l'>Independencia: Durbin–Watson</td><td>DW = {f(R['DW'],3)}</td><td class='l'>Autocorrelación positiva (serie temporal)</td></tr>
<tr><td class='l'>Capacidad predictiva (PRESS)</td><td><i>R</i><sup>2</sup><sub>pred</sub> = {f(R['R2pred'],4)}</td><td class='l'>Sin sobreajuste (≈ <i>R</i><sup>2</sup><sub>aj</sub>)</td></tr>
</tbody></table></div>"""


def fig(src, n, cap, width="100%"):
    return (f'<figure><img src="../figuras/{src}" style="width:{width}"><p class="cap"><b>Figura {n}.</b> {cap}</p></figure>')


REFS = [
    "American Society of Heating, Refrigerating and Air-Conditioning Engineers. (2020). <i>ANSI/ASHRAE Standard 55-2020: Thermal environmental conditions for human occupancy</i>. ASHRAE.",
    "Anderson, T. W., &amp; Darling, D. A. (1954). A test of goodness of fit. <i>Journal of the American Statistical Association, 49</i>(268), 765–769.",
    "Babiak, J., Olesen, B. W., &amp; Petráš, D. (2007). <i>Low temperature heating and high temperature cooling</i> (REHVA Guidebook No. 7). REHVA.",
    "Bezerra, M. A., Santelli, R. E., Oliveira, E. P., Villar, L. S., &amp; Escaleira, L. A. (2008). Response surface methodology (RSM) as a tool for optimization in analytical chemistry. <i>Talanta, 76</i>(5), 965–977.",
    "Box, G. E. P., &amp; Wilson, K. B. (1951). On the experimental attainment of optimum conditions. <i>Journal of the Royal Statistical Society: Series B, 13</i>(1), 1–45.",
    "Durbin, J., &amp; Watson, G. S. (1950). Testing for serial correlation in least squares regression: I. <i>Biometrika, 37</i>(3–4), 409–428.",
    "Eaton, J. W., Bateman, D., Hauberg, S., &amp; Wehbring, R. (2020). <i>GNU Octave version 6.1.0 manual: A high-level interactive language for numerical computations</i>.",
    "Fanger, P. O. (1970). <i>Thermal comfort: Analysis and applications in environmental engineering</i>. Danish Technical Press.",
    "International Organization for Standardization. (1998). <i>ISO 7726:1998 Ergonomics of the thermal environment — Instruments for measuring physical quantities</i>. ISO.",
    "International Organization for Standardization. (2005). <i>ISO 7730:2005 Ergonomics of the thermal environment — Analytical determination and interpretation of thermal comfort using calculation of the PMV and PPD indices and local thermal comfort criteria</i>. ISO.",
    "International Organization for Standardization. (2021). <i>ISO 11855-1:2021 Building environment design — Embedded radiant heating and cooling systems — Part 1: Definitions, symbols, and comfort criteria</i>. ISO.",
    "Montgomery, D. C. (2017). <i>Design and analysis of experiments</i> (9th ed.). John Wiley &amp; Sons.",
    "Myers, R. H., Montgomery, D. C., &amp; Anderson-Cook, C. M. (2016). <i>Response surface methodology: Process and product optimization using designed experiments</i> (4th ed.). John Wiley &amp; Sons.",
    "Olesen, B. W. (2002). Radiant floor heating in theory and practice. <i>ASHRAE Journal, 44</i>(7).",
    "Rhee, K.-N., &amp; Kim, K. W. (2015). A 50 year review of basic and applied research in radiant heating and cooling systems for the built environment. <i>Building and Environment, 91</i>, 166–190.",
]
REFS_HTML = "".join(f"<p>{r}</p>" for r in REFS)

# ------------------------------------------------------------------ textos núcleo
RESUMEN = f"""Los sistemas de calefacción por piso radiante son una alternativa eficiente para climatizar viviendas en zonas
de clima frío, pero su desempeño depende de la temperatura del agua de impulsión y de las condiciones exteriores. Este estudio
modeló la temperatura operativa interior (<i>T</i><sub>op</sub>) de un ambiente calefaccionado por piso radiante en función de la
temperatura de entrada del agua (<i>T</i><sub>w</sub>) y de la temperatura del aire exterior (<i>T</i><sub>e</sub>) mediante la
metodología de superficie de respuesta (MSR). Se registraron {R['n']} observaciones con el sistema en funcionamiento durante dos
semanas (11 al 25 de septiembre de 2026) en tres franjas diarias, con termómetro de globo y sensores de temperatura. Se ajustó un
modelo polinomial de segundo orden en variables codificadas por mínimos cuadrados, se evaluó con ANOVA y se realizó el análisis
canónico. El modelo explicó el {f(R['R2']*100,1)} % de la variabilidad (<i>F</i> = {f(R['F'],1)}; <i>p</i> &lt; 0.001; RMSE =
{f(R['RMSE'],2)} °C; <i>R</i><sup>2</sup><sub>pred</sub> = {f(R['R2pred'],3)}). Ambos efectos lineales, el término cuadrático de
<i>T</i><sub>e</sub> y la interacción fueron significativos; la curvatura en <i>T</i><sub>w</sub> no lo fue (<i>p</i> = {f(R['pt'][3],3)}).
La temperatura exterior fue el factor dominante (<i>β</i><sub>2</sub> = {f(b2,2)}) frente a la del agua (<i>β</i><sub>1</sub> = {f(b1,2)}),
y la interacción negativa indica que el agua caliente es más eficaz en condiciones más frías. El punto estacionario resultó un punto
silla fuera de la región experimental, por lo que la mejor condición se ubica en la frontera: <i>T</i><sub>w</sub> = {f(R['T1m'],1)} °C y
<i>T</i><sub>e</sub> = {f(R['T2m'],1)} °C, con <i>T</i><sub>op</sub> estimada de {f(R['ymax'],1)} °C, todavía por debajo del umbral
invernal de confort de 20 °C. Se concluye que el sistema, en su configuración actual, requiere mayor aporte térmico o mejoras en
la envolvente para alcanzar condiciones de confort."""

ABSTRACT = f"""Radiant floor heating systems are an efficient option for space heating in cold climates, but their performance depends on
supply water temperature and outdoor conditions. This study modelled the indoor operative temperature (<i>T</i><sub>op</sub>) of a room heated
by a radiant floor as a function of the supply water temperature (<i>T</i><sub>w</sub>) and the outdoor air temperature (<i>T</i><sub>e</sub>)
using response surface methodology (RSM). A total of {R['n']} observations were recorded with the system in operation over two weeks
(11–25 September 2026) in three daily time windows using a globe thermometer and temperature sensors. A second-order polynomial model in
coded variables was fitted by least squares, assessed through ANOVA and analysed canonically. The model explained {f(R['R2']*100,1)} % of the
variance (<i>F</i> = {f(R['F'],1)}; <i>p</i> &lt; 0.001; RMSE = {f(R['RMSE'],2)} °C; predicted <i>R</i><sup>2</sup> = {f(R['R2pred'],3)}). Both linear
effects, the quadratic term of <i>T</i><sub>e</sub> and the interaction were significant, whereas curvature in <i>T</i><sub>w</sub> was not
(<i>p</i> = {f(R['pt'][3],3)}). Outdoor temperature was the dominant factor (<i>β</i><sub>2</sub> = {f(b2,2)}) compared with water temperature
(<i>β</i><sub>1</sub> = {f(b1,2)}), and the negative interaction shows that hot water is more effective under colder conditions. The stationary
point was a saddle point outside the experimental region; hence the best condition lies on the boundary (<i>T</i><sub>w</sub> = {f(R['T1m'],1)} °C,
<i>T</i><sub>e</sub> = {f(R['T2m'],1)} °C), giving an estimated <i>T</i><sub>op</sub> of {f(R['ymax'],1)} °C, still below the 20 °C winter comfort
threshold. The system, as currently configured, requires greater heat input or envelope improvements to achieve thermal comfort."""

KW_ES = "piso radiante; temperatura operativa; metodología de superficie de respuesta; confort térmico; calefacción hidrónica; análisis canónico"
KW_EN = "radiant floor heating; operative temperature; response surface methodology; thermal comfort; hydronic heating; canonical analysis"

INTRO = """<p>La calefacción de espacios en zonas de clima frío representa una fracción importante del consumo energético de las
edificaciones y condiciona directamente la salud y el bienestar de sus ocupantes. Entre las tecnologías disponibles, los sistemas
hidrónicos de piso radiante destacan por distribuir el calor de forma uniforme, operar con temperaturas de agua moderadas y
favorecer el intercambio radiante con los ocupantes, lo que permite alcanzar sensaciones de confort con temperaturas de aire
menores que los sistemas convectivos (Olesen, 2002; Babiak et al., 2007). Una revisión de cinco décadas de investigación confirma
su potencial de ahorro energético y su compatibilidad con fuentes de baja temperatura (Rhee &amp; Kim, 2015).</p>
<p>El desempeño de estos sistemas suele evaluarse mediante la temperatura operativa (<i>T</i><sub>op</sub>), magnitud que combina la
temperatura del aire y la temperatura radiante media y que constituye la base de los criterios de confort de ISO 7730 (2005) y
ASHRAE 55 (2020), derivados del modelo de Fanger (1970). Las normas de diseño de sistemas radiantes embebidos, como ISO 11855-1
(2021), establecen además límites para la temperatura superficial del piso que restringen la temperatura de impulsión del agua.</p>
<p>En la práctica, la <i>T</i><sub>op</sub> alcanzada depende simultáneamente de variables controlables, como la temperatura de entrada
del agua (<i>T</i><sub>w</sub>), y de variables no controlables, como la temperatura del aire exterior (<i>T</i><sub>e</sub>), cuyas
relaciones pueden ser no lineales y presentar interacción. La metodología de superficie de respuesta (MSR), introducida por Box y
Wilson (1951) y sistematizada por Myers et al. (2016) y Montgomery (2017), permite aproximar estas relaciones mediante polinomios de
segundo orden, identificar puntos estacionarios y caracterizar la región de operación favorable; su aplicación se ha extendido a la
optimización de procesos en múltiples disciplinas (Bezerra et al., 2008).</p>
<p>Pese a ello, son escasos los estudios que aplican la MSR a datos de campo de sistemas de piso radiante operando en condiciones
reales de clima frío, con amplias oscilaciones térmicas diarias. El objetivo de esta investigación fue modelar la temperatura
operativa interior de un ambiente calefaccionado por piso radiante en función de la temperatura de entrada del agua y de la
temperatura exterior mediante la MSR, determinar la naturaleza del punto estacionario y estimar la mejor condición de operación
dentro de la región observada.</p>"""

METODOS_SISTEMA = f"""<p>El estudio se realizó en un ambiente experimental equipado con un sistema hidrónico de calefacción por piso radiante, compuesto por
una caldera de agua caliente, un circuito de tuberías embebido en la losa y puntos de medición de temperatura en la entrada y la
salida del circuito. Las mediciones se efectuaron durante dos semanas consecutivas (del 11 al 25 de septiembre de 2026) en tres
franjas diarias: mañana (05:00–07:00 h), tarde (12:30–14:30 h) y noche (20:00–22:00 h), con registros a intervalos de 5 min.</p>
<p>En el interior se empleó un termohigrómetro con termómetro de globo, conforme a los principios de ISO 7726 (1998), que registró la
temperatura del aire, la temperatura radiante, la temperatura operativa y la humedad relativa; además, se midió la velocidad del aire
con anemómetro y la temperatura superficial del piso en tres puntos (centro, extremo y puerta). En el exterior se registraron la
temperatura del aire, la temperatura radiante y la humedad relativa con un segundo termohigrómetro de globo. Dado que la velocidad del
aire interior fue nula en todos los registros (&lt; 0.2 m/s), la temperatura operativa se calculó como la media aritmética de la
temperatura del aire y la temperatura radiante media (ISO 7730, 2005).</p>"""

METODOS_MSR = f"""<p>Se seleccionaron dos factores: <i>T</i><sub>w</sub> (factor controlable) y <i>T</i><sub>e</sub> (factor ambiental), y como respuesta la
<i>T</i><sub>op</sub> interior. Se conservaron únicamente los registros con el sistema en funcionamiento (con temperatura de agua
registrada), lo que dio una muestra de n = {R['n']} observaciones. Los factores se codificaron en el intervalo [−1, 1] mediante</p>
<div class="eq"><span><i>x<sub>i</sub></i> = (<i>T<sub>i</sub></i> − <i>T<sub>i</sub></i><sup>c</sup>) / (Δ<i>T<sub>i</sub></i>/2)</span><span class="num">(1)</span></div>
<p>donde <i>T<sub>i</sub></i><sup>c</sup> es el centro del rango observado y Δ<i>T<sub>i</sub></i>/2 su semirrango ({{TCOD}}). Se ajustó el modelo de segundo orden</p>
<div class="eq"><span><i>y</i> = <i>β</i><sub>0</sub> + <i>β</i><sub>1</sub><i>x</i><sub>1</sub> + <i>β</i><sub>2</sub><i>x</i><sub>2</sub> + <i>β</i><sub>11</sub><i>x</i><sub>1</sub><sup>2</sup> + <i>β</i><sub>22</sub><i>x</i><sub>2</sub><sup>2</sup> + <i>β</i><sub>12</sub><i>x</i><sub>1</sub><i>x</i><sub>2</sub> + <i>ε</i></span><span class="num">(2)</span></div>
<p>por mínimos cuadrados ordinarios, <b>β̂</b> = (<b>X</b>′<b>X</b>)<sup>−1</sup><b>X</b>′<b>y</b>, con <b>X</b> = [1, <i>x</i><sub>1</sub>, <i>x</i><sub>2</sub>,
<i>x</i><sub>1</sub><sup>2</sup>, <i>x</i><sub>2</sub><sup>2</sup>, <i>x</i><sub>1</sub><i>x</i><sub>2</sub>]. La significancia global se evaluó con ANOVA
(prueba <i>F</i>) y la de cada coeficiente con la prueba <i>t</i> (α = 0.05). Para el análisis canónico, el modelo se expresó en forma matricial</p>
<div class="eq"><span><i>ŷ</i> = <i>β̂</i><sub>0</sub> + <b>x</b>′<b>b</b> + <b>x</b>′<b>B</b><b>x</b>,&nbsp;&nbsp; <b>b</b> = [<i>β̂</i><sub>1</sub>, <i>β̂</i><sub>2</sub>]′,&nbsp;&nbsp; <b>B</b> = [<i>β̂</i><sub>11</sub>, <i>β̂</i><sub>12</sub>/2; <i>β̂</i><sub>12</sub>/2, <i>β̂</i><sub>22</sub>]</span><span class="num">(3)</span></div>
<p>y el punto estacionario se obtuvo igualando el gradiente a cero (Myers et al., 2016):</p>
<div class="eq"><span><b>x</b><sub>s</sub> = −½ <b>B</b><sup>−1</sup><b>b</b>,&nbsp;&nbsp;&nbsp; <i>ŷ</i><sub>s</sub> = <i>β̂</i><sub>0</sub> + ½ <b>x</b><sub>s</sub>′<b>b</b></span><span class="num">(4)</span></div>
<p>Su naturaleza se determinó por el signo de los valores propios de <b>B</b>: todos negativos (máximo), todos positivos (mínimo) o de
signo mixto (punto silla). Como el punto estacionario puede caer fuera de la región observada, se buscó además el máximo de
<i>ŷ</i> sobre una malla de 201 × 201 puntos en −1 ≤ <i>x<sub>i</sub></i> ≤ 1 y los resultados se decodificaron con
<i>T<sub>i</sub></i> = <i>T<sub>i</sub></i><sup>c</sup> + (Δ<i>T<sub>i</sub></i>/2)<i>x<sub>i</sub></i>.</p>
<p>La adecuación del modelo se verificó mediante <i>R</i><sup>2</sup>, <i>R</i><sup>2</sup> ajustado, <i>R</i><sup>2</sup> de predicción (estadístico
PRESS), raíz del error cuadrático medio (RMSE) y análisis de residuos: normalidad (Kolmogórov–Smirnov y Anderson–Darling; Anderson &amp;
Darling, 1954), homocedasticidad (residuos frente a valores predichos) e independencia (Durbin &amp; Watson, 1950). Los cálculos se realizaron
en GNU Octave (Eaton et al., 2020) y se verificaron de forma independiente en Python (NumPy, SciPy).</p>"""

RES_DESC = f"""<p>La Tabla {{TDESC}} resume las variables analizadas. La temperatura de entrada del agua varió entre 11.9 y 48.1 °C (media
{f(D['Tw']['mean'])} °C) y la temperatura exterior entre −5.3 y 15.3 °C (media {f(D['Te']['mean'])} °C), lo que refleja una
amplitud térmica exterior de más de 20 °C. La temperatura operativa interior osciló entre 5.7 y 20.2 °C, con media de
{f(D['To']['mean'])} °C; solo el {f(R['frac_18'],1)} % de los registros superó 18 °C y el {f(R['frac_comfort20'],2)} % alcanzó
20 °C. La correlación entre los factores fue despreciable (<i>r</i> = {f(R['r12'],3)}; VIF = {f(R['VIF'],3)}), de modo que sus efectos pueden
estimarse de manera independiente. La <i>T</i><sub>op</sub> se correlacionó más con <i>T</i><sub>e</sub> (<i>r</i> = {f(R['r_p2'],3)}) que
con <i>T</i><sub>w</sub> (<i>r</i> = {f(R['r_p1'],3)}).</p>
<p>Por franja horaria (Tabla {{THOR}}; Figura {{F5}}), las condiciones más desfavorables se presentaron en la mañana, con
<i>T</i><sub>e</sub> media de {f(BH['Mañana']['Te_mean'])} °C y <i>T</i><sub>op</sub> de {f(BH['Mañana']['To_mean'])} °C, mientras que en la tarde,
con mayor temperatura exterior y ganancia solar, la <i>T</i><sub>op</sub> media llegó a {f(BH['Tarde']['To_mean'])} °C. La segunda semana
presentó una <i>T</i><sub>op</sub> media ligeramente superior ({f(R['by_week']['2']['To'])} °C frente a {f(R['by_week']['1']['To'])} °C).</p>"""

RES_MOD = f"""<p>Los coeficientes estimados se muestran en la Tabla {{TCOEF}}. El modelo ajustado en variables codificadas es</p>
<div class="eq"><span>{EQ_MODEL}</span><span class="num">(5)</span></div>
<p>y, expresado en variables reales (°C),</p>
<div class="eq" style="font-size:9.3pt"><span>{EQ_REAL}</span><span class="num">(6)</span></div>
<p>El ANOVA (Tabla {{TANOVA}}) indica que la regresión es altamente significativa (<i>F</i><sub>0</sub> = {f(R['F'],2)}; <i>p</i> &lt; 0.001) y que el
modelo explica el {f(R['R2']*100,2)} % de la variabilidad de la <i>T</i><sub>op</sub>. Los términos de segundo orden, en conjunto, aportan una mejora
significativa respecto del modelo de primer orden (<i>F</i> = {f(R['F_2o'],2)}; <i>p</i> &lt; 0.001), aunque modesta en magnitud
(<i>R</i><sup>2</sup> de {f(R['R2_lin'],4)} a {f(R['R2'],4)}). Todos los coeficientes fueron significativos salvo <i>β</i><sub>11</sub>
(<i>p</i> = {f(R['pt'][3],3)}), lo que indica que la respuesta varía de forma prácticamente lineal con <i>T</i><sub>w</sub> en el rango estudiado. En
unidades físicas, en el centro de la región, un aumento de 1 °C en <i>T</i><sub>w</sub> eleva la <i>T</i><sub>op</sub> en
{f(R['slope_T1_mid'],3)} °C, mientras que un aumento de 1 °C en <i>T</i><sub>e</sub> la eleva en {f(b2/h2,3)} °C.</p>"""

RES_CANON = f"""<p>En forma matricial, <b>b</b> = [{f(b1,4)}; {f(b2,4)}] y <b>B</b> = [{f(b11,4)}, {f(b12/2,4)}; {f(b12/2,4)}, {f(b22,4)}]. Los valores
propios de <b>B</b> fueron <i>λ</i><sub>1</sub> = {f(lam1,4)} y <i>λ</i><sub>2</sub> = {f(lam2,4)}; al tener signos opuestos, el punto
estacionario <b>x</b><sub>s</sub> = ({f(R['xs'][0],3)}; {f(R['xs'][1],3)}) es un <b>punto silla</b> (Tabla {{TCANON}}). Además, se encuentra fuera de la
región experimental (|<i>x</i><sub>1,s</sub>| &gt; 1), pues su decodificación exige <i>T</i><sub>w</sub> = {f(R['T1s'],1)} °C, valor físicamente
inviable para un piso radiante; por tanto, no constituye un óptimo operativo. La superficie (Figura {{F1}}) y el diagrama de contorno
(Figura {{F2}}) muestran una respuesta creciente en ambas direcciones, sin máximo interior; la mejor condición se ubica en el vértice
(<i>x</i><sub>1</sub>, <i>x</i><sub>2</sub>) = (1, 1), equivalente a <i>T</i><sub>w</sub> = {f(R['T1m'],1)} °C y <i>T</i><sub>e</sub> =
{f(R['T2m'],1)} °C, con <i>T</i><sub>op</sub> estimada de {f(R['ymax'],2)} °C.</p>"""

RES_VALID = f"""<p>La Figura {{F3}} compara los valores observados y predichos: los puntos se agrupan en torno a la recta 1:1 sin sesgo sistemático,
con RMSE = {f(R['RMSE'],2)} °C y MAE = {f(R['MAE'],2)} °C. El <i>R</i><sup>2</sup> de predicción ({f(R['R2pred'],4)}) es prácticamente igual al
<i>R</i><sup>2</sup> ajustado, lo que descarta sobreajuste. El análisis de residuos (Figura {{F4}}; Tabla {{TDIAG}}) muestra varianza aproximadamente
constante y distribución cercana a la normal (KS: <i>p</i> = {f(R['KS_p'],3)}), con una ligera asimetría negativa ({f(R['skew'],2)}) atribuible a
algunos registros de baja <i>T</i><sub>op</sub> al inicio de las sesiones matutinas. El estadístico de Durbin–Watson (DW = {f(R['DW'],2)})
revela autocorrelación positiva de los residuos, esperable en series temporales de un sistema con inercia térmica.</p>
<p>La Figura {{F6}} ilustra la interacción negativa (<i>β</i><sub>12</sub> = {f(b12,3)}): la pendiente de la <i>T</i><sub>op</sub> respecto de
<i>T</i><sub>w</sub> es de {f(R['slope_T1_cold'],3)} °C/°C cuando el exterior está a −5.3 °C y se reduce a {f(R['slope_T1_warm'],3)} °C/°C con
15.3 °C. Ninguna combinación dentro de la región alcanza el rango de confort invernal de 20–24 °C.</p>"""

DISC = f"""<p>Los resultados muestran que la temperatura operativa interior está gobernada principalmente por la temperatura exterior, cuyo
efecto codificado (<i>β</i><sub>2</sub> = {f(b2,2)}) duplica al de la temperatura del agua (<i>β</i><sub>1</sub> = {f(b1,2)}). Este hallazgo es
coherente con un ambiente cuyas pérdidas por la envolvente son elevadas frente al aporte del piso, de modo que el balance térmico del
recinto sigue de cerca las condiciones exteriores. El efecto positivo y casi lineal de <i>T</i><sub>w</sub> concuerda con la física del
intercambio piso–ambiente, en el que el flujo de calor es aproximadamente proporcional a la diferencia entre la temperatura superficial
y la operativa (Olesen, 2002; ISO 11855-1, 2021).</p>
<p>La interacción negativa indica que elevar la temperatura del agua es más eficaz precisamente cuando más se necesita, es decir, en las
horas frías. En horas cálidas la ganancia solar y la menor demanda reducen el beneficio marginal del agua caliente. Desde el punto de vista
operativo, ello respalda estrategias de control con curva de compensación climática, en las que <i>T</i><sub>w</sub> se ajusta en función de
<i>T</i><sub>e</sub>, recomendadas para sistemas de baja temperatura (Babiak et al., 2007).</p>
<p>El análisis canónico identificó un punto silla fuera de la región, situación frecuente cuando los datos cubren una zona de la superficie
alejada del óptimo (Myers et al., 2016; Montgomery, 2017). En estos casos, la recomendación metodológica es explorar en la dirección de máximo
ascenso o analizar la cresta de la superficie; aquí, la dirección de mejora implica aumentar <i>T</i><sub>w</sub>, cuyo límite superior real
está fijado por la temperatura superficial máxima admisible del piso (del orden de 29 °C en zonas ocupadas según ISO 11855-1). La temperatura
superficial máxima medida en el centro del piso (≈ 29.7 °C) indica que el sistema ya opera cerca de ese límite, por lo que incrementar
<i>T</i><sub>w</sub> no sería una solución adecuada.</p>
<p>La <i>T</i><sub>op</sub> máxima estimada ({f(R['ymax'],1)} °C) y la escasa proporción de registros ≥ 20 °C ({f(R['frac_comfort20'],2)} %) muestran que el
sistema no alcanza los niveles de confort de invierno recomendados por ISO 7730 (2005) y ASHRAE 55 (2020). Por ello, las mejoras deben orientarse
a reducir pérdidas (aislamiento de la envolvente y del piso, hermeticidad) y a extender el tiempo de funcionamiento previo a las horas críticas,
aprovechando la inercia de la losa.</p>
<p>Entre las limitaciones del estudio destacan: (i) los datos provienen de mediciones de campo y no de un diseño experimental planificado
(p. ej., central compuesto), por lo que la región explorada está determinada por las condiciones naturales; (ii) la autocorrelación de los
residuos (DW = {f(R['DW'],2)}) implica que los errores estándar pueden estar subestimados y los valores <i>p</i> deben interpretarse con cautela,
si bien la magnitud de los estadísticos <i>F</i> y <i>t</i> de los términos principales hace improbable que cambie la conclusión; (iii) no se
incluyeron variables como radiación solar, caudal o retardos temporales asociados a la inercia de la losa; y (iv) el estudio corresponde a un
único ambiente y a dos semanas de medición.</p>"""

CONCL = f"""<p>(1) Se obtuvo un modelo de superficie de respuesta de segundo orden que explica el {f(R['R2']*100,1)} % de la variabilidad de la temperatura
operativa interior (RMSE = {f(R['RMSE'],2)} °C), con capacidad predictiva verificada (<i>R</i><sup>2</sup><sub>pred</sub> = {f(R['R2pred'],3)}).</p>
<p>(2) La temperatura exterior es el factor de mayor influencia; la temperatura de entrada del agua tiene un efecto positivo, significativo y
prácticamente lineal, y la interacción negativa entre ambas indica que el agua caliente es más eficaz en condiciones frías.</p>
<p>(3) El punto estacionario es un punto silla situado fuera de la región experimental (<i>T</i><sub>w</sub> ≈ {f(R['T1s'],0)} °C), por lo que no representa un
óptimo físicamente alcanzable. La mejor condición observada es <i>T</i><sub>w</sub> = {f(R['T1m'],1)} °C con <i>T</i><sub>e</sub> = {f(R['T2m'],1)} °C, que
produce una <i>T</i><sub>op</sub> estimada de {f(R['ymax'],1)} °C.</p>
<p>(4) En su configuración actual, el sistema no alcanza el umbral de confort invernal de 20 °C. Se recomiendan mejoras en la envolvente, un control con
compensación climática y futuros estudios con diseño central compuesto, modelos con retardos temporales y variables adicionales como la radiación solar y el caudal.</p>"""

# ------------------------------------------------------------------ ARTÍCULO
def numerar(html, mapping):
    for k, v in mapping.items():
        html = html.replace("{" + k + "}", str(v))
    return html


art_map = {"TCOD": "Tabla 2", "TDESC": "3", "THOR": "4", "TCOEF": "5", "TANOVA": "6", "TCANON": "7", "TDIAG": "8",
           "F1": "2", "F2": "3", "F3": "4", "F4": "5", "F5": "1", "F6": "6"}

TAB_VARS = """<div class="tbl"><p class="cap"><b>Tabla 1.</b> Variables medidas e instrumentos.</p>
<table><thead><tr><th class='l'>Ubicación</th><th class='l'>Variable</th><th class='l'>Instrumento</th></tr></thead><tbody>
<tr><td class='l'>Circuito hidráulico</td><td class='l'>T de caldera, T de entrada y salida del agua (°C)</td><td class='l'>Sensores de temperatura</td></tr>
<tr><td class='l'>Interior</td><td class='l'>T del aire, T radiante, T operativa (°C); HR (%)</td><td class='l'>Termohigrómetro con globo</td></tr>
<tr><td class='l'>Interior</td><td class='l'>Velocidad del aire (m/s)</td><td class='l'>Anemómetro</td></tr>
<tr><td class='l'>Piso</td><td class='l'>T superficial en centro, extremo y puerta (°C)</td><td class='l'>Termómetro de contacto</td></tr>
<tr><td class='l'>Exterior</td><td class='l'>T del aire, T radiante, T operativa (°C); HR (%)</td><td class='l'>Termohigrómetro con globo</td></tr>
</tbody></table></div>"""

articulo = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Artículo científico – MSR piso radiante</title>
<link rel="stylesheet" href="estilos.css"><style>
.top {{ border-top:3px solid var(--accent); padding-top:6px; }}
.jr {{ display:flex; justify-content:space-between; font-family:"Liberation Sans",Arial,sans-serif; font-size:7.8pt; color:var(--muted); }}
.type {{ font-family:"Liberation Sans",Arial,sans-serif; font-size:8pt; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); margin:14px 0 4px; font-weight:700; }}
h1.t {{ font-size:17pt; line-height:1.18; margin:0 0 6px; color:#111; }}
.ten {{ font-family:"Liberation Sans",Arial,sans-serif; font-size:11pt; font-style:italic; color:var(--muted); margin:0 0 10px; line-height:1.25; }}
.auth {{ font-family:"Liberation Sans",Arial,sans-serif; font-size:10.5pt; margin:4px 0 4px; }}
.aff {{ font-size:8.2pt; color:var(--muted); line-height:1.35; margin-bottom:10px; text-align:left; }}
.abs {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; border-top:.8px solid var(--rule); border-bottom:.8px solid var(--rule); padding:9px 0 8px; margin-bottom:12px; font-size:8.7pt; line-height:1.33; }}
.abs h4 {{ margin:0 0 4px; font-size:9pt; text-transform:uppercase; letter-spacing:.06em; }}
.abs .kw {{ margin-top:6px; text-align:left; }}
.cols {{ padding-left:0; }}
.cols p {{ text-indent:0; }}
.cols h2 {{ font-size:10.5pt; margin:12px 0 5px; text-transform:uppercase; letter-spacing:.03em; }}
.cols h3 {{ font-size:9.6pt; margin:9px 0 4px; font-style:italic; }}
.span {{ column-span:all; }}
.cols .eq {{ font-size:9.6pt; }}
.decl p {{ font-size:8.7pt; }}
</style></head><body>
<div class="top"><div class="jr"><span>Artículo original · Ingeniería Mecánica Eléctrica / Energía en edificaciones</span><span>Manuscrito preparado para revista indexada en Scopus</span></div></div>
<div class="type">Artículo de investigación</div>
<h1 class="t">{TIT_ES}</h1>
<p class="ten">{TIT_EN}</p>
<p class="auth">{AUT1}<sup>1,*</sup>, {AUT2}<sup>1</sup>, {DOC_}<sup>2</sup></p>
<p class="aff"><sup>1</sup> Estudiante investigador, curso de Metodología de la Investigación. &nbsp;
<sup>2</sup> Docente nombrado, Ingeniero Mecánico Electricista; asesor de la investigación.<br>
<sup>*</sup> Autor de correspondencia: {EMAIL}</p>
<div class="abs"><div><h4>Resumen</h4><p>{RESUMEN}</p><p class="kw"><b>Palabras clave:</b> {KW_ES}.</p></div>
<div><h4>Abstract</h4><p>{ABSTRACT}</p><p class="kw"><b>Keywords:</b> {KW_EN}.</p></div></div>
<div class="cols">
<h2>1. Introducción</h2>{INTRO}
<h2>2. Materiales y métodos</h2>
<h3>2.1. Sistema estudiado y adquisición de datos</h3>{METODOS_SISTEMA}
{TAB_VARS}
<h3>2.2. Factores, respuesta y modelo de superficie de respuesta</h3>
{numerar(METODOS_MSR, {"TCOD": "Tabla 2"})}
{TAB_COD.replace('{n}', '2')}
<h2>3. Resultados</h2>
<h3>3.1. Análisis descriptivo</h3>
{numerar(RES_DESC, art_map)}
{TAB_DESC.replace('{n}', '3')}
{TAB_HOR.replace('{n}', '4')}
{fig('fig5_horarios.png', 1, 'Distribución de la temperatura de entrada del agua, la temperatura exterior y la temperatura operativa interior por franja horaria.', '90%')}
<h3>3.2. Modelo de segundo orden y ANOVA</h3>
{numerar(RES_MOD, art_map)}
{TAB_COEF.replace('{n}', '5')}
{TAB_ANOVA.replace('{n}', '6')}
<h3>3.3. Análisis canónico y región de operación</h3>
{numerar(RES_CANON, art_map)}
{TAB_CANON.replace('{n}', '7')}
{fig('fig1_superficie.png', 2, 'Superficie de respuesta ajustada de la temperatura operativa interior en función de <i>T</i><sub>w</sub> y <i>T</i><sub>e</sub>; los puntos son las observaciones.', '66%')}
{fig('fig2_contorno.png', 3, 'Contornos de la temperatura operativa estimada (°C). La estrella indica la mejor condición dentro de la región experimental.', '64%')}
<h3>3.4. Adecuación del modelo</h3>
{numerar(RES_VALID, art_map)}
{fig('fig3_obs_pred.png', 4, 'Valores observados frente a predichos de la temperatura operativa.', '46%')}
{TAB_DIAG.replace('{n}', '8')}
<div class="span">{fig('fig4_residuos.png', 5, 'Diagnóstico de residuos: (a) residuos frente a valores predichos; (b) histograma con densidad normal; (c) gráfico Q–Q normal; (d) residuos en orden de registro.', '82%')}</div>
{fig('fig6_interaccion.png', 6, 'Efecto de <i>T</i><sub>w</sub> sobre la <i>T</i><sub>op</sub> estimada para distintos niveles de <i>T</i><sub>e</sub> (interacción). La banda verde indica el rango de confort invernal.', '60%')}
<h2>4. Discusión</h2>{DISC}
<h2>5. Conclusiones</h2>{CONCL}
<div class="decl">
<h2>Contribución de los autores (CRediT)</h2>
<p><b>{AUT1}:</b> conceptualización, recolección de datos, análisis formal, software, redacción del borrador original. <b>{AUT2}:</b> metodología,
recolección de datos, curación de datos, visualización, redacción – revisión. <b>{DOC_}:</b> supervisión, validación, redacción – revisión y edición.</p>
<h2>Disponibilidad de datos</h2>
<p>Los datos ({R['n']} registros), el código en GNU Octave y los scripts de verificación están disponibles a solicitud del autor de correspondencia.</p>
<h2>Conflicto de intereses</h2><p>Los autores declaran no tener conflictos de intereses.</p>
<h2>Financiamiento</h2><p>Esta investigación no recibió financiamiento específico de agencias públicas, comerciales o sin fines de lucro.</p>
</div>
<h2>Referencias</h2><div class="refs">{REFS_HTML}</div>
</div></body></html>"""

# ------------------------------------------------------------------ INFORME
inf_map = {"TCOD": "Tabla 3", "TDESC": "4", "THOR": "5", "TCOEF": "6", "TANOVA": "7", "TCANON": "8", "TDIAG": "9",
           "F1": "2", "F2": "3", "F3": "4", "F4": "5", "F5": "1", "F6": "6"}

octave_code = (ROOT / "proyecto_octave/superficie_respuesta.m").read_text(encoding="utf-8")
octave_res = (ROOT / "proyecto_octave/resultados/resultados.txt").read_text(encoding="utf-8")
esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

TOC = [("Resumen", "res"), ("I. Introducción", "s1"), ("II. Planteamiento del problema", "s2"), ("III. Objetivos", "s3"),
       ("IV. Hipótesis y variables", "s4"), ("V. Marco teórico", "s5"), ("VI. Metodología", "s6"), ("VII. Resultados", "s7"),
       ("VIII. Discusión", "s8"), ("IX. Conclusiones", "s9"), ("X. Recomendaciones", "s10"), ("Referencias", "ref"),
       ("Anexo A. Matriz de consistencia", "aA"), ("Anexo B. Código fuente en GNU Octave", "aB"), ("Anexo C. Salida de resultados", "aC")]
toc_html = "".join(f'<li><a href="#{a}"><span>{t}</span><span class="pg" data-target="{a}"></span></a></li>' for t, a in TOC)

informe = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Informe de investigación – MSR piso radiante</title>
<link rel="stylesheet" href="estilos.css"><style>
body {{ font-size:11pt; line-height:1.5; }}
.cover {{ height:250mm; display:flex; flex-direction:column; align-items:center; text-align:center; break-after:page; border:1.5px solid var(--accent); outline:4px solid #fff; box-shadow:0 0 0 5.5px var(--accent); padding:22mm 16mm 14mm; }}
.cover .k {{ font-family:"Liberation Sans",Arial,sans-serif; letter-spacing:.18em; text-transform:uppercase; font-size:10pt; color:var(--muted); }}
.cover h1 {{ font-size:19pt; line-height:1.25; margin:16mm 0 6mm; color:#111; text-align:center; }}
.cover .sub {{ font-family:"Liberation Sans",Arial,sans-serif; font-size:12pt; color:var(--accent); font-weight:700; letter-spacing:.08em; text-transform:uppercase; }}
.cover .rule {{ width:60mm; height:2px; background:var(--accent); margin:9mm auto; }}
.cover table {{ width:auto; font-size:11pt; margin:0 auto; }}
.cover td {{ text-align:left; padding:3px 8px; border:none !important; vertical-align:top; }}
.cover td.h {{ font-family:"Liberation Sans",Arial,sans-serif; font-weight:700; color:var(--accent); white-space:nowrap; }}
.cover .foot {{ margin-top:auto; font-family:"Liberation Sans",Arial,sans-serif; font-size:11pt; color:var(--muted); }}
h2.s {{ font-size:14pt; border-bottom:1.5px solid var(--accent); padding-bottom:3px; margin:0 0 10px; break-before:page; text-transform:uppercase; letter-spacing:.02em; }}
h3 {{ font-size:11.5pt; margin:14px 0 6px; }}
h4 {{ font-size:10.5pt; margin:10px 0 4px; color:#2d3748; }}
.toc ul {{ list-style:none; padding:0; margin:0; }}
.toc li a {{ display:flex; color:var(--ink); text-decoration:none; padding:4px 0; border-bottom:1px dotted #b8c2cc; }}
.toc li a span:first-child {{ flex:1; }}
ul.b, ol.b {{ margin:.2em 0 .7em 1.2em; padding-left:.6em; }}
ul.b li, ol.b li {{ margin-bottom:.25em; }}
table {{ font-size:9.3pt; }}
.mc td, .mc th {{ font-size:7.6pt; vertical-align:top; text-align:left; border:.6px solid #9aa5b1; padding:4px 5px; line-height:1.3; }}
.mc thead th {{ background:var(--soft); }}
.mc th:nth-child(1),.mc th:nth-child(2),.mc th:nth-child(3) {{ width:22%; }} .mc th:nth-child(4) {{ width:12%; }}
</style></head><body>

<section class="cover">
<div class="k">Curso: Metodología de la Investigación</div>
<h1>{TIT_ES.upper()}</h1>
<div class="sub">Informe de investigación</div>
<div class="rule"></div>
<table>
<tr><td class="h">Integrantes:</td><td>{AUT1.upper()}<br>{AUT2.upper()}</td></tr>
<tr><td class="h">Docente asesor:</td><td>Ing. {DOC_.upper()}</td></tr>
<tr><td class="h">Condición y categoría:</td><td>Nombrado</td></tr>
<tr><td class="h">Especialidad:</td><td>Ingeniero Mecánico Electricista</td></tr>
<tr><td class="h">Período de medición:</td><td>11 al 25 de septiembre de 2026</td></tr>
</table>
<div class="foot">Noviembre de 2026</div>
</section>

<section class="toc"><h2 class="s" style="break-before:auto">Índice</h2><ul>{toc_html}</ul>
<h3>Índice de tablas y figuras</h3>
<p style="font-size:9.5pt;text-align:left">Tabla 1. Operacionalización de variables · Tabla 2. Instrumentos · Tabla 3. Codificación de factores · Tabla 4. Estadística
descriptiva · Tabla 5. Resultados por franja horaria · Tabla 6. Coeficientes del modelo · Tabla 7. ANOVA · Tabla 8. Análisis canónico · Tabla 9.
Diagnóstico de supuestos · Tabla 10. Contraste de hipótesis.<br>Figura 1. Distribución por franja horaria · Figura 2. Superficie de respuesta ·
Figura 3. Contornos · Figura 4. Observado vs. predicho · Figura 5. Residuos · Figura 6. Interacción.</p></section>

<h2 class="s" id="res">Resumen</h2>
<p>{RESUMEN}</p><p><b>Palabras clave:</b> {KW_ES}.</p>
<h3>Abstract</h3><p><i>{ABSTRACT}</i></p><p><b>Keywords:</b> {KW_EN}.</p>

<h2 class="s" id="s1">I. Introducción</h2>{INTRO}
<p>El presente informe se organiza de la siguiente manera: el capítulo II plantea el problema; los capítulos III y IV presentan los objetivos,
las hipótesis y las variables; el capítulo V desarrolla el marco teórico; el VI describe la metodología; el VII expone los resultados; el VIII
los discute, y los capítulos IX y X presentan las conclusiones y recomendaciones.</p>

<h2 class="s" id="s2">II. Planteamiento del problema</h2>
<h3>2.1. Descripción de la realidad problemática</h3>
<p>En las zonas de clima frío, las viviendas y ambientes de trabajo registran temperaturas interiores bajas durante gran parte del año, en especial
en las primeras horas de la mañana, cuando la temperatura exterior desciende por debajo de 0 °C. Esta condición afecta el confort, la salud y la
productividad de los ocupantes. Los sistemas de piso radiante son una alternativa técnica para mejorar el ambiente interior; sin embargo, su
operación suele basarse en ajustes empíricos de la temperatura del agua sin conocer cuantitativamente cómo esta variable, junto con la temperatura
exterior, determina la temperatura operativa que perciben los ocupantes. Esta falta de un modelo cuantitativo impide establecer condiciones de
operación adecuadas y evaluar si el sistema es capaz de alcanzar el confort térmico.</p>
<h3>2.2. Formulación del problema</h3>
<h4>Problema general</h4>
<p>¿Cómo influyen la temperatura de entrada del agua y la temperatura del aire exterior en la temperatura operativa interior de un ambiente
calefaccionado por piso radiante, modelada mediante la metodología de superficie de respuesta?</p>
<h4>Problemas específicos</h4>
<ol class="b"><li>¿Cuál es el efecto lineal, cuadrático y de interacción de la temperatura de entrada del agua y de la temperatura exterior sobre la temperatura operativa interior?</li>
<li>¿Qué naturaleza tiene el punto estacionario de la superficie de respuesta y se ubica dentro de la región experimental?</li>
<li>¿Cuál es la mejor condición de operación dentro de la región estudiada y permite alcanzar el confort térmico?</li></ol>
<h3>2.3. Justificación</h3>
<p><b>Técnica:</b> el modelo permite predecir la temperatura operativa a partir de variables medibles y orientar la regulación de la caldera.
<b>Económica:</b> conocer el efecto marginal de la temperatura del agua evita sobrecalentamientos innecesarios y el consumo excesivo de combustible.
<b>Social:</b> contribuye a mejorar las condiciones de confort y salud en ambientes de clima frío. <b>Metodológica:</b> muestra la aplicación de la MSR
(Montgomery, 2017) a datos de campo, incluido el análisis canónico y la verificación de supuestos.</p>
<h3>2.4. Delimitación</h3>
<p><b>Espacial:</b> un ambiente experimental con sistema hidrónico de piso radiante. <b>Temporal:</b> 11 al 25 de septiembre de 2026, en tres franjas diarias.
<b>Conceptual:</b> se estudian dos factores (<i>T</i><sub>w</sub>, <i>T</i><sub>e</sub>) y una respuesta (<i>T</i><sub>op</sub>).</p>

<h2 class="s" id="s3">III. Objetivos</h2>
<h3>3.1. Objetivo general</h3>
<p>Modelar la temperatura operativa interior de un ambiente calefaccionado por piso radiante en función de la temperatura de entrada del agua y de la
temperatura del aire exterior mediante la metodología de superficie de respuesta.</p>
<h3>3.2. Objetivos específicos</h3>
<ol class="b"><li>Estimar y evaluar estadísticamente los efectos lineales, cuadráticos y de interacción de un modelo de segundo orden.</li>
<li>Determinar la ubicación y la naturaleza del punto estacionario mediante el análisis canónico.</li>
<li>Identificar la mejor condición de operación dentro de la región experimental y contrastarla con los criterios de confort térmico.</li></ol>

<h2 class="s" id="s4">IV. Hipótesis y variables</h2>
<h3>4.1. Hipótesis general</h3>
<p>La temperatura de entrada del agua y la temperatura del aire exterior influyen significativamente en la temperatura operativa interior, y dicha
relación puede representarse adecuadamente mediante un modelo de superficie de respuesta de segundo orden.</p>
<h3>4.2. Hipótesis específicas</h3>
<ol class="b"><li>H<sub>E1</sub>: al menos un término lineal, cuadrático o de interacción del modelo es significativo (H<sub>0</sub>: <i>β</i><sub>1</sub> = <i>β</i><sub>2</sub> = <i>β</i><sub>11</sub> = <i>β</i><sub>22</sub> = <i>β</i><sub>12</sub> = 0).</li>
<li>H<sub>E2</sub>: la superficie de respuesta presenta un punto estacionario de tipo máximo dentro de la región experimental.</li>
<li>H<sub>E3</sub>: existe una condición de operación dentro de la región experimental que permite alcanzar una temperatura operativa de al menos 20 °C.</li></ol>
<h3>4.3. Operacionalización de variables</h3>
<div class="tbl"><p class="cap"><b>Tabla 1.</b> Operacionalización de variables.</p>
<table><thead><tr><th class='l'>Variable</th><th class='l'>Tipo</th><th class='l'>Definición operacional</th><th class='l'>Indicador / unidad</th><th class='l'>Escala</th></tr></thead><tbody>
<tr><td class='l'>Temperatura de entrada del agua (<i>T</i><sub>w</sub>)</td><td class='l'>Independiente (controlable)</td><td class='l'>Temperatura del agua al ingresar al circuito del piso</td><td class='l'>°C; codificada <i>x</i><sub>1</sub></td><td class='l'>Razón</td></tr>
<tr><td class='l'>Temperatura del aire exterior (<i>T</i><sub>e</sub>)</td><td class='l'>Independiente (ambiental)</td><td class='l'>Temperatura del aire medida con termohigrómetro exterior</td><td class='l'>°C; codificada <i>x</i><sub>2</sub></td><td class='l'>Intervalo</td></tr>
<tr><td class='l'>Temperatura operativa interior (<i>T</i><sub>op</sub>)</td><td class='l'>Dependiente</td><td class='l'>Media de la T del aire y la T radiante en el interior</td><td class='l'>°C</td><td class='l'>Intervalo</td></tr>
</tbody></table></div>

<h2 class="s" id="s5">V. Marco teórico</h2>
<h3>5.1. Antecedentes</h3>
<p>Box y Wilson (1951) propusieron la metodología de superficie de respuesta para alcanzar experimentalmente condiciones óptimas mediante polinomios
de primer y segundo orden, base de la teoría desarrollada posteriormente por Myers et al. (2016). Bezerra et al. (2008) describen su aplicación
sistemática en la optimización de procesos, incluido el uso del análisis canónico. En el campo de los sistemas radiantes, Olesen (2002) analizó los
fundamentos y la práctica de la calefacción por piso radiante, y Babiak et al. (2007) establecieron criterios de diseño para sistemas de calefacción de
baja temperatura. Rhee y Kim (2015) revisaron cincuenta años de investigación en calefacción y refrigeración radiante, destacando la necesidad de estudios
de campo que vinculen las variables de operación con el confort.</p>
<h3>5.2. Bases teóricas</h3>
<h4>a) Calefacción por piso radiante</h4>
<p>Es un sistema hidrónico en el que el agua calentada por una caldera circula por tuberías embebidas en la losa del piso. El calor se transmite por
conducción a la superficie del piso y desde esta al ambiente por radiación (≈ 60 %) y convección. La temperatura superficial del piso se limita, por
confort de los pies, a un máximo del orden de 29 °C en zonas ocupadas (ISO 11855-1, 2021).</p>
<h4>b) Temperatura operativa y confort térmico</h4>
<p>La temperatura operativa es la temperatura uniforme de un recinto negro imaginario en el que un ocupante intercambiaría la misma cantidad de calor por
radiación y convección que en el ambiente real. Para velocidades del aire bajas (&lt; 0.2 m/s) se aproxima como la media de la temperatura del aire y la
temperatura radiante media (ISO 7730, 2005). Las normas ISO 7730 y ASHRAE 55 (2020), basadas en el modelo de Fanger (1970), recomiendan en invierno
temperaturas operativas de aproximadamente 20 a 24 °C para actividad sedentaria.</p>
<h4>c) Metodología de superficie de respuesta</h4>
<p>Conjunto de técnicas matemáticas y estadísticas para modelar y analizar problemas en los que una respuesta depende de varias variables, con el
objetivo de optimizarla (Montgomery, 2017). El modelo de segundo orden permite representar curvatura e interacción; el análisis canónico, mediante los
valores propios de la matriz <b>B</b>, determina si el punto estacionario es un máximo, un mínimo o un punto silla (Myers et al., 2016).</p>
<h3>5.3. Definición de términos</h3>
<ul class="b"><li><b>Factor codificado:</b> variable transformada al intervalo [−1, 1] para comparar efectos en una misma escala.</li>
<li><b>Punto estacionario:</b> punto en el que el gradiente de la superficie es nulo.</li>
<li><b>Punto silla:</b> punto estacionario que no es máximo ni mínimo; la respuesta aumenta en una dirección y disminuye en otra.</li>
<li><b>Termómetro de globo:</b> esfera negra con sensor interno que integra la radiación del entorno para estimar la temperatura radiante media (ISO 7726, 1998).</li></ul>

<h2 class="s" id="s6">VI. Metodología</h2>
<h3>6.1. Enfoque, tipo, nivel y diseño</h3>
<p>La investigación tiene enfoque <b>cuantitativo</b>, es de tipo <b>aplicada</b> y de nivel <b>explicativo</b>. El diseño es <b>no experimental, longitudinal</b>
(mediciones de campo repetidas en el tiempo sobre el sistema en operación), con análisis mediante la metodología de superficie de respuesta.</p>
<h3>6.2. Población y muestra</h3>
<p>La población está constituida por todas las condiciones de operación del sistema de piso radiante durante el período de estudio. La muestra comprende
{R['n']} registros con el sistema en funcionamiento (con temperatura de agua registrada), tomados cada 5 min en tres franjas diarias durante dos semanas
(muestreo no probabilístico por conveniencia temporal). Algunas fechas del archivo fuente aparecen con el mes «08» en lugar de «09»
(13/08 y 23/08), lo que corresponde a errores de transcripción que no afectan el análisis.</p>
<h3>6.3. Técnicas e instrumentos</h3>
<p>Se aplicó la técnica de <b>observación sistemática con medición instrumental</b>, y los datos se registraron en fichas de registro digitales (hojas de cálculo).</p>
{TAB_VARS.replace('Tabla 1.', 'Tabla 2.')}
<h3>6.4. Procedimiento</h3>{METODOS_SISTEMA}
<h3>6.5. Técnicas de procesamiento y análisis de datos</h3>
{numerar(METODOS_MSR, {"TCOD": "Tabla 3"})}
{TAB_COD.replace('{n}', '3')}
<p>Los pasos implementados en el script <code>superficie_respuesta.m</code> (Anexo B) fueron: (1) lectura de datos; (2) codificación; (3) construcción de la
matriz <b>X</b> y estimación de coeficientes; (4) forma matricial; (5) cálculo del punto estacionario; (6) valores propios de <b>B</b>; (7) decodificación;
(8) búsqueda de la mejor condición en la región; y (9) elaboración de gráficos.</p>

<h2 class="s" id="s7">VII. Resultados</h2>
<h3>7.1. Análisis descriptivo</h3>
{numerar(RES_DESC, inf_map)}
{TAB_DESC.replace('{n}', '4')}
{TAB_HOR.replace('{n}', '5')}
{fig('fig5_horarios.png', 1, 'Distribución de <i>T</i><sub>w</sub>, <i>T</i><sub>e</sub> y <i>T</i><sub>op</sub> por franja horaria.', '92%')}
<h3>7.2. Modelo de segundo orden y ANOVA</h3>
{numerar(RES_MOD, inf_map)}
{TAB_COEF.replace('{n}', '6')}
{TAB_ANOVA.replace('{n}', '7')}
<h3>7.3. Análisis canónico y región de operación</h3>
{numerar(RES_CANON, inf_map)}
{TAB_CANON.replace('{n}', '8')}
{fig('fig1_superficie.png', 2, 'Superficie de respuesta ajustada de la temperatura operativa interior.', '78%')}
{fig('fig2_contorno.png', 3, 'Contornos de la temperatura operativa estimada (°C) y mejor condición dentro de la región (estrella).', '76%')}
<h3>7.4. Adecuación del modelo</h3>
{numerar(RES_VALID, inf_map)}
{fig('fig3_obs_pred.png', 4, 'Valores observados frente a predichos de la temperatura operativa.', '55%')}
{fig('fig4_residuos.png', 5, 'Diagnóstico de residuos: (a) residuos vs. predichos; (b) histograma; (c) Q–Q normal; (d) residuos en orden de registro.', '88%')}
{TAB_DIAG.replace('{n}', '9')}
{fig('fig6_interaccion.png', 6, 'Efecto de <i>T</i><sub>w</sub> sobre la <i>T</i><sub>op</sub> para distintos niveles de <i>T</i><sub>e</sub>; banda verde: confort invernal.', '68%')}
<h3>7.5. Contraste de hipótesis</h3>
<div class="tbl"><p class="cap"><b>Tabla 10.</b> Resumen del contraste de hipótesis (α = 0.05).</p>
<table><thead><tr><th class='l'>Hipótesis</th><th class='l'>Evidencia</th><th>Decisión</th></tr></thead><tbody>
<tr><td class='l'>H<sub>E1</sub>: efectos significativos del modelo</td><td class='l'><i>F</i> = {f(R['F'],1)}, <i>p</i> &lt; 0.001; <i>β</i><sub>1</sub>, <i>β</i><sub>2</sub>, <i>β</i><sub>22</sub>, <i>β</i><sub>12</sub> con <i>p</i> &lt; 0.001; <i>β</i><sub>11</sub> con <i>p</i> = {f(R['pt'][3],3)}</td><td>Se acepta (se rechaza H<sub>0</sub>)</td></tr>
<tr><td class='l'>H<sub>E2</sub>: máximo dentro de la región</td><td class='l'><i>λ</i><sub>1</sub> &lt; 0 &lt; <i>λ</i><sub>2</sub> → punto silla; <i>x</i><sub>1,s</sub> = {f(R['xs'][0],2)} &gt; 1</td><td>Se rechaza</td></tr>
<tr><td class='l'>H<sub>E3</sub>: <i>T</i><sub>op</sub> ≥ 20 °C en la región</td><td class='l'>Máximo estimado en la región = {f(R['ymax'],2)} °C</td><td>Se rechaza</td></tr>
<tr><td class='l'>Hipótesis general</td><td class='l'><i>R</i><sup>2</sup> = {f(R['R2'],3)}; <i>R</i><sup>2</sup><sub>pred</sub> = {f(R['R2pred'],3)}; supuestos razonablemente satisfechos</td><td>Se acepta</td></tr>
</tbody></table></div>

<h2 class="s" id="s8">VIII. Discusión</h2>{DISC}

<h2 class="s" id="s9">IX. Conclusiones</h2>{CONCL}

<h2 class="s" id="s10">X. Recomendaciones</h2>
<ol class="b">
<li>Mejorar la envolvente del ambiente (aislamiento de muros, techo y bajo losa; hermeticidad de puertas y ventanas) para reducir la dependencia de la temperatura interior respecto de la exterior.</li>
<li>Implementar un control de la caldera con curva de compensación climática que aumente <i>T</i><sub>w</sub> en las horas frías, donde su efecto es mayor.</li>
<li>Encender el sistema con anticipación a la franja de la mañana para aprovechar la inercia térmica de la losa.</li>
<li>No elevar la temperatura de entrada del agua por encima de los valores medidos sin verificar la temperatura superficial del piso, que ya se acerca al límite de confort de 29 °C.</li>
<li>En futuras investigaciones, aplicar un diseño central compuesto con niveles controlados de <i>T</i><sub>w</sub>, incorporar variables como radiación solar y caudal, y emplear modelos con retardos temporales o errores autocorrelacionados.</li>
</ol>

<h2 class="s" id="ref">Referencias</h2><div class="refs">{REFS_HTML}</div>

<h2 class="s" id="aA">Anexo A. Matriz de consistencia</h2>
<table class="mc"><thead><tr><th>Problemas</th><th>Objetivos</th><th>Hipótesis</th><th>Variables</th><th>Metodología</th></tr></thead><tbody>
<tr><td><b>General:</b> ¿Cómo influyen <i>T</i><sub>w</sub> y <i>T</i><sub>e</sub> en la <i>T</i><sub>op</sub> de un ambiente con piso radiante, modelada mediante MSR?</td>
<td><b>General:</b> Modelar la <i>T</i><sub>op</sub> en función de <i>T</i><sub>w</sub> y <i>T</i><sub>e</sub> mediante la MSR.</td>
<td><b>General:</b> <i>T</i><sub>w</sub> y <i>T</i><sub>e</sub> influyen significativamente en la <i>T</i><sub>op</sub> y la relación se representa con un modelo de 2.º orden.</td>
<td rowspan="4"><b>VI<sub>1</sub>:</b> <i>T</i><sub>w</sub> (°C)<br><b>VI<sub>2</sub>:</b> <i>T</i><sub>e</sub> (°C)<br><b>VD:</b> <i>T</i><sub>op</sub> (°C)</td>
<td rowspan="4"><b>Enfoque:</b> cuantitativo<br><b>Tipo:</b> aplicada<br><b>Nivel:</b> explicativo<br><b>Diseño:</b> no experimental longitudinal<br><b>Muestra:</b> {R['n']} registros<br><b>Instrumentos:</b> termohigrómetro de globo, sensores de temperatura, anemómetro<br><b>Análisis:</b> MSR, ANOVA, análisis canónico (GNU Octave)</td></tr>
<tr><td><b>PE1:</b> ¿Cuáles son los efectos lineales, cuadráticos y de interacción?</td><td><b>OE1:</b> Estimar y evaluar dichos efectos.</td><td><b>HE1:</b> Al menos un efecto es significativo.</td></tr>
<tr><td><b>PE2:</b> ¿Qué naturaleza tiene el punto estacionario?</td><td><b>OE2:</b> Determinar su ubicación y naturaleza.</td><td><b>HE2:</b> Es un máximo dentro de la región.</td></tr>
<tr><td><b>PE3:</b> ¿Cuál es la mejor condición y permite el confort?</td><td><b>OE3:</b> Identificar la mejor condición y contrastarla con el confort.</td><td><b>HE3:</b> Existe una condición con <i>T</i><sub>op</sub> ≥ 20 °C.</td></tr>
</tbody></table>

<h2 class="s" id="aB">Anexo B. Código fuente en GNU Octave</h2>
<p>Script <code>superficie_respuesta.m</code>, que lee <code>datos/datos_MSR.csv</code> y genera los resultados y las figuras.</p>
<pre>{esc(octave_code)}</pre>

<h2 class="s" id="aC">Anexo C. Salida de resultados</h2>
<p>Contenido del archivo <code>resultados/resultados.txt</code> generado por el script del Anexo B.</p>
<pre>{esc(octave_res)}</pre>
</body></html>"""

(DOC / "articulo.html").write_text(articulo, encoding="utf-8")
(DOC / "informe.html").write_text(informe, encoding="utf-8")

FOOT_ART = ('<div style="width:100%;font-family:Liberation Sans,Arial;font-size:7pt;color:#666;padding:0 17mm;display:flex;justify-content:space-between">'
            f'<span>Mamani Galindo, Ramos Yapo &amp; Salinas Mena · MSR aplicada a calefacción por piso radiante</span>'
            '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
FOOT_INF = ('<div style="width:100%;font-family:Liberation Sans,Arial;font-size:8pt;color:#666;padding:0 17mm;text-align:right">'
            '<span class="pageNumber"></span></div>')

def paginas_toc(pdf_path):
    """Busca en el PDF la página donde aparece cada título del índice."""
    from pypdf import PdfReader
    norm = lambda t: "".join(t.upper().split())
    pages = [norm(pg.extract_text() or "") for pg in PdfReader(str(pdf_path)).pages]
    res = {}
    for titulo, ancla in TOC:
        clave = norm(titulo)
        for i in range(2, len(pages)):
            if clave in pages[i]:
                res[ancla] = i + 1
                break
    return res


with sync_playwright() as p:
    import os
    exe = "/opt/pw-browsers/chromium"
    br = p.chromium.launch(executable_path=exe) if os.path.exists(exe) else p.chromium.launch()
    pg = br.new_page()
    pg.goto((DOC / "articulo.html").as_uri()); pg.wait_for_load_state("networkidle")
    pg.pdf(path=str(OUT / "Articulo_cientifico_MSR_piso_radiante.pdf"), format="A4", print_background=True,
           display_header_footer=True, header_template="<div></div>", footer_template=FOOT_ART,
           margin={"top": "18mm", "bottom": "18mm", "left": "17mm", "right": "17mm"})
    inf_pdf = OUT / "Informe_investigacion_MSR_piso_radiante.pdf"
    for paso in range(2):  # 2.ª pasada: con números de página en el índice
        if paso == 1:
            nums = paginas_toc(inf_pdf)
            html = informe
            for ancla, n in nums.items():
                html = html.replace(f'data-target="{ancla}"></span>', f'data-target="{ancla}">{n}</span>')
            (DOC / "informe.html").write_text(html, encoding="utf-8")
        pg.goto((DOC / "informe.html").as_uri()); pg.wait_for_load_state("networkidle")
        pg.pdf(path=str(inf_pdf), format="A4", print_background=True,
               display_header_footer=True, header_template="<div></div>", footer_template=FOOT_INF,
               margin={"top": "20mm", "bottom": "20mm", "left": "22mm", "right": "20mm"})
    br.close()
print("PDF generados en", OUT)
