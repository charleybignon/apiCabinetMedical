from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
from typing import Optional
import pymysql
from datetime import date, time

patients_router = APIRouter()

# Connexion à la base de données
conn = pymysql.connect(
    host="mysql-cabinet-gayrard-bignon.alwaysdata.net",
    user="354243",
    password="$iutinfo",
    database="cabinet-gayrard-bignon_db"
)

# Modèle de données pour un patient
class Patient(BaseModel):
    id_usager: int
    civilite: str
    nom: str
    prenom: str
    sexe: str
    adresse: str
    code_postal: str
    ville: str
    date_nais: date
    lieu_nais: str
    num_secu: str
    id_medecin: Optional[int] = None

class PatientToCreate(BaseModel):
    civilite: str
    nom: str
    prenom: str
    sexe: str
    adresse: str
    code_postal: str
    ville: str
    date_nais: date
    lieu_nais: str
    num_secu: str
    id_medecin: Optional[int] = None

@patients_router.post("/usagers/")
async def create_patient(patient: PatientToCreate):
    # Vérifier si le numéro de sécurité sociale existe déjà
    query_check_duplicate = "SELECT id_usager FROM usager WHERE num_secu = %s"
    with conn.cursor() as cursor:
        cursor.execute(query_check_duplicate, (patient.num_secu,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Le numéro de sécurité sociale existe déjà.")
    
    # Vérifier si l'id_medecin est fourni et s'il correspond à un médecin existant
    if patient.id_medecin is not None:
        query_check_doctor = "SELECT id_medecin FROM medecin WHERE id_medecin = %s"
        with conn.cursor() as cursor:
            cursor.execute(query_check_doctor, (patient.id_medecin,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Le médecin spécifié n'existe pas.")
    
    # Construire la requête d'insertion en tenant compte de la possibilité de laisser id_medecin vide
    query_insert_patient = """
        INSERT INTO usager (civilite, nom, prenom, sexe, adresse, code_postal, ville, date_nais, lieu_nais, num_secu, id_medecin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    # Créer un tuple de valeurs pour l'insertion
    values = (
        patient.civilite, patient.nom, patient.prenom, patient.sexe,
        patient.adresse, patient.code_postal, patient.ville, patient.date_nais,
        patient.lieu_nais, patient.num_secu, patient.id_medecin  # id_medecin peut être None
    )
    
    # Exécuter la requête d'insertion
    with conn.cursor() as cursor:
        cursor.execute(query_insert_patient, values)
        conn.commit()
    
    return patient

# API pour obtenir tous les patients
@patients_router.get("/usagers/", response_model=List[Patient])
async def get_all_patients():
    query = "SELECT id_usager, civilite, nom, prenom, sexe, adresse, code_postal, ville, date_nais, lieu_nais, num_secu, id_medecin FROM usager"
    with conn.cursor() as cursor:
        cursor.execute(query)
        patients = []
        for (id_usager, civilite, nom, prenom, sexe, adresse, code_postal, ville, date_nais, lieu_nais, num_secu, id_medecin) in cursor.fetchall():
            patient = Patient(
                id_usager=id_usager,
                civilite=civilite,
                nom=nom,
                prenom=prenom,
                sexe=sexe,
                adresse=adresse,
                code_postal=code_postal,
                ville=ville,
                date_nais=date_nais,
                lieu_nais=lieu_nais,
                num_secu=num_secu,
                id_medecin=id_medecin
            )
            patients.append(patient)
    return patients

# API pour modifier un patient par son ID
@patients_router.patch("/usagers/{patient_id}")
async def update_patient(patient_id: int, adresse: str, code_postal: str, ville: str, id_medecin: int):
    query = "UPDATE usager SET adresse = %s, code_postal = %s, ville = %s, id_medecin = %s WHERE id_usager = %s"
    values = (adresse, code_postal, ville, id_medecin, patient_id)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        conn.commit()
    return {"message": "Patient mis à jour avec succès"}

# API pour obtenir un patient par son ID
@patients_router.get("/usagers/{patient_id}", response_model=Patient)
async def get_patient(patient_id: int):
    query = "SELECT id_usager, civilite, nom, prenom, sexe, adresse, code_postal, ville, date_nais, lieu_nais, num_secu, id_medecin FROM usager WHERE id_usager = %s"
    values = (patient_id,)
    with conn.cursor() as cursor:
        cursor.execute(query, values)
        row = cursor.fetchone()
        if row:
            id_usager, civilite, nom, prenom, sexe, adresse, code_postal, ville, date_nais, lieu_nais, num_secu, id_medecin = row
            return Patient(
                id_usager=id_usager,
                civilite=civilite,
                nom=nom,
                prenom=prenom,
                sexe=sexe,
                adresse=adresse,
                code_postal=code_postal,
                ville=ville,
                date_nais=date_nais,
                lieu_nais=lieu_nais,
                num_secu=num_secu,
                id_medecin=id_medecin
            )
        else:
            raise HTTPException(status_code=404, detail="Patient non trouvé")

# API pour supprimer un patient par son ID
@patients_router.delete("/usagers/{patient_id}")
async def delete_patient(patient_id: int):
    # Supprimer les consultations associées au patient
    delete_consultations_query = "DELETE FROM consultation WHERE id_usager = %s"
    with conn.cursor() as cursor:
        cursor.execute(delete_consultations_query, (patient_id,))
        conn.commit()

    # Supprimer le patient lui-même
    delete_patient_query = "DELETE FROM usager WHERE id_usager = %s"
    with conn.cursor() as cursor:
        cursor.execute(delete_patient_query, (patient_id,))
        conn.commit()

    return {"message": "Patient et consultations associées supprimés avec succès"}
