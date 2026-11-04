# MSR aplicada a calefacción por piso radiante

Curso: Metodología de la Investigación  
Integrantes: Mamani Galindo Renzo Gabriel · Ramos Yapo Aquiles Taylor  
Docente asesor: Ing. Salinas Mena Mateo Alejandro (nombrado, Ing. Mecánico Electricista)

## Entregables
- `pdf/Articulo_cientifico_MSR_piso_radiante.pdf`: artículo científico (formato para revista indexada en Scopus).
- `pdf/Informe_investigacion_MSR_piso_radiante.pdf`: informe de investigación (carátula, índice, problema, objetivos, hipótesis, marco teórico, metodología, resultados, discusión, conclusiones, recomendaciones y anexos).

## Estructura
- `proyecto_octave/`: proyecto original (datos, script `superficie_respuesta.m`, resultados y figuras de Octave).
- `analisis/analisis_msr.py`: verificación del modelo en Python, diagnósticos adicionales y figuras para publicación (`figuras/`).
- `documentos/`: plantillas HTML/CSS y `construir_pdfs.py`, que genera los PDF.

## Regenerar
```bash
pip install numpy pandas scipy matplotlib openpyxl playwright pypdf
python3 analisis/analisis_msr.py
python3 documentos/construir_pdfs.py
```
