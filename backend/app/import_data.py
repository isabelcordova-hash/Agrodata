"""Transactional, idempotent PostgreSQL import. Run after Alembic."""
import json
from pathlib import Path
from sqlalchemy import delete, select, func
from .db import Session
from .models import Observation, District
ROOT = Path(__file__).resolve().parents[2]
def read(name): return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))
def main():
    observation_count = 0
    with Session.begin() as db:
        db.execute(delete(Observation)); db.execute(delete(District))
        for filename, kind in [("historial_anual.json","history"),("historial_departamento.json","history"),("predicciones_anual.json","forecast"),("predicciones_departamento.json","forecast")]:
            rows=[]
            for r in read(filename):
                year=next(v for k,v in r.items() if k.startswith("A") and isinstance(v,int))
                rows.append(dict(kind=kind,year=year,crop=r["PRODUCTO"],department=r.get("DEPARTAMENTO",""),yield_value=r["rendimiento_promedio"],production=r["produccion_total"],records=r["registros"]))
            db.bulk_insert_mappings(Observation,rows)
            observation_count += len(rows)
        source=read("scoring_distrito.json")
        bounds={c:(min(r["score"] for r in source if r["PRODUCTO"]==c),max(r["score"] for r in source if r["PRODUCTO"]==c)) for c in {r["PRODUCTO"] for r in source}}
        rows=[]
        for r in source:
            lo,hi=bounds[r["PRODUCTO"]]
            rows.append(dict(crop=r["PRODUCTO"],department=r["DEPARTAMENTO"],name=r["DISTRITO"],yield_value=r["valor_promedio"],score_raw=r["score"],score=(r["score"]-lo)/(hi-lo) if hi>lo else 1,stability=r["estabilidad"],records=r["registros"]))
        db.bulk_insert_mappings(District,rows)
        # Derived top ten are validated against the authoritative scoring source.
        top=read("top_distritos_por_cultivo.json")
        keys={(r["PRODUCTO"],r["DEPARTAMENTO"],r["DISTRITO"]) for r in source}
        assert all((r["PRODUCTO"],r["DEPARTAMENTO"],r["DISTRITO"]) in keys for group in top.values() for r in group)
    print(f"Imported {observation_count:,} observations and {len(source):,} district scores; top-ten source validated.")
if __name__ == "__main__": main()
