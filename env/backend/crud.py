from datetime import date
from typing import Any, Dict
from sqlalchemy import insert
from sqlalchemy.orm import Session
from . import model, schemas,security
from backend.security import *
from sqlalchemy.orm import joinedload
from sqlalchemy import update
from sqlalchemy.sql import extract

from sqlalchemy import delete
##########

def create_rack_group(db: Session, rack_group: schemas.RackGroupCreate):
    db_rack_group = model.RackGroup(
        **rack_group.dict()
    )
    db.add(db_rack_group)
    db.commit()
    db.refresh(db_rack_group)
    return db_rack_group

def get_rack_group(db: Session, rackGroup_uid: int):
    return db.query(model.RackGroup).filter(model.RackGroup.rackGroup_uid == rackGroup_uid).first()

def get_rack_groups(db: Session, skip: int = 0, limit: int = 10):
    return db.query(model.RackGroup).order_by(model.RackGroup.rackGroup_uid).offset(skip).limit(limit).all()

def update_rack_group(db: Session, rackGroup_uid: int, rack_group: schemas.RackGroupUpdate):
    db_rack_group = get_rack_group(db, rackGroup_uid)
    if db_rack_group:
        db_rack_group.rackGroup_name = rack_group.rackGroup_name
        db.commit()
        db.refresh(db_rack_group)
    return db_rack_group

def delete_rack_group(db: Session, rackGroup_uid: int):
    db_rack_group = get_rack_group(db, rackGroup_uid)
    if db_rack_group:
        db.delete(db_rack_group)
        db.commit()
    return db_rack_group

# CRUD pour Rack
def create_rack(db: Session, rack: schemas.RackCreate):
    # Création du rack
    db_rack = model.Rack(**rack.dict(exclude={"Equipements"}))  # Exclure Equipements pour la création initiale
    db.add(db_rack)
    db.commit()
    db.refresh(db_rack)

    # Association des équipements au rack
    if rack.Equipements:
        for equipement_id in rack.Equipements:
            # Récupérer l'équipement
            equipement = db.query(model.Equipement).filter(model.Equipement.equipement_id == equipement_id).first()
            if equipement:
                if equipement.rackId is not None:
                    raise ValueError(f"L'équipement {equipement_id} est déjà assigné à un autre rack.")
                
                equipement.rackId = db_rack.rack_uid  # Associer le rack à l'équipement
                db.add(equipement)
            else:
                raise ValueError(f"L'équipement avec l'ID {equipement_id} n'existe pas.")
    
    # Valider les modifications
    db.commit()
    db.refresh(db_rack)
    return db_rack

def get_rack(db: Session, rack_uid: int):
    return db.query(model.Rack).filter(model.Rack.rack_uid == rack_uid).first()

def get_racks(db: Session, skip: int = 0, limit: int = 10):
    return db.query(model.Rack).order_by(model.Rack.rack_uid).offset(skip).limit(limit).all()

def update_rack(db: Session, rack_uid: int, rack: schemas.RackUpdate):
    db_rack = get_rack(db, rack_uid)
    if db_rack:
        db_rack.rack_name = rack.rack_name
        db_rack.marque = rack.marque
        db_rack.numSerie = rack.numSerie
        db_rack.nombreUnites = rack.nombreUnites
        db_rack.miseEnService = rack.miseEnService
        db_rack.refAchat = rack.refAchat
        db_rack.constructeur = rack.constructeur
        db_rack.dateAchat = rack.dateAchat
        db_rack.emplacement= rack.emplacement

        db.commit()
        db.refresh(db_rack)
    return db_rack

def delete_rack(db: Session, rack_uid: int):
    db_rack = get_rack(db, rack_uid)
    if db_rack:
        db.delete(db_rack)
        db.commit()
    return db_rack
def create_maintenance(db: Session, maintenance: schemas.MaintenanceCreate):
    db_maintenance = model.Maintenance(**maintenance.dict())
    db.add(db_maintenance)
    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance

def get_maintenance(db: Session, maintenance_id: int):
    return db.query(model.Maintenance).filter(model.Maintenance.id == maintenance_id).first()

