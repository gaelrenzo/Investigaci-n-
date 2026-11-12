# Prácticas pre-profesionales pagadas: Puno → Arequipa → Zona norte

Búsqueda al **12-nov-2026**. Criterios: **pre**-profesionales (estudiante, no egresado), **pagadas** (subvención) e inicio **antes de agosto 2027**.
Carrera asumida: **Ing. Mecánica Eléctrica** y afines (eléctrica, mecánica, energías). Si es otra, cámbiala con `--carrera`.

> ⚠️ Desde la nube no pude entrar a las webs de empleo (la red bloquea computrabajo, practicas.pe, gob.pe…). Esta lista sale de buscadores web.
> **Confirma cada fecha en la web oficial antes de postular.** Para tener la lista completa y al día, corre el script en tu PC (abajo).

## 1. Puno (prioridad)
| Entidad | Puesto / carrera | Pago | Cierre | Estado |
|---|---|---|---|---|
| Electro Puno – U. Zonal Ananea | Practicante, Sub Gerencia de Coord. de Zonales | Subvención (DL 1401) | 09-nov-2026 | Cerró hace 3 días. Atento a la **ampliación** |
| Electro Puno – Puno | Ing. Mecánica Eléctrica / Eléctrica / Mecatrónica / Energías Renovables | Subvención | 05-nov-2026 | Cerrada (pedía **egresado**) |
| SUNARP – O.R. Juliaca | Practicante | ~S/ 1,130 | ~19-nov-2026 | **Posiblemente vigente** (Derecho/Adm.) |
| INEI Puno (PRAC PRE 017) | Pre-profesional | **S/ 1,130/mes** | Hasta 31-dic-2026, renovable | Proceso de mayo–junio (ya hecho) |
| practicas.pe Puno | PMO / Planeamiento y Control (8.°–10.° ciclo; Sistemas, Economía, Adm.) | No indica | Sin fecha | Revisar |

👉 **Electro Puno es tu mejor opción en Puno para tu carrera.** Saca convocatorias casi cada mes (Juliaca, Puno, Ananea, Moho) y sus "ampliaciones" se publican en
gob.pe/institucion/electropuno/informes-publicaciones.

## 2. Arequipa
No encontré nada **vigente** para Ing. Eléctrica o Mecánica. Las que salieron ya cerraron:
- Cerro Verde: Programa de Practicantes 2027 (cerró el 11-nov-2026, y era para técnicos).
- SENCICO Arequipa, Municipalidad Provincial, GRTC y ESSALUD: cerradas (S/ 1,130 en las públicas).
- Cruz del Sur (Uchumayo): mantenimiento, Ing. Mecánica/Industrial, pero pide **egresado**.
- Faltan por revisar a mano: **SEAL, EGASA, Cerro Verde y Southern** (sus portales de talento).

## 3. Zona norte
| Entidad | Región | Puesto | Pago | Cierre |
|---|---|---|---|---|
| Universidad de Trujillo | La Libertad | 3 practicantes (carrera no indicada) | Subvención | **18-nov-2026** |
| ORI Cajamarca (Conv. 086-2026) | Cajamarca | Practicante | ~S/ 1,130 | **23-nov-2026** |
| DANPER | La Libertad | Practicante (cadena de suministro / agro) | Privada | Sin fecha |
| Minera Poderosa "Talentos de Oro 2027" | La Libertad | Pre-profesional, ciclos VII–XI | Pagada | 25-oct-2026 (cerrada) |
| Volcan "Potencia tu Talento 2027" | Varias | Prácticas 2027 | Pagada | Sin fecha: **revisar ya** |
| Minera Boroo "Talentos 2027" | La Libertad | Estudiantes y egresados | Pagada | Sin fecha: **revisar ya** |

## Fuentes
- https://www.practicas.pe/profesionales-preprofesionales-ingenieria-electrica-puno-111-21.html
- https://www.practicas.pe/preprofesionales-en-puno-21.html
- https://www.perutrabajos.com/institucion-ELECTRO-PUNO-551.html
- https://www.gob.pe/institucion/electropuno/informes-publicaciones/8347374-convocatoria-de-practicas-profesionales-en-el-departamento-de-excelencia-operacional-puno
- https://www.inei.gob.pe/media/convocatoria_cas/BASES_PRAC_PRE___017_PUNO.pdf
- https://www.convocatoriasdetrabajo.com/oportunidad-laboral-practicas-sunarp-derecho-noviembre-2026-638507.html
- https://www.practicas.pe/preprofesionales-en-arequipa-4.html
- https://www.practicas.pe/pre-profesional-region-cajamarca-6.html
- https://www.practicas.pe/pre-profesional-en-caja-trujillo-205.html
- https://www.practicas.pe/oferta-convocatoria-practicas-pre-profesionales-programa-talentos-oro-minera-poderosa-la-libertad-69975.html
- https://www.practicas.pe/convocatoria-practicas-pre-y-profesionales-minera-boroo-septiembre-2026-11480.html
- https://mineriayproyectos.com/mineria/2026/09/29/volcan-practicas-profesionales-2027/

## Correr el scraper en tu PC
```bash
pip install requests beautifulsoup4
python3 scraper_practicas.py --carrera "mecanica electrica|electrica|mecanica|energ" --solo-pagadas
```
Revisa practicas.pe, perutrabajos, convocatoriasdetrabajo, Computrabajo y Bumeran por región (Puno → Arequipa → norte).
Descarta los avisos que piden egresado o bachiller y los que cierran después de agosto 2027.
Saca `practicas_resultados.csv` y `.md` ordenados por región, pago y fecha de cierre.
Opciones: `--incluir-cerradas` y `--pausa 2` (más lento, para no saturar las webs).
Nota: no pude probarlo contra las webs reales por el bloqueo de red; si alguna fuente devuelve 0 avisos, avísame y ajusto el parser.
