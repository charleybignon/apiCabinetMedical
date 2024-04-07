from fastapi import FastAPI, APIRouter
import pymysql

stats_router = APIRouter()

# Connexion à la base de données
conn = pymysql.connect(
    host="mysql-cabinet-gayrard-bignon.alwaysdata.net",
    user="354243",
    password="$iutinfo",
    database="cabinet-gayrard-bignon_db"
)

# API pour obtenir les statistiques des médecins
@stats_router.get("/stats/medecins")
async def get_medecin_stats():
    query = """
        SELECT m.nom, COUNT(c.id_medecin) as consultations
        FROM medecin m
        LEFT JOIN consultation c ON m.id_medecin = c.id_medecin
        GROUP BY m.id_medecin
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        medecin_stats = cursor.fetchall()
    return medecin_stats

# API pour obtenir les statistiques des usagers
@stats_router.get("/stats/usagers")
async def get_usager_stats():
    query = """
        SELECT u.nom, COUNT(c.id_usager) as consultations
        FROM usager u
        LEFT JOIN consultation c ON u.id_usager = c.id_usager
        GROUP BY u.id_usager
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        usager_stats = cursor.fetchall()
    return usager_stats
