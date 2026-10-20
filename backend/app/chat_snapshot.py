"""Emit a read-only agricultural snapshot for the local Next.js chatbot."""
import json
from sqlalchemy import select
from .db import Session
from .models import Observation, District

def main():
    result = {name: [] for name in ["historial_anual.json", "historial_departamento.json", "predicciones_anual.json", "predicciones_departamento.json", "scoring_distrito.json"]}
    with Session() as db:
        for row in db.scalars(select(Observation).order_by(Observation.year, Observation.crop, Observation.department)):
            filename = ("historial" if row.kind == "history" else "predicciones") + ("_departamento.json" if row.department else "_anual.json")
            item = {"ANO": row.year, "PRODUCTO": row.crop, "rendimiento_promedio": row.yield_value, "produccion_total": row.production}
            if row.department:
                item["DEPARTAMENTO"] = row.department
            result[filename].append(item)
        for row in db.scalars(select(District)):
            result["scoring_distrito.json"].append({"PRODUCTO": row.crop, "DEPARTAMENTO": row.department, "DISTRITO": row.name, "valor_promedio": row.yield_value, "score": row.score_raw, "registros": row.records})
    print(json.dumps(result, ensure_ascii=True))

if __name__ == "__main__":
    main()
