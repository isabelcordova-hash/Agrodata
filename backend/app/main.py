import secrets
import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import httpx
import jwt
from fastapi import FastAPI, Depends, HTTPException, Query, Response, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from .db import Session, settings
from .models import User, Observation, District
app = FastAPI(title="AgroData API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["GET","POST"], allow_headers=["Content-Type"])
hasher=PasswordHash.recommended()
google_keys=jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs", cache_keys=True)
def session():
    with Session() as db: yield db
def issue(response, user):
    token=jwt.encode({"sub":str(user.id),"exp":datetime.now(timezone.utc)+timedelta(hours=8)},settings.jwt_secret,algorithm="HS256")
    response.set_cookie("agrodata_session",token,httponly=True,samesite="lax",max_age=28800)
def current(request: Request, db=Depends(session)):
    try:
        payload=jwt.decode(request.cookies.get("agrodata_session",""),settings.jwt_secret,algorithms=["HS256"])
        user=db.get(User,int(payload["sub"]))
        if not user: raise ValueError()
        return user
    except (jwt.PyJWTError,ValueError,KeyError): raise HTTPException(401,"Inicia sesión para continuar")
class Credentials(BaseModel):
    email: str = Field(min_length=5,max_length=254,pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=10,max_length=128)
    name: str = Field(default="Investigador",min_length=1,max_length=100)
@app.get("/health")
def health(db=Depends(session)):
    db.execute(select(1)); return {"status":"ok"}
@app.post("/auth/register",status_code=201)
def register(body: Credentials,response: Response,db=Depends(session)):
    user=User(email=body.email.lower().strip(),name=body.name,password_hash=hasher.hash(body.password))
    db.add(user)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"El correo ya está registrado")
    issue(response,user); return {"name":user.name,"email":user.email}
@app.post("/auth/login")
def login(body: Credentials,response: Response,db=Depends(session)):
    user=db.scalar(select(User).where(User.email==body.email.lower().strip()))
    if not user or not user.password_hash or not hasher.verify(body.password,user.password_hash): raise HTTPException(401,"Credenciales incorrectas")
    issue(response,user); return {"name":user.name,"email":user.email}
@app.get("/auth/me")
def me(user=Depends(current)): return {"name":user.name,"email":user.email}
@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("agrodata_session"); return {"ok":True}
@app.get("/auth/google")
def google():
    if not settings.google_client_id or not settings.google_client_secret: raise HTTPException(503,"Configura las credenciales OAuth de Google en backend/.env")
    state=secrets.token_urlsafe(32)
    response=RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?"+urlencode({"client_id":settings.google_client_id,"redirect_uri":settings.google_redirect_uri,"response_type":"code","scope":"openid email profile","state":state}))
    response.set_cookie("oauth_state",state,httponly=True,samesite="lax",max_age=600)
    return response
@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str="", state: str="",db=Depends(session)):
    expected=request.cookies.get("oauth_state")
    if not expected or not secrets.compare_digest(state,expected): raise HTTPException(400,"Estado OAuth inválido")
    async with httpx.AsyncClient(timeout=15) as client:
        token=await client.post("https://oauth2.googleapis.com/token",data={"code":code,"client_id":settings.google_client_id,"client_secret":settings.google_client_secret,"redirect_uri":settings.google_redirect_uri,"grant_type":"authorization_code"})
        if token.status_code!=200: raise HTTPException(400,"Google no pudo autorizar la sesión")
        info=await client.get("https://openidconnect.googleapis.com/v1/userinfo",headers={"Authorization":"Bearer "+token.json()["access_token"]})
    if info.status_code!=200 or not info.json().get("email_verified"): raise HTTPException(400,"Google no verificó el correo")
    data=info.json()
    try:
        id_token=token.json()["id_token"]
        signing_key=await asyncio.to_thread(google_keys.get_signing_key_from_jwt,id_token)
        claims=jwt.decode(id_token,signing_key.key,algorithms=["RS256"],audience=settings.google_client_id,issuer=["https://accounts.google.com","accounts.google.com"])
        if claims["sub"]!=data["sub"]: raise ValueError()
    except (jwt.PyJWTError,ValueError,KeyError): raise HTTPException(400,"Token de identidad de Google inválido")
    user=db.scalar(select(User).where(User.google_sub==data["sub"]))
    if not user:
        if db.scalar(select(User).where(User.email==data["email"].lower())): raise HTTPException(409,"Este correo ya tiene una cuenta local; inicia sesión con tu contraseña")
        user=User(email=data["email"].lower(),name=data.get("name","Investigador"),google_sub=data["sub"]); db.add(user); db.commit()
    response=RedirectResponse(settings.frontend_url); response.delete_cookie("oauth_state"); issue(response,user); return response
@app.get("/api/metadata")
def metadata(crop: str="PAPA",db=Depends(session),user=Depends(current)):
    crops=db.scalars(select(Observation.crop).distinct().order_by(Observation.crop)).all()
    departments=db.scalars(select(Observation.department).where(Observation.crop==crop,Observation.kind=="history",Observation.department!="").distinct().order_by(Observation.department)).all()
    return {"crops":crops,"departments":departments,"districts":db.scalar(select(func.count()).select_from(District)),"crop_count":len(crops),"model":"XGBoost","r2":None,"wmape":None}
def serialize(row): return {column.name:getattr(row,column.name) for column in row.__table__.columns}
@app.get("/api/overview")
def overview(crop: str="PAPA",department: str="",db=Depends(session),user=Depends(current)):
    rows=db.scalars(select(Observation).where(Observation.crop==crop,Observation.department==department).order_by(Observation.year)).all()
    history=[r for r in rows if r.kind=="history"]
    recent=history[-5:]; baseline=sum(r.yield_value for r in recent)/len(recent) if recent else None
    forecast=next((r for r in rows if r.kind=="forecast" and r.year==2027),None)
    return {"history":[serialize(r) for r in history],"forecast":[serialize(r) for r in rows if r.kind=="forecast"],"baseline":baseline,"baseline_years":[r.year for r in recent],"variation":(forecast.yield_value/baseline-1)*100 if forecast and baseline else None,"outlier":bool(history and baseline and abs(history[-1].yield_value/baseline-1)>.3)}
@app.get("/api/rankings")
def rankings(crop: str="PAPA",department: str="",page: int=Query(1,ge=1),size: int=Query(10,ge=1,le=100),db=Depends(session),user=Depends(current)):
    conditions=[District.crop==crop]
    if department: conditions.append(District.department==department)
    count=db.scalar(select(func.count()).select_from(District).where(*conditions))
    rows=db.scalars(select(District).where(*conditions).order_by(District.score.desc(),District.id).offset((page-1)*size).limit(size)).all()
    return {"items":[serialize(r) for r in rows],"total":count,"page":page,"size":size}
@app.get("/api/observations")
def observations(crop: str="PAPA",department: str="",page: int=Query(1,ge=1),size: int=Query(20,ge=1,le=100),db=Depends(session),user=Depends(current)):
    conditions=[Observation.crop==crop,Observation.department==department]
    count=db.scalar(select(func.count()).select_from(Observation).where(*conditions))
    rows=db.scalars(select(Observation).where(*conditions).order_by(Observation.year,Observation.kind).offset((page-1)*size).limit(size)).all()
    return {"items":[serialize(r) for r in rows],"total":count,"page":page,"size":size}
