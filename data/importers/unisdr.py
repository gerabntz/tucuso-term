"""UNISDR 2009 DRR terminology importer (ES definitions + official EN pairs).

License: the publication states "Se puede citar o reimprimir libremente esta
publicación, pero se solicita que se incluya la fuente" — free reuse with
attribution. Source attribution travels on every row.

The ES→EN map below is transcribed from the document's own section
"Lista de los términos con su equivalente en Inglés" (pp. 36–38).
"""
import argparse
import re
from pathlib import Path

from data.importers.covenin import verify_sha256, import_rows

SOURCE = "unisdr-2009"

TERM_MAP = {
    "Adaptación al cambio climático": "adaptation",
    "Amenaza": "hazard",
    "Amenaza biológica": "biological hazard",
    "Amenaza geológica": "geological hazard",
    "Amenaza hidrometeorológica": "hydrometeorological hazard",
    "Amenaza natural": "natural hazard",
    "Amenaza socio-natural": "socio-natural hazard",
    "Amenaza tecnológica": "technological hazard",
    "Cambio climático": "climate change",
    "Capacidad": "capacity",
    "Capacidad de afrontamiento": "coping capacity",
    "Código de construcción": "building code",
    "Concientización/sensibilización pública": "public awareness",
    "Degradación ambiental": "environmental degradation",
    "Desarrollo de capacidades": "capacity development",
    "Desarrollo sostenible": "sustainable development",
    "Desastre": "disaster",
    "El Niño Oscilación del Sur (ENOS)": "El Niño-Southern Oscillation phenomenon",
    "Estudio del impacto ambiental": "environmental impact assessment",
    "Evaluación del riesgo": "risk assessment",
    "Gases de efecto invernadero": "greenhouse gases",
    "Grado de exposición": "exposure",
    "Gestión correctiva del riesgo de desastres": "corrective disaster risk management",
    "Gestión de emergencias": "emergency management",
    "Gestión del riesgo": "risk management",
    "Gestión del riesgo de desastres": "disaster risk management",
    "Gestión prospectiva del riesgo de desastres": "prospective disaster risk management",
    "Instalaciones vitales": "critical facilities",
    "Medidas estructurales": "structural measures",
    "Medidas no estructurales": "non-structural measures",
    "Mitigación": "mitigation",
    "Plan para la reducción del riesgo de desastres": "disaster risk reduction plan",
    "Planificación de contingencias": "contingency planning",
    "Planificación/ordenamiento territorial": "land-use planning",
    "Plataforma nacional para la reducción del riesgo de desastres":
        "national platform for disaster risk reduction",
    "Preparación": "preparedness",
    "Prevención": "prevention",
    "Pronóstico": "forecast",
    "Recuperación": "recovery",
    "Reducción del riesgo de desastres": "disaster risk reduction",
    "Reforzamiento": "retrofitting",
    "Respuesta": "response",
    "Resiliencia": "resilience",
    "Riesgo": "risk",
    "Riesgo aceptable": "acceptable risk",
    "Riesgo de desastres": "disaster risk",
    "Riesgo intensivo": "intensive risk",
    "Riesgo extensivo": "extensive risk",
    "Riesgo residual": "residual risk",
    "Servicios de emergencia": "emergency services",
    "Servicios de los ecosistemas": "ecosystem services",
    "Sistema de alerta temprana": "early warning system",
    "Transferencia del riesgo": "risk transfer",
    "Vulnerabilidad": "vulnerability",
}

MIN_ENTRIES = 45


def parse_unisdr(filepath):
    lines = [ln.rstrip() for ln in
             Path(filepath).read_text(encoding="utf-8").splitlines()]
    # body region: after the cover garbage, before the equivalence list
    start = next(i for i, ln in enumerate(lines)
                 if i > 400 and ln.strip() == "Adaptación al cambio climático")
    end = next(i for i, ln in enumerate(lines)
               if ln.startswith("*Términos nuevos"))
    body = lines[start:end]

    terms = {t.rstrip("*"): en for t, en in TERM_MAP.items()}
    # case-tolerant lookup for headings like "Grado de Exposición"
    lookup = {t.lower(): t for t in terms}

    entries = []
    i = 0
    while i < len(body):
        key = body[i].strip().rstrip("*").lower()
        if key in lookup:
            es = lookup[key]
            j = i + 1
            def_lines = []
            while j < len(body):
                ln = body[j].strip()
                if ln.startswith("Comentario:") or ln.rstrip("*").lower() in lookup:
                    break
                if ln and not re.fullmatch(r"\d+", ln):
                    def_lines.append(ln)
                j += 1
            definition = re.sub(r"\s+", " ", " ".join(def_lines)).strip()
            if definition:
                entries.append((es, terms[es], definition))
            # skip past the comment to avoid re-matching cross-references
            while j < len(body) and not body[j].strip().rstrip("*").lower() in lookup:
                j += 1
            i = j
        else:
            i += 1

    seen = {}
    for es, en, definition in entries:   # keep the longest definition per term
        if es not in seen or len(definition) > len(seen[es][2]):
            seen[es] = (es, en, definition)
    result = list(seen.values())
    if len(result) < MIN_ENTRIES:
        raise ValueError(f"Expected at least {MIN_ENTRIES} entries, got {len(result)}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Import UNISDR 2009 terminology")
    parser.add_argument("db_path")
    args = parser.parse_args()
    repo_root = Path(__file__).parents[2]
    source_file = repo_root / "data" / "sources" / "unisdr-terminology-2009-es.txt"
    verify_sha256(source_file)
    entries = parse_unisdr(source_file)
    rows = [dict(source_ref=None, text=es, definition=definition, en_equiv=en,
                 example=None) for es, en, definition in entries]
    import_rows(args.db_path, rows, SOURCE)
    print(f"Imported {len(rows)} entries from {SOURCE}")


if __name__ == "__main__":
    main()
