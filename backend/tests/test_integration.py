"""Integration checks against the migrated and seeded local PostgreSQL database."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, delete, func
from app.main import app
from app.db import Session
from app.models import User, Observation, District
@pytest.fixture
def client():
    email=f"qa-{uuid.uuid4().hex}@example.test"
    with TestClient(app) as c:
        response=c.post("/auth/register",json={"email":email,"password":"AgroData-test-2026","name":"QA"})
        assert response.status_code==201
        yield c
    with Session.begin() as db: db.execute(delete(User).where(User.email==email))
def test_requires_authentication():
    with TestClient(app) as c:
        assert c.get("/api/overview").status_code==401
        assert c.get("/auth/google/callback?code=fake&state=fake").status_code==400
def test_baseline_and_projection(client):
    data=client.get("/api/overview?crop=PAPA").json()
    last5=data["history"][-5:]
    assert len(last5)==5
    assert data["baseline"]==pytest.approx(sum(r["yield_value"] for r in last5)/5)
    prediction=next(r for r in data["forecast"] if r["year"]==2027)
    assert data["variation"]==pytest.approx((prediction["yield_value"]/data["baseline"]-1)*100)
def test_cascade_and_rankings(client):
    meta=client.get("/api/metadata?crop=PAPA").json()
    with Session() as db:
        expected=db.scalars(select(Observation.department).where(Observation.crop=="PAPA",Observation.kind=="history",Observation.department!="").distinct().order_by(Observation.department)).all()
    assert meta["departments"]==expected
    region=expected[0]
    first=client.get("/api/rankings",params={"crop":"PAPA","department":region,"size":2}).json()
    second=client.get("/api/rankings",params={"crop":"PAPA","department":region,"size":2,"page":2}).json()
    assert all(r["department"]==region and r["crop"]=="PAPA" and 0<=r["score"]<=1 for r in first["items"])
    assert not {r["id"] for r in first["items"]}&{r["id"] for r in second["items"]}
    assert client.get("/api/rankings?page=0").status_code==422
    assert client.get("/api/rankings?size=101").status_code==422
def test_auth_lifecycle(client):
    user=client.get("/auth/me").json()
    assert client.post("/auth/login",json={"email":user["email"],"password":"incorrect-password"}).status_code==401
    assert client.post("/auth/login",json={"email":user["email"],"password":"AgroData-test-2026"}).status_code==200
    assert client.post("/auth/register",json={"email":user["email"],"password":"AgroData-test-2026"}).status_code==409
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code==401
def test_import_counts():
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(Observation))==5205
        assert db.scalar(select(func.count()).select_from(District))==12050
        assert db.scalar(select(func.min(District.score)))==0
        assert db.scalar(select(func.max(District.score)))==1

def test_departments_exclude_forecasts_and_handle_missing_history(client):
    import json
    from pathlib import Path
    source=json.loads((Path(__file__).resolve().parents[2]/"historial_departamento.json").read_text(encoding="utf-8"))
    crops=client.get("/api/metadata").json()["crops"]
    for crop in crops:
        expected=sorted({r["DEPARTAMENTO"] for r in source if r["PRODUCTO"]==crop})
        actual=client.get("/api/metadata",params={"crop":crop}).json()["departments"]
        assert actual==expected
    missing=client.get("/api/metadata",params={"crop":"CULTIVO_SIN_HISTORIAL"})
    assert missing.status_code==200
    assert missing.json()["departments"]==[]
    data=client.get("/api/overview",params={"crop":"CULTIVO_SIN_HISTORIAL"}).json()
    assert data["history"]==[]
    assert data["baseline"] is None
