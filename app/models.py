from flask_sqlalchemy import SQLAlchemy 
from datetime import date
from enum import Enum

db = SQLAlchemy()

# -----------------------------------------------------
# ENUMS
# -----------------------------------------------------

class StatusEnum(Enum):
    BESCHIKBAAR = "beschikbaar"
    VERHUURD = "uitgeleend"
    ONDERHOUD = "op onderhoud"


class LeeftijdEnum(Enum):
    LOOPFIETSEN = "1 - 4 jaar loopfietsen"
    PEUTER = "2 - 3 jaar"
    KLEUTER = "4 - 6 jaar"
    JUNIOR = "6 - 8 jaar"
    KIDS = "8 - 12 jaar"
    TEEN = "14 - 16 jaar"
    OUDER_DAN_16 = "Ouder dan 16 jaar"



class BetalingswijzeEnum(Enum):
    CONTANT = "Contant"
    KAART = "Kaart"
    OVERSCHRIJVEN_VOLDAAN = "Overschrijven voldaan"
    OVERSCHRIJVEN_NIET_VOLDAAN = "Overschrijven niet voldaan"


class VerhuurStatusEnum(Enum):
    ACTIEF = "Actief"
    BEEINDIGD = "Beëindigd"


# Helper so SQLAlchemy uses enum.value instead of enum.name
ENUM_VALUES = lambda enum: [e.value for e in enum]


# -----------------------------------------------------
# MODELLEN
# -----------------------------------------------------

class Adres(db.Model):
    __tablename__ = 'adres'

    adres_id = db.Column(db.Integer, primary_key=True)
    straat = db.Column(db.Text, nullable=False)
    huisnummer = db.Column(db.String(20), nullable=False)
    postcode = db.Column(db.Integer, nullable=False)   # Tip: maak dit String(10)
    gemeente = db.Column(db.Text, nullable=False)
    land = db.Column(db.Text, nullable=False)

    # FIXED: correct spelling
    verantwoordelijken = db.relationship("Verantwoordelijke", backref="adres", lazy=True)


class Verantwoordelijke(db.Model):
    __tablename__ = 'verantwoordelijke'

    verantwoordelijke_id = db.Column(db.Integer, primary_key=True)
    voornaam = db.Column(db.Text, nullable=False)
    achternaam = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    adres_id = db.Column(db.Integer, db.ForeignKey("adres.adres_id"), nullable=False)

    kinderen = db.relationship("Kind", backref="verantwoordelijke", lazy=True)
    items = db.relationship("Item", backref="verantwoordelijke", lazy=True)


class Kind(db.Model):
    __tablename__ = "kind"

    kind_id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.Text, nullable=False)
    geboortedatum = db.Column(db.Date, nullable=False)
    verantwoordelijke_id = db.Column(db.Integer, db.ForeignKey("verantwoordelijke.verantwoordelijke_id"), nullable=False)

    @property
    def leeftijd(self):
        today = date.today()
        return (
            today.year
            - self.geboortedatum.year
            - ((today.month, today.day) < (self.geboortedatum.month, self.geboortedatum.day))
        )


class Item(db.Model):
    __tablename__ = 'item'

    itemnr = db.Column(db.Integer, primary_key=True)

    # NEW: correct and consistent with Supabase
    merk = db.Column(db.Text, nullable=False)
    model = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.Enum(StatusEnum, values_callable=ENUM_VALUES),
        nullable=False,
        default=StatusEnum.BESCHIKBAAR.value
    )

    verantwoordelijke_id = db.Column(db.Integer, db.ForeignKey('verantwoordelijke.verantwoordelijke_id'))
    leeftijdscategorie = db.Column(
        db.Enum(LeeftijdEnum, values_callable=ENUM_VALUES),
        nullable=True
    )


class Betaling(db.Model):
    __tablename__ = "betaling"

    id = db.Column(db.Integer, primary_key=True)
    itemnr = db.Column(db.Integer, db.ForeignKey("item.itemnr"), nullable=False)
    kind_id = db.Column(db.Integer, db.ForeignKey("kind.kind_id"), nullable=False)

    betalingswijze = db.Column(
        db.Enum(BetalingswijzeEnum, values_callable=ENUM_VALUES),
        nullable=False
    )

    bedrag = db.Column(db.Float, nullable=False)
    datum = db.Column(db.Date, nullable=False)
    tijd = db.Column(db.Time, nullable=False)


# -----------------------------------------------------
# VERHUUR
# -----------------------------------------------------

class Verhuur(db.Model):
    __tablename__ = "verhuur"   # Correct for Supabase

    verhuur_id = db.Column(db.Integer, primary_key=True)
    itemnr = db.Column(db.Integer, db.ForeignKey("item.itemnr"), nullable=False)
    kind_id = db.Column(db.Integer, db.ForeignKey("kind.kind_id"), nullable=False)
    verantwoordelijke_id = db.Column(db.Integer, db.ForeignKey("verantwoordelijke.verantwoordelijke_id"), nullable=False)

    startdatum = db.Column(db.Date, nullable=False)
    einddatum = db.Column(db.Date, nullable=False)

    status = db.Column(
        db.Enum(VerhuurStatusEnum, values_callable=ENUM_VALUES),
        nullable=False,
        default=VerhuurStatusEnum.ACTIEF.value
    )

    # Relationships (sqlalchemy handles backrefs)
    item = db.relationship("Item")
    kind = db.relationship("Kind")
    verantwoordelijke = db.relationship("Verantwoordelijke")







