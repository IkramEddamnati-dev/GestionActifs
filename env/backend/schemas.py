from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from enum import Enum as PyEnum

class RackGroupBase(BaseModel):
    rackGroup_name: str
    

class RackGroupCreate(RackGroupBase):
    pass

class RackGroupUpdate(RackGroupBase):
    pass

class RackGroupInDBBase(RackGroupBase):
    rackGroup_uid: int
    racks: Optional[List['RackInDBBase']] = []

    class Config:
        orm_mode = True

class RackGroup(RackGroupInDBBase):
    pass
class RackGroupInDB(RackGroupInDBBase):
    pass

class RackBase(BaseModel):
    rack_name: str
    marque: Optional[str]
    numSerie: Optional[str]
    nombreUnites: Optional[str]
    miseEnService: Optional[str]
    refAchat: Optional[str]
    constructeur: Optional[str]
    dateAchat: Optional[str]
    emplacement: str
class RackCreate(RackBase):
    rackGroupId: int
    Equipements: Optional[List[int]] = None


class RackUpdate(RackBase):
    pass

class RackInDBBase(RackBase):
    rack_uid: int

    class Config:
        orm_mode = True

class Rack(RackInDBBase):
    rack_group: Optional[RackGroup] = None
    Equipements: Optional[List['Equipement']] = []

class RackInDB(RackInDBBase):
    pass

class MaintenanceBase(BaseModel):
    prestataireMaintenance: Optional[str] = None
    dateDebutMaintenance: Optional[datetime] = None
    dateFinMaintenance: Optional[datetime] = None
    typeMaintenance: Optional[str] = None
    dateDePanne:Optional[datetime] = None
    description: Optional[str] = None
    equipement_id: Optional[int] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(MaintenanceBase):
    pass

class MaintenanceInDB(MaintenanceBase):
    id: int
    equipement: Optional["EquipementBase"] = []


    class Config:
        orm_mode = True
class ContratBase(BaseModel):
    num_contrat: str
    dateAchat: date
    dateExpiration: Optional[date] = None
    montant: Optional[float] = None
    fournisseur: str
    description: Optional[str] = None

class ContratCreate(ContratBase):
    pass

class Contrat(ContratBase):
    id: int
    acquisition: Optional["Acquisition"] = []

    class Config:
        orm_mode = True

class EventBase(BaseModel):
    date: datetime
    statut: str
    acquisition_id:Optional[int]=None
class EventCreate(EventBase):
    date: datetime
    statut: str
    acquisition_id:Optional[int]=None
    pass

class EventInDB(EventBase):
    id: int

    class Config:
        orm_mode = True

class AcquisitionBase(BaseModel):
    type: str
    budget: float
    dateAchat: date
    fournisseur: str
    statut: str
    contrat_id: Optional[int] = None


class AcquisitionCreate(AcquisitionBase):
    pass

class Acquisition(AcquisitionBase):
    num_acquisition: int
    contrat: Optional[ContratBase] = None
    events: Optional[List[EventBase]] = []
    equipements:Optional[List["EquipementBase"]] = []

    class Config:
        orm_mode = True
        
class UserCreate(BaseModel):
    username: str
    password: str
    role: str | None = None
    statut:bool | None = None
    employee_id:int | None=None

class UserOut(BaseModel):
    id: int
    username: str
    role: str | None
    employee_id:int | None=None

    class Config:
        orm_mode = True

class UserRead(BaseModel):
    id: int
    username: str
    password_hashed:str
    role: Optional[str] = None
    statut: Optional[bool] = None
    employee_id: Optional[int] = None
    employee: Optional['EmployeeBase'] = None

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password_hashed: Optional[str] = None
    role: Optional[str] = None
    statut: Optional[bool] = None
    employee_id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
class EquipementBase(BaseModel):
    equipement_id: int

    type: str
    adresse_ip: str
    status: bool
    nom: str
    num_serie: int
    codeBar: str
    quantite:int
    marque: str
    modele: str
    dateMiseService: datetime
    rackable: bool
    responsable: str
    systemeInstalle: Optional[str] = None
    nombreUniteOccRack: Optional[int] = None
    nombreLecteur: Optional[int] = None
    nombreBonde: Optional[int] = None
    stockage: Optional[str] = None
    ram: Optional[int] = None
    cpu: Optional[int] = None
    refAchat: str
    numContratMaint: int
    prestataireMaintenance: Optional[str] = None
    dateDebutMaintenance: Optional[datetime] = None
    dateFinMaintenance: Optional[datetime] = None
    typeMaintenance: Optional[str] = None
    num_acquisition: int
    cluster_id: Optional[int] = None
    rackId : Optional[int] = None


