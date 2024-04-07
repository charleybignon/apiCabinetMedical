from fastapi import FastAPI,Depends
from API_AppMed.patients import patients_router
from API_AppMed.medecins import medecins_router
from API_AppMed.consultations import consults_router
from API_AppMed.statistiques import stats_router
from API_AUTH.authentification import auth_router, vérifier_token


app = FastAPI()

# Montage des sous-routeurs

app.include_router(auth_router, tags=["Authentification"])
app.include_router(patients_router, dependencies=[Depends(vérifier_token)], tags=["Patients"])
app.include_router(medecins_router, dependencies=[Depends(vérifier_token)], tags=["Médecins"])
app.include_router(consults_router, dependencies=[Depends(vérifier_token)], tags=["Consultations"])
app.include_router(stats_router, dependencies=[Depends(vérifier_token)], tags=["Statistiques"])


