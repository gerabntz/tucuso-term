# Pendientes (2026-07-05)

## Contenido
- [ ] **Importar la base de datos definitiva cuando esté lista** (corpus TT_2 del
  equipo terminológico, empezando por Seguridad alimentaria). El modelo de ficha
  ya está soportado (dominio, subdominio, variaciones, no confundir, inf.
  lingüística, pronunciación, acepciones múltiples, equivalentes multilengua).
  Hará falta un importador nuevo estilo `data/importers/` que lea el xlsx.
- [ ] Revisión humana de las categorías asignadas por máquina a los 105 seeds
  (`data/importers/domains.py` — editable a mano).
- [ ] Llenar `pronunciation`/`ling_info` de los términos existentes vía
  correcciones (quórum de 2 revisores).

## Operación
- [ ] Reclutar ≥2 revisores bilingües e invitarlos: `python -m server.reviewer_cli
  invite <alias> data/tucuso.db` (runbook §Reviewers).
- [ ] Decidir capa de selección de idioma (¿equivalentes listados o filtro por
  lengua?) — debate abierto Sharly/Gera.

## Marca e infraestructura
- [ ] Diseñar logo (hoy: icono provisional `T⇄` en `web/static/icon.svg`).
- [ ] Comprar dominio personalizado y apuntarlo a PythonAnywhere (CNAME; el plan
  free no admite dominios propios — evaluar plan Hacker ~$5/mes o migrar).
- [ ] Backups programados de `data/tucuso.db` (hoy: copia manual).

## Ideas aparcadas
- "Mot du jour" / término del día (descartado por ahora).
- App móvil nativa: el export JSON/CSV ya es la tubería de contenido futura.
