from datetime import datetime
from sqlalchemy import Enum,Column, Date, DateTime, ForeignKey, Integer, String, Boolean, Float, Table, Text
from sqlalchemy.orm import relationship, declarative_base
from enum import Enum as PyEnum

Base = declarative_base()
employee_equipement_association = Table(
    'employee_equipement_association',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('status', Boolean),
    Column('date_affectation', DateTime),
    Column('date_desaffectation', DateTime, nullable=True),
    Column('employee_id', Integer, ForeignKey('employee.id')),
    Column('equipement_id', Integer, ForeignKey('equipements.equipement_id'))
)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, unique=True)
    password_hashed = Column(Text, nullable=False)
    role = Column(Text, nullable=True)
    statut= Column(Boolean, nullable=True)
    employee_id = Column(Integer, ForeignKey("employee.id"))
    employee = relationship("Employee", back_populates="user")

class Employee(Base):
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True, index=True)
    matricule = Column(String)
    nom = Column(String)
    service = Column(String)
    equipements = relationship("Equipement", secondary=employee_equipement_association, back_populates="employees")
    licenses = relationship("License", back_populates="employee")
    user = relationship("User", back_populates="employee")
    applications_responsables = relationship("Application", back_populates="responsable")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    description = Column(String)
    nom_domaine = Column(String)
    serveurDb = Column(String)
    versionServeurDB = Column(String)
    dateFinSupport = Column(Date)
    dateFinSupportEtendue = Column(Date)
    serveurWeb = Column(String)
    
    # ForeignKey to Employee for the responsable
    responsable_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    responsable = relationship("Employee", back_populates="applications_responsables")

    # ForeignKey and relationship with Equipement (Serveur Physique)
    serveur_physique_id = Column(Integer, ForeignKey("equipements.equipement_id"), nullable=True)
    serveur_physique = relationship("Equipement", back_populates="applications")
    
    # ForeignKey and relationship with MachineVirtuelle
    machine_virtuelle_id = Column(Integer, ForeignKey("machines_virtuelles.id_vm"), nullable=True)
    machine_virtuelle = relationship("MachineVirtuelle", back_populates="applications")

    # Relationship with License (one-to-one)
    license = relationship("License", back_populates="application", uselist=True)

class Maintenance(Base):
    __tablename__ = "maintenances"
    id = Column(Integer, primary_key=True, index=True)
    prestataireMaintenance = Column(String, nullable=True)
    dateDePanne = Column(Date, nullable=True)
    dateDebutMaintenance = Column(Date, nullable=True)
    dateFinMaintenance = Column(Date, nullable=True)
    typeMaintenance = Column(String, nullable=True)
    description = Column(String, nullable=True)
    equipement_id=Column(Integer, ForeignKey("equipements.equipement_id"))
    equipement = relationship("Equipement", back_populates="maintenances")

class Equipement(Base):
    __tablename__ = "equipements"
    equipement_id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    adresse_ip = Column(String)
    status = Column(Boolean)
    quantite=Column(Integer)
    nom = Column(String)
    num_serie = Column(Integer)
    codeBar = Column(String)
    marque = Column(String)
    modele = Column(String)
    dateMiseService = Column(Date)
    rackable = Column(Boolean)
    responsable = Column(String)
    systemeInstalle = Column(String, nullable=True)
    nombreUniteOccRack = Column(Integer, nullable=True)
    nombreLecteur = Column(Integer, nullable=True)
    nombreBonde = Column(Integer, nullable=True)
    stockage = Column(String, nullable=True)
    ram = Column(Integer, nullable=True)
    cpu = Column(Integer, nullable=True)
    refAchat = Column(String)
    numContratMaint = Column(Integer)
    prestataireMaintenance = Column(String, nullable=True)
    dateDebutMaintenance = Column(Date, nullable=True)
    dateFinMaintenance = Column(Date, nullable=True)
    typeMaintenance = Column(String, nullable=True)
    rackId = Column(Integer, ForeignKey("Rack.rack_uid"), nullable=True)
    rack = relationship("Rack", back_populates="Equipements")
    # Relationship with Cluster
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    cluster = relationship("Cluster", back_populates="equipements")
    licenses = relationship("License", back_populates="equipement")

    # Relationship with Acquisition
    num_acquisition = Column(Integer, ForeignKey("acquisition.num_acquisition"))
    acquisition = relationship("Acquisition", back_populates="equipements")
    
    # Relationship with Employee
    employees = relationship("Employee", secondary=employee_equipement_association, back_populates="equipements")
    
    # Relationship with Hyperviseur and Application
    hyperviseur = relationship("Hyperviseur", back_populates="serveur_physique")
    applications = relationship("Application", back_populates="serveur_physique")
    maintenances = relationship("Maintenance", back_populates="equipement")

class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    
    # Relationship with Equipement
    equipements = relationship("Equipement", back_populates="cluster")
    
    # Relationship with MachineVirtuelle
    machines_virtuelles = relationship("MachineVirtuelle", back_populates="cluster")