def get_maintenances(db: Session, skip: int = 0, limit: int = 10):
    return db.query(model.Maintenance).order_by(model.Maintenance.id).offset(skip).limit(limit).all()
# # return db.query(model.Maintenance).order_by(
#         extract('year', model.Maintenance.dateDePanne), 
#         extract('month', model.Maintenance.dateDePanne)
#     ).offset(skip).limit(limit).all()
def update_maintenance(db: Session, maintenance_id: int, maintenance:schemas.MaintenanceUpdate):
    db_maintenance = db.query(model.Maintenance).filter(model.Maintenance.id == maintenance_id).first()
    if db_maintenance:
        for key, value in maintenance.dict(exclude_unset=True).items():
            setattr(db_maintenance, key, value)
        db.commit()
        db.refresh(db_maintenance)
    return db_maintenance

def delete_maintenance(db: Session, maintenance_id: int):
    db_maintenance = db.query(model.Maintenance).filter(model.Maintenance.id == maintenance_id).first()
    if db_maintenance:
        db.delete(db_maintenance)
        db.commit()
    return db_maintenance
####3

def get_contrat(db: Session, contrat_id: int):
    return db.query(model.Contrat).filter(model.Contrat.id == contrat_id).first()

def get_contrats(db: Session, skip: int = 0, filters: Dict[str, Any] = {}):
    query = db.query(model.Contrat)

    if filters.get("num_contrat"):
        query = query.filter(model.Contrat.num_contrat.contains(filters["num_contrat"]))
    
    if filters.get("fournisseur"):
        query = query.filter(model.Contrat.fournisseur.contains(filters["fournisseur"]))
    
    if filters.get("min_montant") is not None:
        query = query.filter(model.Contrat.montant >= filters["min_montant"])
    
    if filters.get("max_montant") is not None:
        query = query.filter(model.Contrat.montant <= filters["max_montant"])
    
    if filters.get("date_achat"):
        query = query.filter(model.Contrat.dateAchat == filters["date_achat"])

    return query.order_by(model.Contrat.id).offset(skip).all()
def create_contrat(db: Session, contrat: schemas.ContratCreate):
    db_contrat = model.Contrat(**contrat.dict())
    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)
    return db_contrat

def update_contrat(db: Session, contrat_id: int, contrat: schemas.ContratCreate):
    db_contrat = db.query(model.Contrat).filter(model.Contrat.id == contrat_id).first()
    if db_contrat:
        for key, value in contrat.dict().items():
            setattr(db_contrat, key, value)
        db.commit()
        db.refresh(db_contrat)
    return db_contrat

def delete_contrat(db: Session, contrat_id: int):
    db_contrat = db.query(model.Contrat).filter(model.Contrat.id == contrat_id).first()
    if db_contrat:
        db.delete(db_contrat)
        db.commit()
    return db_contrat


##
def create_employee_equipement_association(db: Session, association: schemas.EmployeeEquipementAssociationCreate):
    stmt = insert(model.employee_equipement_association).values(
        status=association.status,
        date_affectation=association.date_affectation,
        date_desaffectation=association.date_desaffectation,
        employee_id=association.employee_id,
        equipement_id=association.equipement_id
    )
    db.execute(stmt)
    db.commit()
    return True
def update_employee_equipement_association_in_db(db: Session, association_id: int, values: dict):
    # Rechercher l'association existante par ID
    association = db.query(model.employee_equipement_association).filter(model.employee_equipement_association.c.id == association_id).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Association not found")

    # Filtrer les valeurs non définies
    update_values = {k: v for k, v in values.items() if v is not None}

    # Exécuter la mise à jour
    db.execute(
        update(model.employee_equipement_association)
        .where(model.employee_equipement_association.c.id == association_id)
        .values(**update_values)
    )
    
    db.commit()
    
    # Recharger l'association mise à jour
    updated_association = db.query(model.employee_equipement_association).filter(model.employee_equipement_association.c.id == association_id).first()
    
    return updated_association

def get_employee_equipement_associations_by_equipement(db: Session, equipement_id: int):
    associations = db.query(model.employee_equipement_association).filter_by(equipement_id=equipement_id).all()
    return associations
