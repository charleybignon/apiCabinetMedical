from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
import pymysql
from datetime import date, time, timedelta
import datetime  # Importez datetime pour la conversion

consults_router = APIRouter()

# Connexion à la base de données
conn = pymysql.connect(
    host="mysql-cabinet-gayrard-bignon.alwaysdata.net",
    user="354243",
    password="$iutinfo",
    database="cabinet-gayrard-bignon_db"
)

# Modèle de données pour une consultation
class Consultation(BaseModel):
    id_consult: int
    date_consult: date
    heure_consult: time
    duree_consult: int
    id_medecin: int
    id_usager: int

class ConsultationToCreate(BaseModel):
    date_consult: date
    heure_consult: time
    duree_consult: int
    id_medecin: int
    id_usager: int

# Fonction utilitaire pour vérifier l'existence d'un usager par ID
def user_exists(user_id: int) -> bool:
    query = "SELECT COUNT(*) FROM usager WHERE id_usager = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return result[0] > 0

# Fonction utilitaire pour vérifier l'existence d'un médecin par ID
def doctor_exists(doctor_id: int) -> bool:
    query = "SELECT COUNT(*) FROM medecin WHERE id_medecin = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (doctor_id,))
        result = cursor.fetchone()
        return result[0] > 0
    
def check_user_consultation_overlap(id_usager: int, date_consult: date, heure_consult: time, duree_consult: int) -> bool:
    start_time = heure_consult
    end_time = add_minutes_to_time(heure_consult, duree_consult)
    query = "SELECT COUNT(*) FROM consultation WHERE id_usager = %s AND date_consult = %s AND ((heure_consult <= %s AND (heure_consult + INTERVAL duree_consult MINUTE) > %s) OR (heure_consult >= %s AND heure_consult < %s))"
    with conn.cursor() as cursor:
        cursor.execute(query, (id_usager, date_consult, end_time, start_time, end_time, start_time))
        result = cursor.fetchone()
        return result[0] > 0

# Fonction utilitaire pour ajouter des minutes à un objet time
def add_minutes_to_time(t: time, minutes: int) -> time:
    new_minute = t.minute + minutes
    new_hour = t.hour + new_minute // 60
    new_minute = new_minute % 60
    return time(hour=new_hour, minute=new_minute)

# Fonction utilitaire pour vérifier les chevauchements de consultations pour un médecin
def check_doctor_consultation_overlap(id_medecin: int, date_consult: date, heure_consult: time, duree_consult: int) -> bool:
    start_time = heure_consult
    end_time = add_minutes_to_time(heure_consult, duree_consult)
    query = "SELECT COUNT(*) FROM consultation WHERE id_medecin = %s AND date_consult = %s AND ((heure_consult <= %s AND (heure_consult + INTERVAL duree_consult MINUTE) > %s) OR (heure_consult >= %s AND heure_consult < %s))"
    with conn.cursor() as cursor:
        cursor.execute(query, (id_medecin, date_consult, end_time, start_time, end_time, start_time))
        result = cursor.fetchone()
        return result[0] > 0

# API pour créer une consultation
@consults_router.post("/consultations/")
async def create_consultation(consultation: ConsultationToCreate):
    # Vérifier si l'usager existe
    if not user_exists(consultation.id_usager):
        raise HTTPException(status_code=404, detail="L'usager spécifié n'existe pas.")
    
    # Vérifier si le médecin existe
    if not doctor_exists(consultation.id_medecin):
        raise HTTPException(status_code=404, detail="Le médecin spécifié n'existe pas.")
    
    # Vérifier les chevauchements de consultations pour l'usager
    if check_user_consultation_overlap(consultation.id_usager, consultation.date_consult, consultation.heure_consult, consultation.duree_consult):
        raise HTTPException(status_code=409, detail="Cet usager a déjà une consultation qui chevauche avec la nouvelle consultation.")
    
    # Vérifier les chevauchements de consultations pour le médecin
    if check_doctor_consultation_overlap(consultation.id_medecin, consultation.date_consult, consultation.heure_consult, consultation.duree_consult):
        raise HTTPException(status_code=409, detail="Ce médecin a déjà une consultation qui chevauche avec la nouvelle consultation.")
    
    # Insertion de la consultation dans la base de données
    query = "INSERT INTO consultation (date_consult, heure_consult, duree_consult, id_medecin, id_usager) VALUES (%s, %s, %s, %s, %s)"
    values = (
        consultation.date_consult,
        consultation.heure_consult,
        consultation.duree_consult,
        consultation.id_medecin,
        consultation.id_usager
    )
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    
    return consultation

# API pour obtenir toutes les consultations
@consults_router.get("/consultations/", response_model=List[Consultation])
async def get_all_consultations():
    query = "SELECT id_consult, date_consult, heure_consult, duree_consult, id_medecin, id_usager FROM consultation"
    with conn.cursor() as cursor:
        cursor.execute(query)
        consultations = []
        for (id_consult, date_consult, heure_consult, duree_consult, id_medecin, id_usager) in cursor.fetchall():
            # Convertir datetime.timedelta en time
            heure_consult = datetime.datetime.min + heure_consult
            heure_consult = heure_consult.time()
            
            consultation = Consultation(
                id_consult=id_consult,
                date_consult=date_consult,
                heure_consult=heure_consult,
                duree_consult=duree_consult,
                id_medecin=id_medecin,
                id_usager=id_usager
            )
            consultations.append(consultation)
    return consultations

# API pour modifier une consultation par son ID
@consults_router.patch("/consultations/{consultation_id}")
async def update_consultation(consultation_id: int, duree_consult: int):
    query = "UPDATE consultation SET duree_consult = %s WHERE id_consult = %s"
    values = (duree_consult, consultation_id)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    return {"message": "Consultation mise à jour avec succès"}

# API pour obtenir une consultation par son ID
@consults_router.get("/consultations/{consultation_id}", response_model=Consultation)
async def get_consultation(consultation_id: int):
    query = "SELECT * FROM consultation WHERE id_consult = %s"
    values = (consultation_id,)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        row = cursor.fetchone()
        if row:
            # Convertir datetime.timedelta en time
            heure_consult = datetime.datetime.min + row[2]
            heure_consult = heure_consult.time()
            
            consultation = Consultation(
                id_consult=row[0],
                date_consult=row[1],
                heure_consult=heure_consult,
                duree_consult=row[3],
                id_medecin=row[4],
                id_usager=row[5]
            )
            return consultation
        else:
            raise HTTPException(status_code=404, detail="Consultation non trouvée")
# API pour supprimer une consultation par son ID
@consults_router.delete("/consultations/{consultation_id}")
async def delete_consultation(consultation_id: int):
    query = "DELETE FROM consultation WHERE id_consult = %s"
    values = (consultation_id,)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    return {"message": "Consultation supprimée avec succès"}
