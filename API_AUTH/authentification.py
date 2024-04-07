from fastapi import APIRouter, HTTPException, Depends, Request, Response
import pymysql
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

# Création du routeur pour les routes d'authentification
auth_router = APIRouter()

# Connexion à la base de données MySQL
conn = pymysql.connect(
    host="mysql-cabinet-gayrard-bignon.alwaysdata.net",
    user="354243",
    password="$iutinfo",
    database="cabinet-gayrard-bignon_db"
)

# Fonction pour vérifier les informations d'identification dans la base de données MySQL
def vérifier_informations_identification(login: str, mot_de_passe: str):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connexion WHERE login = %s AND password = %s", (login, mot_de_passe))
    utilisateur = cursor.fetchone()
    cursor.close()
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Informations d'identification invalides")
    return utilisateur[0]

# Fonction pour vérifier le token JWT et extraire le login
def vérifier_token(request: Request):
    try:
        token = request.headers["Authorization"]
        payload = jwt.decode(token, "clé_secrète", algorithms=["HS256"])
        return payload["login"]
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token invalide")

# Endpoint pour l'authentification et la génération de token JWT
@auth_router.post("/login")
def login(credentials: dict, response: Response):
    login_validé = vérifier_informations_identification(credentials.get('login'), credentials.get('password'))
    token_expiration = datetime.utcnow() + timedelta(minutes=15)
    token = jwt.encode({"login": login_validé, "exp": token_expiration}, "clé_secrète", algorithm="HS256")
    response.headers["Authorization"] = f"Bearer {token}"
    return {"token": token}

@auth_router.get("/login")
def get_login(token: str = Depends(vérifier_token)):
    return {"login": token}