def get_employee_equipement_association(db: Session, skip: int = 0):
    return db.query(model.employee_equipement_association).order_by(model.employee_equipement_association.id) .offset(skip).all()

def get_associations_by_employee(db: Session, employee_id: int):
    associations = db.query(model.employee_equipement_association).filter_by(employee_id=employee_id).all()
    return associations
def get_equipements_by_employee(db: Session, employee_id: int):
    # Récupérer l'employé avec les équipements associés via l'association many-to-many
    employee = db.query(model.Employee).filter(model.Employee.id == employee_id).first()

    if not employee:
        return []  # Retourner une liste vide si l'employé n'existe pas

    return employee.equipements  # Retourner les équipements associés
def get_employee_equipement_associations(db: Session, association_id: int):
    return db.query(model.employee_equipement_association).filter(model.employee_equipement_association.c.id == association_id).first()
def delete_employee_equipement_association_in_db(db: Session, association_id: int):
    # Construire la requête de suppression
    stmt = delete(model.employee_equipement_association).where(model.employee_equipement_association.c.id == association_id)

    # Exécuter la requête
    result = db.execute(stmt)

    # Vérifier si l'association a été supprimée
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Association not found")

    # Confirmer la transaction
    db.commit()
# Employee CRUD operations
def get_employee(db: Session, employee_id: int):
    return db.query(model.Employee).filter(model.Employee.id == employee_id).first()

def get_employees(db: Session, skip: int = 0, limit: int = 10000000):
    return db.query(model.Employee).order_by(model.Employee.id) .offset(skip).limit(limit).all()

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    db_employee = model.Employee(matricule=employee.matricule,nom=employee.nom, service=employee.service)
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def update_employe(db: Session, employee_id: int, employee: schemas.EmployeeCreate):
    db_employe = db.query(model.Employee).filter(model.Employee.id == employee_id).first()
    if db_employe is None:
        return None
    for key, value in employee.dict().items():
        setattr(db_employe, key, value)
    db.commit()
    db.refresh(db_employe)
    return db_employe

def delete_employe(db: Session, employee_id: int):
    db_employe = db.query(model.Employee).filter(model.Employee.id == employee_id).first()
    if db_employe:
        db.delete(db_employe)
        db.commit()
    return db_employe

# Equipement CRUD operations
def get_equipement(db: Session, equipement_id: int):
    return db.query(model.Equipement).filter(model.Equipement.equipement_id == equipement_id).first()
def get_equipements(db: Session, skip: int = 0, filters: Dict[str, Any] = {}):
    query = db.query(model.Equipement)

    for field, value in filters.items():
        if value is not None:  # Vérifier si une valeur a été fournie
            if field == "employees":  # Gestion du filtre pour employee_id
                query = query.filter(model.Equipement.employees.any(model.Employee.id == value))
            else:
                column_attr = getattr(model.Equipement, field)
                if isinstance(value, str):
                    query = query.filter(column_attr.contains(value))
                elif isinstance(value, int):
                    query = query.filter(column_attr == value)
                elif isinstance(value, list):  # Si la valeur est une liste, on applique un filtre "in"
                    query = query.filter(column_attr.in_(value))
                elif isinstance(value, bool):
                    query = query.filter(column_attr == value)

    return query.order_by(model.Equipement.adresse_ip).offset(skip).all()

def create_equipement(db: Session, equipement: schemas.EquipementCreate):
    db_equipement = model.Equipement(**equipement.dict()
    )
    db.add(db_equipement)
    db.commit()
    db.refresh(db_equipement)
    return db_equipement
def update_equipement(db: Session, equipement_id: int, equipement: schemas.EmployeeCreate):
    db_equipement = db.query(model.Equipement).filter(model.Equipement.equipement_id== equipement_id).first()
    if db_equipement is None:
        return None
    for key, value in equipement.dict().items():
        setattr(db_equipement, key, value)
    db.commit()
    db.refresh(db_equipement)
    return db_equipement

def delete_equipement(db: Session, equipement_id: int):
    db_equipement = db.query(model.Equipement).filter(model.Equipement.equipement_id == equipement_id).first()
    if db_equipement:
        db.delete(db_equipement)
        db.commit()
    return db_equipement