class EquipementCreate(BaseModel):
    type: str
    adresse_ip: str
    status: bool
    nom: str
    num_serie: int
    codeBar: str
    quantite:int
    marque: str
    modele: str
    dateMiseService: datetime
    rackable: bool
    responsable: str
    systemeInstalle: Optional[str] = None
    nombreUniteOccRack: Optional[int] = None
    nombreLecteur: Optional[int] = None
    nombreBonde: Optional[int] = None
    stockage: Optional[str] = None
    ram: Optional[int] = None
    cpu: Optional[int] = None
    refAchat: str
    numContratMaint: int
    prestataireMaintenance: Optional[str] = None
    dateDebutMaintenance: Optional[datetime] = None
    dateFinMaintenance: Optional[datetime] = None
    typeMaintenance: Optional[str] = None
    num_acquisition: int
    cluster_id: Optional[int] = None
    rackId : Optional[int] = None

class Equipement(EquipementBase):
    equipement_id: int
    acquisition: Optional['Acquisition'] = []
    cluster:Optional['ClusterBase'] = None
    employees:Optional[list['Employee1']]=[]
    rack:Optional['RackBase'] = None


    class Config:
        orm_mode = True






class EmployeeEquipementAssociationBase(BaseModel):

    status: bool
    date_affectation: datetime
    date_desaffectation: Optional[datetime] = None
    employee_id: int
    equipement_id: int
class EmployeeEquipementAssociationCreate(EmployeeEquipementAssociationBase):
   pass

class EmployeeEquipementAssociation(EmployeeEquipementAssociationBase):
    id: int
    
    
    class Config:
        orm_mode = True


class HyperviseurBase(BaseModel):
    nom: str

class Hyperviseur(HyperviseurBase):
    id: int
    serveur_physique_id: int
    machines_virtuelles: list['MachineVirtuelle'] = []
    serveur_physique:Optional['Equipement']=None

    class Config:
        orm_mode = True
class HyperviseurCreate(BaseModel):
    nom: str
    serveur_physique_id: int

class MachineVirtuelleBase(BaseModel):
    id_vm: int
    nom:str
    stockage: str
    ram: str
    cpu: str
    OS: Optional[ str]=None
    nom_domaine: Optional[ str]=None
    domaine: Optional[ str]=None
    ip_adresse: Optional[ str]=None
    dateExpirationSupportOS: Optional[datetime]=None
    dateExpirationSupportOSEtendue:Optional[datetime]=None
    networkEgenet: Optional[bool]=None
    antivirus:  Optional[bool]=None
    cluster:Optional[ "ClusterBase"]=None


class MachineVirtuelle(MachineVirtuelleBase):
    id_vm: int
    hyperviseur_id: int
    hyperviseur: Optional[HyperviseurBase]=None

    cluster_id:Optional[ int]=None
    applications: list['Application'] = []

    class Config:
        orm_mode = True
class MachineVirtuelleCreate(BaseModel):
    nom:str
    stockage: str
    ram: str
    cpu: str
    OS: Optional[ str]=None
    nom_domaine: Optional[ str]=None
    domaine: Optional[ str]=None
    ip_adresse: Optional[ str]=None
    dateExpirationSupportOS: Optional[datetime]=None
    dateExpirationSupportOSEtendue:Optional[datetime]=None
    networkEgenet: Optional[bool]=None
    antivirus:  Optional[bool]=None
    hyperviseur_id: int
    cluster_id:Optional[ int]=None

class ApplicationBase(BaseModel):
    nom: str
    description: str
    responsable_id: Optional[int] = None
    nom_domaine: Optional[str]=None
    serveurDb: Optional[str]=None
    versionServeurDB: Optional[str]=None
    dateFinSupport: Optional[datetime]=None
    dateFinSupportEtendue:Optional[datetime]=None
    serveurWeb: Optional[str]=None
    serveur_physique_id: Optional[int] = None
    machine_virtuelle_id: Optional[int] = None

