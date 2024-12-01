import csv
from datetime import date, timedelta
from io import StringIO
from lib2to3.pytree import Base
from ntpath import join
from sqlalchemy import select, join
from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
import jwt
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from . import model, schemas, crud
from .database import SessionLocal, engine
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import engine, Base
from backend.schemas import UserCreate, UserOut, Token
from backend.crud import create_user, get_contrats, get_equipements_by_employee, get_user_by_username, authenticate_user
from backend.security import *
from sqlalchemy.orm import joinedload

model.Base.metadata.create_all(bind=engine)

app = FastAPI()
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Dépendance de session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
origins=[
    "http://localhost:5173/"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet toutes les origines
    allow_credentials=True,
    allow_methods=["*"],  # Permet toutes les méthodes
    allow_headers=["*"],  # Permet tous les en-têtes
)
#########
# Fonction pour extraire les IDs des équipements
@app.post("/rackgroups/", response_model=schemas.RackGroup)
def create_rack_group(rack_group: schemas.RackGroupCreate, db: Session = Depends(get_db)):
    return crud.create_rack_group(db=db, rack_group=rack_group)

@app.get("/rackgroups/{rackGroup_uid}", response_model=schemas.RackGroup)
def read_rack_group(rackGroup_uid: int, db: Session = Depends(get_db)):
    db_rack_group = crud.get_rack_group(db, rackGroup_uid=rackGroup_uid)
    if db_rack_group is None:
        raise HTTPException(status_code=404, detail="RackGroup not found")
    return db_rack_group