# Acquisition CRUD operations
def get_acquisition(db: Session, acquisition_id: int):
    return db.query(model.Acquisition).options(joinedload(model.Acquisition.contrat)).filter(model.Acquisition.num_acquisition == acquisition_id).first()

def get_acquisitions(db: Session, skip: int = 0, limit: int = 10000000):
    return db.query(model.Acquisition).options(joinedload(model.Acquisition.contrat)).order_by(model.Acquisition.num_acquisition) .offset(skip).limit(limit).all()

def create_acquisition(db: Session, acquisition: schemas.AcquisitionCreate):
    db_acquisition = model.Acquisition(**acquisition.dict())
    db.add(db_acquisition)
    db.commit()
    db.refresh(db_acquisition)
    return db_acquisition
def update_acquisition(db: Session, num_acquisition: int, acquisition_update: schemas.AcquisitionBase):
    db_acquisition = db.query(model.Acquisition).filter(model.Acquisition.num_acquisition == num_acquisition).first()
    if db_acquisition is None:
        return None

    # Mettre à jour les attributs individuels
    for key, value in acquisition_update.dict(exclude_unset=True).items():
        setattr(db_acquisition, key, value)

    db.commit()
    db.refresh(db_acquisition)
    return db_acquisition
def delete_acquisition(db: Session, num_acquisition: int):
    db_acquisition = db.query(model.Acquisition).filter(model.Acquisition.num_acquisition == num_acquisition).first()
    if db_acquisition is None:
        return None

    db.delete(db_acquisition)
    db.commit()
    return db_acquisition
def get_user_by_username(db: Session, username: str):
    return db.query(model.User).filter(model.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password) # type: ignore
    db_user = model.User(username=user.username, password_hashed=hashed_password, role=user.role, statut=user.statut ,employee_id=user.employee_id )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not user.statut:
        return None 
    if not verify_password(password, user.password_hashed):
        return False
    return user

# CRUD for Hyperviseur
def create_hyperviseur(db: Session, hyperviseur: schemas.HyperviseurCreate):
    db_hyperviseur = model.Hyperviseur(**hyperviseur.dict())
    db.add(db_hyperviseur)
    db.commit()
    db.refresh(db_hyperviseur)
    return db_hyperviseur

def get_hyperviseur(db: Session, hyperviseur_id: int):
    return db.query(model.Hyperviseur).filter(model.Hyperviseur.id == hyperviseur_id).first()

def get_hyperviseurs(db: Session, skip: int = 0, filters: Optional[Dict[str, Optional[str]]] = None):
    query = db.query(model.Hyperviseur).order_by(model.Hyperviseur.id)

    if filters:
        if filters.get("nom"):
            query = query.filter(model.Hyperviseur.nom.ilike(f"%{filters['nom']}%"))

    return query.all()
def update_hyperviseur(db: Session, hyperviseur_id: int, hyperviseur: schemas.HyperviseurCreate):
    db_hyperviseur = get_hyperviseur(db, hyperviseur_id)
    if db_hyperviseur is None:
        return None
    for key, value in hyperviseur.dict(exclude_unset=True).items():
        setattr(db_hyperviseur, key, value)
    db.commit()
    db.refresh(db_hyperviseur)
    return db_hyperviseur

def delete_hyperviseur(db: Session, hyperviseur_id: int):
    db_hyperviseur = get_hyperviseur(db, hyperviseur_id)
    if db_hyperviseur is None:
        return None
    db.delete(db_hyperviseur)
    db.commit()
    return db_hyperviseur

# CRUD for MachineVirtuelle
def create_machine_virtuelle(db: Session, machine_virtuelle: schemas.MachineVirtuelleCreate):
    db_machine_virtuelle = model.MachineVirtuelle(**machine_virtuelle.dict())
    db.add(db_machine_virtuelle)
    db.commit()
    db.refresh(db_machine_virtuelle)
    return db_machine_virtuelle

def get_machine_virtuelle(db: Session, vm_id: int):
    return db.query(model.MachineVirtuelle).filter(model.MachineVirtuelle.id_vm == vm_id).first()