class MachineVirtuelle(Base):
    __tablename__ = "machines_virtuelles"
    id_vm = Column(Integer, primary_key=True, index=True)
    nom=Column(String)
    stockage = Column(String(50))
    ram = Column(String(50))
    cpu = Column(String(50))
    OS = Column(String, nullable=True)
    nom_domaine = Column(String, nullable=True)
    domaine = Column(String, nullable=True)
    ip_adresse = Column(String, nullable=True)
    dateExpirationSupportOS = Column(DateTime, nullable=True)
    dateExpirationSupportOSEtendue = Column(DateTime, nullable=True)
    networkEgenet = Column(Boolean, nullable=True, default=False)
    antivirus = Column(Boolean, nullable=True, default=False)
    # ForeignKey and relationship with Hyperviseur
    hyperviseur_id = Column(Integer, ForeignKey("hyperviseur.id"))
    hyperviseur = relationship("Hyperviseur", back_populates="machines_virtuelles")
    
    # ForeignKey and relationship with Cluster
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    cluster = relationship("Cluster", back_populates="machines_virtuelles")
    
    # Relationship with Application
    applications = relationship("Application", back_populates="machine_virtuelle")

class Contrat(Base):
    __tablename__ = "contrat"
    
    id = Column(Integer, primary_key=True, index=True)
    num_contrat = Column(String(255), nullable=False, unique=True)  # Numéro de contrat
    dateAchat = Column(Date, nullable=False)  # Date de l'achat
    dateExpiration = Column(Date)  # Date d'expiration du contrat
    montant = Column(Float)  # Montant du contrat
    fournisseur = Column(String, nullable=False)  # Fournisseur lié au contrat
    description=Column(String)
    # Relation avec les acquisitions
    acquisition = relationship("Acquisition",uselist=False, back_populates="contrat")

class Acquisition(Base):

    __tablename__ = "acquisition"
    num_acquisition = Column(Integer, primary_key=True, index=True)
    type=Column(String,nullable=False)
    budget = Column(Float)
    dateAchat = Column(Date, nullable=False) 
    fournisseur = Column(String, nullable=False) 
    statut = Column(String, default="En cours")  
    equipements = relationship("Equipement", back_populates="acquisition")
    contrat_id = Column(Integer, ForeignKey("contrat.id"))
    events = relationship("Event", back_populates="acquisition", cascade="all, delete-orphan")

    contrat = relationship("Contrat",uselist=False, back_populates="acquisition", lazy='joined')
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    acquisition_id = Column(Integer, ForeignKey("acquisition.num_acquisition"), nullable=False)
    statut = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    acquisition = relationship("Acquisition", back_populates="events")

class Hyperviseur(Base):
    __tablename__ = "hyperviseur"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    
    # Relationship with Equipement (Serveur Physique)
    serveur_physique_id = Column(Integer, ForeignKey("equipements.equipement_id"))
    serveur_physique = relationship("Equipement", back_populates="hyperviseur")
    
    # Relationship with MachineVirtuelle
    machines_virtuelles = relationship("MachineVirtuelle", back_populates="hyperviseur")


class License(Base):
    __tablename__ = 'licenses'
    
    id = Column(Integer, primary_key=True, index=True)
    dateDebut = Column(String)
    dateExpiration = Column(String)
    key = Column(String)
    type = Column(String)
    nombreUtilisations = Column(Integer, nullable=True)  # Pertinent pour les licences par volume
    utilisationsRestantes = Column(Integer, nullable=True)  # Pertinent pour les licences par volume
    fournisseur = Column(String)
    cout = Column(Float)
    statut = Column(String)
    renouvellementAutomatique = Column(Boolean, default=False)
    dateRenouvellement = Column(String, nullable=True)

    # ForeignKey and relationship with Application (one-to-one)
    id_application = Column(Integer, ForeignKey('applications.id'), nullable=True)
    application = relationship("Application", back_populates="license")
    
    # ForeignKey and relationship with Equipement (one-to-many)
    id_equipement = Column(Integer, ForeignKey('equipements.equipement_id'), nullable=True)
    equipement = relationship("Equipement", back_populates="licenses")

    # ForeignKey and relationship with Employee (one-to-many)
    id_employee = Column(Integer, ForeignKey('employee.id'), nullable=True)
    employee = relationship("Employee", back_populates="licenses")


class RackGroup(Base):
    __tablename__ = "RackGroup"
    rackGroup_uid = Column(Integer, primary_key=True, index=True)
    rackGroup_name = Column(String(255), index=True)
    rack = relationship("Rack", back_populates="rack_group")

class Rack(Base):
    __tablename__ = "Rack"
    rack_uid = Column(Integer, primary_key=True, index=True)
    rackGroupId = Column(Integer, ForeignKey("RackGroup.rackGroup_uid"))
    rack_name = Column(String(255), index=True)
    marque = Column(String)
    numSerie = Column(String)
    nombreUnites = Column(String)
    miseEnService = Column(String)
    refAchat = Column(String)
    constructeur = Column(String)
    dateAchat = Column(String)
    emplacement = Column(String)

    rack_group = relationship("RackGroup", back_populates="rack")
    Equipements = relationship("Equipement", back_populates="rack")
    