@app.get("/rackgroups/", response_model=list[schemas.RackGroup])
def read_rack_groups(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    rack_groups = crud.get_rack_groups(db, skip=skip, limit=limit)
    return rack_groups

@app.patch("/rackgroups/{rackGroup_uid}", response_model=schemas.RackGroup)
def update_rack_group(rackGroup_uid: int, rack_group: schemas.RackGroupUpdate, db: Session = Depends(get_db)):
    return crud.update_rack_group(db, rackGroup_uid=rackGroup_uid, rack_group=rack_group)

@app.delete("/rackgroups/{rackGroup_uid}")
def delete_rack_group(rackGroup_uid: int, db: Session = Depends(get_db)):
    return crud.delete_rack_group(db, rackGroup_uid=rackGroup_uid)

# Routes pour Rack
@app.post("/racks/", response_model=schemas.Rack)
def create_rack(rack: schemas.RackCreate, db: Session = Depends(get_db)):
    return crud.create_rack(db=db, rack=rack)

@app.get("/racks/{rack_uid}", response_model=schemas.Rack)
def read_rack(rack_uid: int, db: Session = Depends(get_db)):
    db_rack = crud.get_rack(db, rack_uid=rack_uid)
    if db_rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    return db_rack

@app.get("/racks/", response_model=list[schemas.Rack])
def read_racks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    racks = crud.get_racks(db, skip=skip, limit=limit)
    return racks

@app.patch("/racks/{rack_uid}", response_model=schemas.Rack)
def update_rack(rack_uid: int, rack: schemas.RackUpdate, db: Session = Depends(get_db)):
    return crud.update_rack(db, rack_uid=rack_uid, rack=rack)

@app.delete("/racks/{rack_uid}")
def delete_rack(rack_uid: int, db: Session = Depends(get_db)):
    return crud.delete_rack(db, rack_uid=rack_uid)
def extraire_ids_equipements(db: Session):
    ids_equipements = db.query(model.Maintenance.equipement_id).distinct().all()
    ids_equipements = [id[0] for id in ids_equipements]
    return ids_equipements

def extraire_equipements(db: Session):
    resultats = db.query(
        model.Maintenance.equipement_id,
        model.Equipement.type,
        model.Equipement.nom,
        model.Equipement.num_serie
    ).join(
        model.Equipement,
        model.Maintenance.equipement_id == model.Equipement.equipement_id
    ).distinct().all()
    
    equipements = {id: (type, nom, num_serie) for id, type, nom, num_serie in resultats}
    return equipements

def calculer_mtbf(equipement_id: int, db: Session):
    maintenances = db.query(model.Maintenance).filter(model.Maintenance.equipement_id == equipement_id).order_by(model.Maintenance.dateDePanne).all()
    equipement = db.query(model.Equipement).filter(model.Equipement.equipement_id == equipement_id).first()

    if len(maintenances) < 2:
        return None
    temps_total = timedelta()
    for i in range(1, len(maintenances)):
        temps_total += maintenances[i].dateDePanne - maintenances[i-1].dateDePanne
    mtbf = temps_total / (len(maintenances) - 1)
    return mtbf.days, equipement.type, equipement.nom, equipement.num_serie

def calculer_mtbf_pour_tous_equipements(db: Session):
    ids_equipements = extraire_ids_equipements(db)
    mtbf_resultats = {}
    for equipement_id in ids_equipements:
        result = calculer_mtbf(equipement_id, db)
        if result is not None:
            mtbf, type_equipement, nom, num_serie = result
            mtbf_resultats[equipement_id] = {
                "mtbf": mtbf,
                "type": type_equipement,
                "nom": nom,
                "numero_serie": num_serie
            }
        else:
            mtbf_resultats[equipement_id] = {
                "mtbf": None,
                "type": "Inconnu",
                "nom": "Inconnu",
                "numero_serie": "Inconnu"
            }
    return mtbf_resultats

@app.get("/mtbf")
def obtenir_mtbf(db: Session = Depends(get_db)):
    resultats = calculer_mtbf_pour_tous_equipements(db)
    resultats_list = [{"equipement_id": k, **v} for k, v in resultats.items()]

    # Grouper les résultats par type
    grouped_resultats = {}
    for item in resultats_list:
        type_equipement = item["type"]
        if type_equipement not in grouped_resultats:
            grouped_resultats[type_equipement] = []
        grouped_resultats[type_equipement].append(item)

    # Convertir en liste pour la réponse
    response = [{"type": key, "equipements": value} for key, value in grouped_resultats.items()]
    return {"data": response}

@app.post("/maintenances/", response_model=schemas.MaintenanceInDB)
def create_maintenance(maintenance: schemas.MaintenanceCreate, db: Session = Depends(get_db)):
    return crud.create_maintenance(db=db, maintenance=maintenance)

@app.get("/maintenances/{maintenance_id}", response_model=schemas.MaintenanceInDB)
def read_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    db_maintenance = crud.get_maintenance(db, maintenance_id)
    if db_maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return db_maintenance

@app.get("/maintenances/", response_model=List[schemas.MaintenanceInDB])
def read_maintenances(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_maintenances(db, skip=skip, limit=limit)

@app.patch("/maintenances/{maintenance_id}", response_model=schemas.MaintenanceInDB)
def update_maintenance(maintenance_id: int, maintenance: schemas.MaintenanceUpdate, db: Session = Depends(get_db)):
    db_maintenance = crud.update_maintenance(db, maintenance_id, maintenance)
    if db_maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return db_maintenance

@app.delete("/maintenances/{maintenance_id}", response_model=schemas.MaintenanceInDB)
def delete_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    db_maintenance = crud.delete_maintenance(db, maintenance_id)
    if db_maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return db_maintenance
#################
@app.delete("/clusters/{cluster_id}/equipements/{equipement_id}")
def remove_equipement_from_cluster(cluster_id: int, equipement_id: int, db: Session = Depends(get_db)):
    cluster = db.query(model.Cluster).filter(model.Cluster.id == cluster_id).first()
    equipement = db.query(model.Equipement).filter(model.Equipement.equipement_id == equipement_id).first()
    
    if not cluster or not equipement:
        raise HTTPException(status_code=404, detail="Cluster or Equipement not found")

    cluster.equipements.remove(equipement)
    db.commit()
    return {"message": "Equipement removed from cluster"}

@app.post("/clusters/", response_model=schemas.ClusterRead)
def create_cluster(cluster: schemas.ClusterCreate, db: Session = Depends(get_db)):
    return crud.create_cluster(db=db, cluster=cluster)

# Route to get a Cluster by ID
@app.get("/clusters/{cluster_id}", response_model=schemas.ClusterRead)
def read_cluster(cluster_id: int, db: Session = Depends(get_db)):
    db_cluster = crud.get_cluster(db=db, cluster_id=cluster_id)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return db_cluster

# Route to get all Clusters
@app.get("/clusters/", response_model=List[schemas.ClusterRead])
def read_clusters(skip: int = 0, limit: int = 100000000, db: Session = Depends(get_db)):
    clusters = crud.get_clusters(db=db, skip=skip, limit=limit)
    return clusters

# Route to update a Cluster
@app.patch("/clusters/{cluster_id}", response_model=schemas.ClusterRead)
def update_cluster(cluster_id: int, cluster: schemas.ClusterUpdate, db: Session = Depends(get_db)):
    db_cluster = crud.update_cluster(db=db, cluster_id=cluster_id, cluster=cluster)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return db_cluster

# Route to delete a Cluster
@app.delete("/clusters/{cluster_id}", response_model=schemas.ClusterRead)
def delete_cluster(cluster_id: int, db: Session = Depends(get_db)):
    db_cluster = crud.delete_cluster(db=db, cluster_id=cluster_id)
    if db_cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return db_cluster
####
@app.post("/licenses/", response_model=schemas.LicenseBase)
def create_license(license: schemas.LicenseCreate, db: Session = Depends(get_db)):
    return crud.create_license(db=db, license=license)

@app.get("/licenses/{license_id}", response_model=schemas.License)
def read_license(license_id: int, db: Session = Depends(get_db)):
    db_license = crud.get_license(db=db, license_id=license_id)
    if db_license is None:
        raise HTTPException(status_code=404, detail="License not found")
    return db_license

@app.get("/licenses/", response_model=list[schemas.License])
def read_licenses(
    skip: int = 0,
    limit: int = 10,
    dateDebut: Optional[str] = None,
    dateExpiration: Optional[str] = None,
    type: Optional[str] = None,
    fournisseur: Optional[str] = None,
    statut: Optional[str] = None,
    id_employee: Optional[int] = None,
    id_equipement: Optional[int] = None,
    id_application: Optional[int] = None,
    db: Session = Depends(get_db)
):
    licenses = crud.get_licenses(
        db, 
        skip=skip, 
        limit=limit,
        dateDebut=dateDebut,
        dateExpiration=dateExpiration,
        type=type,
        fournisseur=fournisseur,
        statut=statut,
        id_employee=id_employee,
        id_equipement=id_equipement,
        id_application=id_application
    )
    return licenses

@app.post("/licenses/bulk-create/")
async def create_licenses(licenses: list[schemas.LicenseCreate], db: Session = Depends(get_db)):
    try:
        for license in licenses:
            crud.create_license(db, license)
        return {"message": "Licenses created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.patch("/licenses/{license_id}", response_model=schemas.License)
def update_license(license_id: int, license: schemas.LicenseCreate, db: Session = Depends(get_db)):
    db_license = crud.update_license(db=db, license_id=license_id, license=license)
    if db_license is None:
        raise HTTPException(status_code=404, detail="License not found")
    return db_license

@app.delete("/licenses/{license_id}", response_model=schemas.License)
def delete_license(license_id: int, db: Session = Depends(get_db)):
    db_license = crud.delete_license(db=db, license_id=license_id)
    if db_license is None:
        raise HTTPException(status_code=404, detail="License not found")
    return db_license

##########

@app.post("/applications/", response_model=schemas.Application)
def create_application(application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    return crud.create_application(db=db, application=application)

@app.get("/applications/{application_id}", response_model=schemas.Application)
def read_application(application_id: int, db: Session = Depends(get_db)):
    db_application = crud.get_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application

@app.get("/applications/", response_model=list[schemas.Application])
def read_applications(
    skip: int = 0,
    id:Optional[int] = Query(None),
    nom: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    responsable_id: Optional[int] = Query(None),
    
    db: Session = Depends(get_db),
):
    filters = {"id":id,"nom": nom, "description": description, "responsable_id":responsable_id}
   
    applications = crud.get_applications(db, skip=skip, filters=filters)
    return applications

@app.put("/applications/{application_id}", response_model=schemas.Application)
def update_application(application_id: int, application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    db_application = crud.update_application(db=db, application_id=application_id, application=application)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application

@app.delete("/applications/{application_id}", response_model=schemas.Application)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    db_application = crud.delete_application(db=db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application
#########

@app.post("/contrats/", response_model=schemas.Contrat)
def create_contrat(contrat: schemas.ContratCreate, db: Session = Depends(get_db)):
    return crud.create_contrat(db=db, contrat=contrat)

@app.get("/contrats/{contrat_id}", response_model=schemas.Contrat)
def read_contrat(contrat_id: int, db: Session = Depends(get_db)):
    db_contrat = crud.get_contrat(db, contrat_id)
    if db_contrat is None:
        raise HTTPException(status_code=404, detail="Contrat not found")
    return db_contrat

@app.get("/contrats/", response_model=list[schemas.Contrat])
def read_contrats(
    skip: int = 0,
    num_contrat: Optional[str] = None,
    fournisseur: Optional[str] = None,
    min_montant: Optional[float] = None,
    max_montant: Optional[float] = None,
    date_achat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    filters = {
        "num_contrat": num_contrat,
        "fournisseur": fournisseur,
        "min_montant": min_montant,
        "max_montant": max_montant,
        "date_achat": date_achat,
    }
    return get_contrats(db, skip=skip, filters=filters)
@app.put("/contrats/{contrat_id}", response_model=schemas.Contrat)
def update_contrat(contrat_id: int, contrat: schemas.ContratCreate, db: Session = Depends(get_db)):
    db_contrat = crud.update_contrat(db, contrat_id, contrat)
    if db_contrat is None:
        raise HTTPException(status_code=404, detail="Contrat not found")
    return db_contrat

@app.delete("/contrats/{contrat_id}", response_model=schemas.Contrat)
def delete_contrat(contrat_id: int, db: Session = Depends(get_db)):
    db_contrat = crud.delete_contrat(db, contrat_id)
    if db_contrat is None:
        raise HTTPException(status_code=404, detail="Contrat not found")
    return db_contrat
################
@app.patch("/employee-equipement/{association_id}", response_model=schemas.EmployeeEquipementAssociationCreate)
def update_employee_equipement_association(
    association_id: int,
    association: schemas.EmployeeEquipementAssociationCreate,  # Utiliser un schéma approprié
    db: Session = Depends(get_db)
):
    # Convertir le schéma en dictionnaire, en excluant les valeurs non définies
    association_values = association.dict(exclude_unset=True)

    # Appeler la fonction de mise à jour dans crud
    updated_association = crud.update_employee_equipement_association_in_db(  # Utiliser le nouveau nom de la fonction
        db=db,
        association_id=association_id,
        values=association_values
    )
    
    return updated_association
@app.delete("/employee-equipement/{association_id}")
def delete_employee_equipement_association(
    association_id: int,
    db: Session = Depends(get_db)
):
    crud.delete_employee_equipement_association_in_db(db=db, association_id=association_id)
    return {"message": "Association deleted successfully"}

@app.get("/employee-equipement/")
def get_associations(db: Session = Depends(get_db)):
    stmt = (
        select(
            model.employee_equipement_association.c.id,
            model.Employee.nom.label('employee_nom'),
            model.Employee.service.label('employee_service'),

            model.Employee.id.label('employee_id'),
            model.Employee.matricule.label('employee_matricule'),
            model.Equipement.nom.label('equipement_nom'),
            model.Equipement.equipement_id.label('equipement_id'),

            model.Equipement.type.label('equipement_type'),
            model.employee_equipement_association.c.date_affectation,
            model.employee_equipement_association.c.date_desaffectation,
            model.employee_equipement_association.c.employee_id,
            model.employee_equipement_association.c.equipement_id,
            model.employee_equipement_association.c.status
        )
        .select_from(
            join(
                model.employee_equipement_association,
                model.Employee,
                model.employee_equipement_association.c.employee_id == model.Employee.id
            )
            .join(
                model.Equipement,
                model.employee_equipement_association.c.equipement_id == model.Equipement.equipement_id
            )
        )
    )
    
    results = db.execute(stmt).fetchall()
    
    if not results:
        raise HTTPException(status_code=404, detail="No associations found")
    
    associations = [
        {
            "id": row.id,
            "employee_nom": row.employee_nom,
            "employee_id":row.employee_id,
            "employee_matricule": row.employee_matricule,
            "employee_service":row.employee_service,
            "equipement_nom": row.equipement_nom,
            "equipement_type": row.equipement_type,
            "equipement_id":row.equipement_id,
            "date_affectation": row.date_affectation,
            "date_desaffectation": row.date_desaffectation,
            "status": row.status,
        }
        for row in results
    ]
    
    return associations
# @app.post("/employee_equipement/{employee_id}/equipements/")
# def assign_multiple_equipements_to_employee(employee_id: int, equipement_ids: List[int], db: Session = Depends(get_db)):
#     try:
#         # Boucler sur chaque ID d'équipement et créer une association
#         for equipement_id in equipement_ids:
#             association = model.employee_equipement_association.insert().values(
#                 employee_id=employee_id,
#                 equipement_id=equipement_id,
#                 status=True,
#                 date_affectation=datetime.utcnow()
#             )
#             db.execute(association)
#         db.commit()
#         return {"message": f"Successfully assigned {len(equipement_ids)} equipements to employee {employee_id}"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
@app.get("/employee-equipement/{association_id}", response_model=schemas.EmployeeEquipementAssociation)
def read_employee_equipement_associations(association_id: int, db: Session = Depends(get_db)):
    db_equipement = crud.get_employee_equipement_associations(db, association_id=association_id)
    if db_equipement is None:
        raise HTTPException(status_code=404, detail="Assosiation not found")
    return db_equipement

@app.post("/employee-equipement/", response_model=schemas.EmployeeEquipementAssociationCreate)
def create_employee_equipement_association(association: schemas.EmployeeEquipementAssociationCreate, db: Session = Depends(get_db)):
    print(association.dict())
    db_association = crud.create_employee_equipement_association(db=db, association=association)
    if not db_association:
        raise HTTPException(status_code=400, detail="Association could not be created")
    
    return association.dict()
@app.get("/equipement/{equipement_id}/associations/", response_model=List[schemas.EmployeeEquipementAssociation])
def read_associations_by_equipement(equipement_id: int, db: Session = Depends(get_db)):
    associations = crud.get_employee_equipement_associations_by_equipement(db, equipement_id)
    if not associations:
        raise HTTPException(status_code=404, detail="No associations found for this equipment")
    return associations
@app.get("/employees/{employee_id}/associations/", response_model=List[schemas.EmployeeEquipementAssociation])
def read_employee_equipement_associations(employee_id: int, db: Session = Depends(get_db)):
    associations = crud.get_associations_by_employee(db, employee_id)
    if not associations:
        raise HTTPException(status_code=404, detail="No associations found for this employee")
    return associations
@app.get("/employee/{employee_id}/equipements", response_model=List[schemas.Equipement])
def read_equipements_by_employee(employee_id: int, db: Session = Depends(get_db)):
    equipements = get_equipements_by_employee(db, employee_id)
    
    if equipements is None:
        raise HTTPException(status_code=404, detail="Aucune affectation trouvée pour cet employé")
    
    return equipements
#############
@app.post("/utlisateur/", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db, user)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/utlisateur/me/", response_model=UserOut)
async def read_users_me(current_user: model.User = Depends(get_current_user)):
    return current_user

@app.get("/utlisateur/{user_id}", response_model=schemas.UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.patch("/utlisateur/{user_id}", response_model=schemas.UserRead)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db=db, user_id=user_id, user=user)

@app.delete("/utlisateur/{user_id}", response_model=schemas.UserRead)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.delete_user(db=db, user_id=user_id)

@app.get("/utlisateur/", response_model=list[schemas.UserRead])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users
# Employee endpoints
@app.post("/employees/", response_model=schemas.Employee)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    return crud.create_employee(db=db, employee=employee)

@app.get("/employees/{employee_id}", response_model=schemas.Employee)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@app.get("/employees/", response_model=List[schemas.Employee])
def read_employees(skip: int = 0, limit: int = 10000000, db: Session = Depends(get_db)):
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees
@app.patch("/employees/{id}", response_model=schemas.EmployeeBase)
def update_employe(id: int, employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    print(employee)
    db_employe = crud.update_employe(db, employee_id=id, employee=employee)
    if db_employe is None:
        raise HTTPException(status_code=404, detail="Employe not found")
    return db_employe
@app.delete("/employees/{employee_id}", response_model=schemas.Employee)
def delete_employe(employee_id: int, db: Session = Depends(get_db)):
    db_employe = crud.delete_employe(db, employee_id=employee_id)
    if db_employe is None:
        raise HTTPException(status_code=404, detail="Employe not found")
    return db_employe


# Equipement endpoints
def convert_value(value: str, value_type: type):
    if value == '' or value is None:
        return None
    try:
        if value_type == bool:
            return value.lower() in ['true', '1']
        elif value_type == int:
            return int(value)
        elif value_type == float:
            return float(value)
        elif value_type == str:
            return str(value)
        elif value_type == datetime:
            return datetime.strptime(value, "%Y-%m-%d")
        else:
            return value
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid value {value} for type {value_type}")

@app.post("/equipements/import/")
async def import_equipements(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")

    try:
        # Lire le contenu du fichier
        contents = await file.read()
        csv_reader = csv.DictReader(StringIO(contents.decode("utf-8")))

        # Liste pour stocker les nouveaux équipements
        new_equipements = []

        for row in csv_reader:
            equipement_data = {
                "equipement_id": convert_value(row.get("equipement_id"), int),
                "type": row.get("type"),
                "adresse_ip": row.get("adresse_ip"),
                "status": convert_value(row.get("status"), bool),
                "quantite": convert_value(row.get("quantite"), int),
                "nom": row.get("nom"),
                "num_serie": convert_value(row.get("num_serie"), int),
                "codeBar": row.get("codeBar"),
                "marque": row.get("marque"),
                "modele": row.get("modele"),
                "dateMiseService": convert_value(row.get("dateMiseService"), datetime),
                "rackable": convert_value(row.get("rackable"), bool),
                "responsable": row.get("responsable"),
                "systemeInstalle": row.get("systemeInstalle"),
                "nombreUniteOccRack": convert_value(row.get("nombreUniteOccRack"), int),
                "nombreLecteur": convert_value(row.get("nombreLecteur"), int),
                "nombreBonde": convert_value(row.get("nombreBonde"), int),
                "stockage": row.get("stockage"),
                "ram": convert_value(row.get("ram"), int),
                "cpu": convert_value(row.get("cpu"), int),
                "refAchat": row.get("refAchat"),
                "numContratMaint": convert_value(row.get("numContratMaint"), int),
                "prestataireMaintenance": row.get("prestataireMaintenance"),
                "dateDebutMaintenance": convert_value(row.get("dateDebutMaintenance"), datetime),
                "dateFinMaintenance": convert_value(row.get("dateFinMaintenance"), datetime),
                "typeMaintenance": row.get("typeMaintenance"),
                "cluster_id": convert_value(row.get("cluster_id"), int),
                "num_acquisition": convert_value(row.get("num_acquisition"), int),
            }

            # Créer un nouvel objet Equipement pour chaque ligne du fichier CSV
            equipement = model.Equipement(**equipement_data)
            new_equipements.append(equipement)

        # Ajouter les nouveaux équipements à la base de données
        db.add_all(new_equipements)
        db.commit()

        return {"message": f"{len(new_equipements)} équipements ont été importés avec succès"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue lors de l'importation: {str(e)}")

@app.post("/equipements/", response_model=schemas.Equipement)
def create_equipement(equipement: schemas.EquipementCreate, db: Session = Depends(get_db)):
    return crud.create_equipement(db=db, equipement=equipement)

@app.get("/equipements/{equipement_id}", response_model=schemas.Equipement)
def read_equipement(equipement_id: int, db: Session = Depends(get_db)):
    db_equipement = crud.get_equipement(db, equipement_id=equipement_id)
    if db_equipement is None:
        raise HTTPException(status_code=404, detail="Equipement not found")
    return db_equipement



@app.get("/equipements/", response_model=List[schemas.Equipement])
def read_equipements(
    skip: int = 0,
    status: Optional[bool] = Query(None),
    nom: Optional[str] = Query(None),
    adresse_ip: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    num_serie: Optional[str] = Query(None),
    marque: Optional[str] = Query(None),
    codeBar: Optional[str] = Query(None),
    modele: Optional[str] = Query(None),
    quantite: Optional[int] = Query(None),
    employees: Optional[int] = Query(None),  # Ajout du filtre pour un seul employé
    db: Session = Depends(get_db)
):
    filters = {
        "nom": nom,
        "adresse_ip": adresse_ip,
        "quantite": quantite,
        "status": status,
        "type": type,
        "codeBar": codeBar,
        "marque": marque,
        "num_serie": num_serie,
        "modele": modele
    }

    # Ajout du filtre sur employees si fourni
    if employees:
        filters["employees"] = employees

    equipements = crud.get_equipements(db, skip=skip, filters=filters)
    return equipements

@app.patch("/equipements/{equipement_id}", response_model=schemas.Equipement)
def update_equipement(equipement_id: int, equipement: schemas.EquipementCreate, db: Session = Depends(get_db)):
    db_equipement = crud.update_equipement(db, equipement_id=equipement_id, equipement=equipement)
    if db_equipement is None:
        raise HTTPException(status_code=404, detail="Equipement not found")
    return db_equipement

@app.delete("/equipements/{equipement_id}", response_model=schemas.Equipement)
def delete_equipement(equipement_id: int, db: Session = Depends(get_db)):
    db_equipement = crud.delete_equipement(db, equipement_id=equipement_id)
    if db_equipement is None:
        raise HTTPException(status_code=404, detail="Equipement not found")
    return db_equipement

# Acquisition endpoints
@app.post("/acquisitions/", response_model=schemas.Acquisition)
def create_acquisition(acquisition: schemas.AcquisitionCreate, db: Session = Depends(get_db)):
    db_acquisition = crud.create_acquisition(db=db, acquisition=acquisition)

    # Création de l'événement associé
    new_event = model.Event(
        acquisition_id=db_acquisition.num_acquisition,
        statut=db_acquisition.statut,
        date=datetime.utcnow()
    )
    db.add(new_event)
    db.commit()
    db.refresh(db_acquisition)

    return db_acquisition

@app.get("/acquisitions/{acquisition_id}", response_model=schemas.Acquisition)
def read_acquisition(acquisition_id: int, db: Session = Depends(get_db)):
    db_acquisition = crud.get_acquisition(db, acquisition_id=acquisition_id)
    if db_acquisition is None:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    return db_acquisition

@app.get("/acquisitions/", response_model=List[schemas.Acquisition])
def read_acquisitions(skip: int = 0, limit: int = 10000000, db: Session = Depends(get_db)):
    acquisitions = crud.get_acquisitions(db, skip=skip, limit=limit)
    return acquisitions

@app.patch("/acquisitions/{acquisition_id}", response_model=schemas.Acquisition)
def update_acquisition(acquisition_id: int, acquisition_update: schemas.AcquisitionBase, db: Session = Depends(get_db)):
    db_acquisition = crud.update_acquisition(db, acquisition_id, acquisition_update)
    if db_acquisition is None:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    return db_acquisition
@app.delete("/acquisitions/{num_acquisition}", response_model=schemas.AcquisitionCreate)
def delete_acquisition(num_acquisition: int, db: Session = Depends(get_db)):
    db_acquisition = crud.delete_acquisition(db, num_acquisition)
    if db_acquisition is None:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    return db_acquisition
@app.post("/acquisitions/{acquisition_id}/events/", response_model=schemas.EventInDB)
def create_event(acquisition_id: int, event: schemas.EventCreate, db: Session = Depends(get_db)):
    acquisition = db.query(model.Acquisition).filter(model.Acquisition.num_acquisition == acquisition_id).first()
    if not acquisition:
        raise HTTPException(status_code=404, detail="Acquisition not found")

    new_event = model.Event(
        acquisition_id=event.acquisition_id,
        statut=event.statut,
        date=event.date
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event
@app.get("/acquisitions/{acquisition_id}/events", response_model=List[schemas.EventCreate])
def get_acquisition_events(acquisition_id: int, db: Session = Depends(get_db)):
    acquisition = db.query(model.Acquisition).filter(model.Acquisition.num_acquisition == acquisition_id).first()
    if not acquisition:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    
    events = db.query(model.Event).filter(model.Event.acquisition_id == acquisition_id).all()
    return events
# Hyperviseur Routes
@app.post("/hyperviseurs/", response_model=schemas.Hyperviseur)
def create_hyperviseur(hyperviseur: schemas.HyperviseurCreate, db: Session = Depends(get_db)):
    return crud.create_hyperviseur(db=db, hyperviseur=hyperviseur)

@app.get("/hyperviseurs/{hyperviseur_id}", response_model=schemas.Hyperviseur)
def read_hyperviseur(hyperviseur_id: int, db: Session = Depends(get_db)):
    db_hyperviseur = crud.get_hyperviseur(db, hyperviseur_id=hyperviseur_id)
    if db_hyperviseur is None:
        raise HTTPException(status_code=404, detail="Hyperviseur not found")
    return db_hyperviseur


@app.get("/hyperviseurs/", response_model=List[schemas.Hyperviseur])
def read_hyperviseurs(
    skip: int = Query(0, alias="page", ge=0),
    nom: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    filters = {
        "nom": nom,
    }
    return crud.get_hyperviseurs(db, skip=skip, filters=filters)

@app.patch("/hyperviseurs/{hyperviseur_id}", response_model=schemas.Hyperviseur)
def update_hyperviseur(hyperviseur_id: int, hyperviseur: schemas.HyperviseurCreate, db: Session = Depends(get_db)):
    db_hyperviseur = crud.update_hyperviseur(db, hyperviseur_id=hyperviseur_id, hyperviseur=hyperviseur)
    if db_hyperviseur is None:
        raise HTTPException(status_code=404, detail="Hyperviseur not found")
    return db_hyperviseur

@app.delete("/hyperviseurs/{hyperviseur_id}", response_model=schemas.Hyperviseur)
def delete_hyperviseur(hyperviseur_id: int, db: Session = Depends(get_db)):
    db_hyperviseur = crud.delete_hyperviseur(db, hyperviseur_id=hyperviseur_id)
    if db_hyperviseur is None:
        raise HTTPException(status_code=404, detail="Hyperviseur not found")
    return db_hyperviseur

# Machine Virtuelle Routes
@app.post("/machines_virtuelles/", response_model=schemas.MachineVirtuelle)
def create_machine_virtuelle(machine_virtuelle: schemas.MachineVirtuelleCreate, db: Session = Depends(get_db)):
    return crud.create_machine_virtuelle(db=db, machine_virtuelle=machine_virtuelle)

@app.get("/machines_virtuelles/{vm_id}", response_model=schemas.MachineVirtuelle)
def read_machine_virtuelle(vm_id: int, db: Session = Depends(get_db)):
    db_machine_virtuelle = crud.get_machine_virtuelle(db, vm_id=vm_id)
    if db_machine_virtuelle is None:
        raise HTTPException(status_code=404, detail="Machine Virtuelle not found")
    return db_machine_virtuelle

@app.get("/machines_virtuelles/", response_model=List[schemas.MachineVirtuelle])
def read_machines_virtuelles(
    skip: int = 0,
    limit: int = 10000000,
    nom: Optional[str] = Query(None),
    stockage: Optional[str] = Query(None),
    ram: Optional[str] = Query(None),
    cpu: Optional[str] = Query(None),
    OS: Optional[str] = Query(None),
    nom_domaine: Optional[str] = Query(None),
    domaine: Optional[str] = Query(None),
    ip_adresse: Optional[str] = Query(None),
    dateExpirationSupportOS: Optional[str] = Query(None),
    dateExpirationSupportOSEtendue: Optional[str] = Query(None),
    networkEgenet: Optional[bool] = Query(None),
    antivirus: Optional[bool] = Query(None),
    hyperviseur_id: Optional[int] = Query(None),
    cluster_id: Optional[int] = Query(None),
    responsable_id: Optional[int] = Query(None),  # Ajout du filtre pour le responsable
    db: Session = Depends(get_db),
):
    # Construire le dictionnaire de filtres
    filters = {
        "nom": nom,
        "stockage": stockage,
        "ram": ram,
        "cpu": cpu,
        "OS": OS,
        "nom_domaine": nom_domaine,
        "domaine": domaine,
        "ip_adresse": ip_adresse,
        "dateExpirationSupportOS": dateExpirationSupportOS,
        "dateExpirationSupportOSEtendue": dateExpirationSupportOSEtendue,
        "networkEgenet": networkEgenet,
        "antivirus": antivirus,
        "hyperviseur_id": hyperviseur_id,
        "cluster_id": cluster_id,
        "responsable_id": responsable_id
    }

    # Filtrer les valeurs None
    filters = {k: v for k, v in filters.items() if v is not None}

    # Appel de la fonction CRUD avec les filtres
    return crud.get_machines_virtuelles(db, skip=skip, limit=limit, filters=filters)


@app.patch("/machines_virtuelles/{vm_id}", response_model=schemas.MachineVirtuelle)
def update_machine_virtuelle(vm_id: int, machine_virtuelle: schemas.MachineVirtuelleCreate, db: Session = Depends(get_db)):
    db_machine_virtuelle = crud.update_machine_virtuelle(db, vm_id=vm_id, machine_virtuelle=machine_virtuelle)
    if db_machine_virtuelle is None:
        raise HTTPException(status_code=404, detail="Machine Virtuelle not found")
    return db_machine_virtuelle

@app.delete("/machines_virtuelles/{vm_id}", response_model=schemas.MachineVirtuelle)
def delete_machine_virtuelle(vm_id: int, db: Session = Depends(get_db)):
    db_machine_virtuelle = crud.delete_machine_virtuelle(db, vm_id=vm_id)
    if db_machine_virtuelle is None:
        raise HTTPException(status_code=404, detail="Machine Virtuelle not found")
    return db_machine_virtuelle