def get_machines_virtuelles(db: Session, skip: int = 0, limit: int = 10000000, filters: Dict[str, Any] = {}):
    query = db.query(model.MachineVirtuelle).options(joinedload(model.MachineVirtuelle.applications))
    
    # Appliquer les filtres
    for field, value in filters.items():
        if value is not None:  # Si le filtre a une valeur
            if field == "responsable_id":
                query = query.join(model.MachineVirtuelle.applications).filter(model.Application.responsable_id == value)
            else:
                column = getattr(model.MachineVirtuelle, field, None)
                if column is not None:
                    query = query.filter(column == value)
                else:
                    raise InvalidRequestError(f"Invalid field: {field}")
    
    return query.order_by(model.MachineVirtuelle.id_vm).offset(skip).limit(limit).all()

def update_machine_virtuelle(db: Session, vm_id: int, machine_virtuelle: schemas.MachineVirtuelleCreate):
    db_machine_virtuelle = get_machine_virtuelle(db, vm_id)
    if db_machine_virtuelle is None:
        return None
    for key, value in machine_virtuelle.dict(exclude_unset=True).items():
        setattr(db_machine_virtuelle, key, value)
    db.commit()
    db.refresh(db_machine_virtuelle)
    return db_machine_virtuelle

def delete_machine_virtuelle(db: Session, vm_id: int):
    db_machine_virtuelle = get_machine_virtuelle(db, vm_id)
    if db_machine_virtuelle is None:
        return None
    db.delete(db_machine_virtuelle)
    db.commit()
    return db_machine_virtuelle


###############

def get_application(db: Session, application_id: int):
    return db.query(model.Application).filter(model.Application.id == application_id).first()

def get_applications(db: Session, skip: int = 0, filters: Dict[str, Any] = {}):
    query = db.query(model.Application)
    
    # Appliquer des filtres
    for field, value in filters.items():
        if value:
            if hasattr(model.Application, field):
                attr = getattr(model.Application, field)
                if isinstance(value, str):  # Pour les chaînes de caractères, on peut utiliser 'ilike'
                    query = query.filter(attr.ilike(f"%{value}%"))
                else:
                    query = query.filter(attr == value)
    
    return query.order_by(model.Application.id).offset(skip).all()

