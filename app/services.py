# services.py
from .models import db, Kind, Item, StatusEnum, VerhuurStatusEnum

# ---------------------- KLANTEN ----------------------

def update_kinderen(klant, ids, namen, datums):
    """Synchronise kinderen (toevoegen / bewerken / verwijderen)."""
    bestaande = {k.kind_id: k for k in klant.kinderen}
    ontvangen = set()

    for kid, naam, datum in zip(ids, namen, datums):
        if kid:  # bestaand kind
            kid = int(kid)
            ontvangen.add(kid)
            k = bestaande[kid]
            k.naam = naam
            k.geboortedatum = datum
        else:  # nieuw kind
            if naam.strip():
                nieuw = Kind(
                    naam=naam,
                    geboortedatum=datum,
                    verantwoordelijke_id=klant.verantwoordelijke_id
                )
                db.session.add(nieuw)

    # verwijder kinderen die niet meer in formulier zitten
    for kid in list(bestaande.keys()):
        if kid not in ontvangen:
            db.session.delete(bestaande[kid])


# ---------------------- FIETSEN ----------------------

def set_fiets_verhuurd(fiets, verantwoordelijke_id):
    fiets.status = StatusEnum.VERHUURD
    fiets.verantwoordelijke_id = verantwoordelijke_id

def set_fiets_beschikbaar(fiets):
    fiets.status = StatusEnum.BESCHIKBAAR
    fiets.verantwoordelijke_id = None


# ---------------------- VERHUUR ----------------------

def verleng_verhuur(verh, nieuwe_datum):
    verh.einddatum = nieuwe_datum
    db.session.commit()