class Application(ApplicationBase):
    id: int
    serveur_physique_id: Optional[int] = None
    machine_virtuelle_id: Optional[int] = None

    license: Optional[list['LicenseBase2']] = []
    serveur_physique: Optional['EquipementBase'] = None
    machine_virtuelle: Optional['MachineVirtuelleBase'] = None
    responsable:Optional['Employee1'] = None


    class Config:
        orm_mode = True
class ApplicationCreate(BaseModel):
    nom: str
    description: str
    responsable_id: int
    nom_domaine: Optional[str]=None
    serveurDb: Optional[str]=None
    versionServeurDB: Optional[str]=None
    dateFinSupport: Optional[datetime]=None
    dateFinSupportEtendue:Optional[datetime]=None
    serveurWeb: Optional[str]=None
    serveur_physique_id: Optional[int] = None
    machine_virtuelle_id: Optional[int] = None
# Schéma pour Employee
class EmployeeBase(BaseModel):
    matricule: str
    nom: str
    service: str

class EmployeeCreate(EmployeeBase):
    matricule: str
    nom: str
    service: str

class Employee(EmployeeBase):
    id: int
    equipements: List[Equipement] = []
    licenses: Optional[list['LicenseBase3']] = []

    class Config:
        orm_mode = True



class Employee1(EmployeeBase):
    id: int

    class Config:
        orm_mode = True

class LicenseBase(BaseModel):
    dateDebut: str
    dateExpiration: str
    key: str
    type: str
    nombreUtilisations: Optional[int] = None
    utilisationsRestantes: Optional[int] = None
    dateRenouvellement: Optional[str] = None
    fournisseur: Optional[str] = None
    cout: Optional[float] = None
    statut: Optional[str] = None
    renouvellementAutomatique: Optional[bool] = False
    id_employee: Optional[int] = None
    id_equipement: Optional[int] = None
    id_application: Optional[int] = None

class License(LicenseBase):
    id: int
    employee:Optional[Employee]=[]
    application:Optional[Application]=None
    equipement:Optional[Equipement]=[]
    class Config:
        orm_mode = True

class LicenseCreate(BaseModel):
    dateDebut: str
    dateExpiration: str
    key: str
    type: str
    nombreUtilisations: Optional[int] = None
    dateRenouvellement: Optional[str] = None
   
    utilisationsRestantes: Optional[int] = None
    fournisseur: Optional[str] = None
    cout: Optional[float] = None
    statut: Optional[str] = None
    renouvellementAutomatique: Optional[bool] = False
    id_employee: Optional[int] = None
    id_equipement: Optional[int] = None
    id_application: Optional[int] = None

class LicenseBase2(BaseModel):
    id: int

    dateDebut: str
    dateExpiration: str
    key: str
    type: str
    nombreUtilisations: Optional[int] = None
    utilisationsRestantes: Optional[int] = None
    dateRenouvellement: Optional[str] = None
    fournisseur: Optional[str] = None
    cout: Optional[float] = None
    statut: Optional[str] = None
    renouvellementAutomatique: Optional[bool] = False
    id_employee: Optional[int] = None
    id_equipement: Optional[int] = None
    id_application: Optional[int] = None
class LicenseBase3(BaseModel):
    id: int

    dateDebut: str
    dateExpiration: str
    key: str
    type: str
    nombreUtilisations: Optional[int] = None
    utilisationsRestantes: Optional[int] = None
    dateRenouvellement: Optional[str] = None
    fournisseur: Optional[str] = None
    cout: Optional[float] = None
    statut: Optional[str] = None
    renouvellementAutomatique: Optional[bool] = False
    id_equipement: Optional[int] = None
    id_application: Optional[int] = None
# Base schema with shared fields
class ClusterBase(BaseModel):
    nom: str
# Schema for creating a new Cluster
class ClusterCreate(ClusterBase):
    equipements: Optional[List[int]] = None
    machines_virtuelles: Optional[List[int]] = None


# Schema for updating an existing Cluster
class ClusterUpdate(ClusterBase):
    pass

class ClusterRead(ClusterBase):
    id: int
    equipements: Optional[List[EquipementBase] ]= None
    machines_virtuelles:Optional[List[MachineVirtuelleBase] ]= None

    class Config:
        orm_mode = True
# Forward reference update
Employee.update_forward_refs()