def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = model.Application(
        **application.dict()
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def update_application(db: Session, application_id: int, application: schemas.ApplicationCreate):
    db_application = db.query(model.Application).filter(model.Application.id == application_id).first()
    if db_application is None:
        return None
    for var, value in vars(application).items():
        setattr(db_application, var, value) if value else None
    db.commit()
    db.refresh(db_application)
    return db_application

def delete_application(db: Session, application_id: int):
    db_application = db.query(model.Application).filter(model.Application.id == application_id).first()
    if db_application:
        db.delete(db_application)
        db.commit()
    return db_application
#############

def create_license(db: Session, license: schemas.LicenseCreate):
    db_license = model.License(
        **license.dict()
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

def get_license(db: Session, license_id: int):
    return db.query(model.License).filter(model.License.id == license_id).first()

def get_licenses(
    db: Session, 
    skip: int = 0, 
    limit: int = 10,  # Pour limiter le nombre de résultats retournés
    dateDebut: Optional[str] = None,
    dateExpiration: Optional[str] = None,
    type: Optional[str] = None,
    fournisseur: Optional[str] = None,
    statut: Optional[str] = None,
    id_employee: Optional[int] = None,
    id_equipement: Optional[int] = None,
    id_application: Optional[int] = None
):
    # Commencer par une requête de base
    query = db.query(model.License)
    
    # Appliquer les filtres dynamiquement si des valeurs sont fournies
    if dateDebut:
        query = query.filter(model.License.dateDebut == dateDebut)
    if dateExpiration:
        query = query.filter(model.License.dateExpiration == dateExpiration)
    if type:
        query = query.filter(model.License.type == type)
    if fournisseur:
        query = query.filter(model.License.fournisseur == fournisseur)
    if statut:
        query = query.filter(model.License.statut == statut)
    if id_employee:
        query = query.filter(model.License.id_employee == id_employee)
    if id_equipement:
        query = query.filter(model.License.id_equipement == id_equipement)
    if id_application:
        query = query.filter(model.License.id_application == id_application)

    # Retourner les licences avec pagination
    return query.order_by(model.License.id).offset(skip).limit(limit).all()

def update_license(db: Session, license_id: int, license: schemas.LicenseCreate):
    db_license = db.query(model.License).filter(model.License.id == license_id).first()
    
    if db_license:
        for attr, value in vars(license).items():
            setattr(db_license, attr, value)
        
        db.commit()
        db.refresh(db_license)
    
    return db_license

def delete_license(db: Session, license_id: int):

    db_license = db.query(model.License).filter(model.License.id == license_id).first()
    if db_license:
        db.delete(db_license)
        db.commit()
    return db_license

####Cluster
# CRUD operation to create a Cluster
def create_cluster(db: Session, cluster: schemas.ClusterCreate):
    # Créer une instance de Cluster
    db_cluster = model.Cluster(nom=cluster.nom)
    db.add(db_cluster)
    db.commit()
    db.refresh(db_cluster)
    
    # Ajouter les équipements associés
    if cluster.equipements:
        for equipement_id in cluster.equipements:
            equipement = db.query(model.Equipement).filter(model.Equipement.equipement_id == equipement_id).first()
            if equipement:
                equipement.cluster_id = db_cluster.id
                db.add(equipement)
    
    # Ajouter les machines virtuelles associées
    if cluster.machines_virtuelles:
        for vm_id in cluster.machines_virtuelles:
            vm = db.query(model.MachineVirtuelle).filter(model.MachineVirtuelle.id_vm == vm_id).first()
            if vm:
                vm.cluster_id = db_cluster.id
                db.add(vm)
    
    db.commit()
    db.refresh(db_cluster)
    return db_cluster

# CRUD operation to get a Cluster by ID
def get_cluster(db: Session, cluster_id: int):
    return db.query(model.Cluster).filter(model.Cluster.id == cluster_id).first()

# CRUD operation to get all Clusters
def get_clusters(db: Session, skip: int = 0, limit: int = 100000000):
    return db.query(model.Cluster).order_by(model.Cluster.id).offset(skip).limit(limit).all()

# CRUD operation to update a Cluster
def update_cluster(db: Session, cluster_id: int, cluster: schemas.ClusterUpdate):
    db_cluster = db.query(model.Cluster).filter(model.Cluster.id == cluster_id).first()
    if not db_cluster:
        return None
    for key, value in cluster.dict(exclude_unset=True).items():
        setattr(db_cluster, key, value)
    db.commit()
    db.refresh(db_cluster)
    return db_cluster

# CRUD operation to delete a Cluster
def delete_cluster(db: Session, cluster_id: int):
    db_cluster = db.query(model.Cluster).filter(model.Cluster.id == cluster_id).first()
    if db_cluster:
        db.delete(db_cluster)
        db.commit()
    return db_cluster

###########################
def get_user(db: Session, user_id: int):
    return db.query(model.User).filter(model.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(model.User).order_by(model.User.id).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(model.User).filter(model.User.id == user_id).first()
    if not db_user:
        return None
    
    # Vérifier si le mot de passe a été fourni pour la mise à jour
    if user.password_hashed:
        hashed_password = get_password_hash(user.password_hashed)
        db_user.password_hashed = hashed_password

    # Mettre à jour les autres champs
    if user.username is not None:
        db_user.username = user.username
    if user.role is not None:
        db_user.role = user.role
    if user.statut is not None:
        db_user.statut = user.statut

    db.commit()
    db.refresh(db_user)
    return db_user
def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user
def deactivate_user(db: Session, user_id: int):
    db_user = db.query(model.User).filter(model.User.id == user_id).first()
    if db_user:
        db_user.statut = False
        db.commit()
        db.refresh(db_user)
        return db_user
    return None
def activate_user(db: Session, user_id: int):
    db_user = db.query(model.User).filter(model.User.id == user_id).first()
    if db_user:
        db_user.statut = True
        db.commit()
        db.refresh(db_user)
        return db_user
    return None
