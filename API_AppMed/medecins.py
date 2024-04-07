from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
import pymysql

medecins_router = APIRouter()

# Connexion à la base de données
conn = pymysql.connect(
    host="mysql-cabinet-gayrard-bignon.alwaysdata.net",
    user="354243",
    password="$iutinfo",
    database="cabinet-gayrard-bignon_db"
)

# Modèle de données pour un médecin
class Medecin(BaseModel):
    id_medecin: int
    civilite: str
    nom: str
    prenom: str

class MedecinToCreate(BaseModel):
    civilite: str
    nom: str
    prenom: str

# API pour créer un médecin
@medecins_router.post("/medecins/")
async def create_medecin(medecin: MedecinToCreate):
    query = "INSERT INTO medecin (civilite, nom, prenom) VALUES (%s, %s, %s)"
    values = (medecin.civilite, medecin.nom, medecin.prenom)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    return medecin

# API pour obtenir tous les médecins
@medecins_router.get("/medecins/", response_model=List[Medecin])
async def get_all_medecins():
    query = "SELECT id_medecin, civilite, nom, prenom FROM medecin"
    with conn.cursor() as cursor:
        cursor.execute(query)
        medecins = []
        for (id_medecin, civilite, nom, prenom) in cursor.fetchall():
            medecin = Medecin(id_medecin=id_medecin, civilite=civilite, nom=nom, prenom=prenom)
            medecins.append(medecin)
    return medecins

# API pour modifier un médecin par son ID
@medecins_router.patch("/medecins/{medecin_id}")
async def update_medecin(medecin_id: int, nom: str):
    query = "UPDATE medecin SET nom = %s WHERE id_medecin = %s"
    values = (nom, medecin_id)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    return {"message": "Medecin mis à jour avec succès"}

# API pour obtenir un médecin par son ID
@medecins_router.get("/medecins/{medecin_id}", response_model=Medecin)
async def get_medecin(medecin_id: int):
    query = "SELECT * FROM medecin WHERE id_medecin = %s"
    values = (medecin_id,)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        row = cursor.fetchone()
        if row:
            medecin = Medecin(id_medecin=row[0], civilite=row[1], nom=row[2], prenom=row[3])
            return medecin
        else:
            raise HTTPException(status_code=404, detail="Medecin non trouvé")

# API pour supprimer un médecin par son ID
@medecins_router.delete("/medecins/{medecin_id}")
async def delete_medecin(medecin_id: int):
    query = "DELETE FROM medecin WHERE id_medecin = %s"
    values = (medecin_id,)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    return {"message": "Medecin supprimé avec succès"}
