# services.py
from .models import db, Kind, Item, StatusEnum, VerhuurStatusEnum,Adres, LeeftijdEnum, Verantwoordelijke
from sqlalchemy import nulls_last, or_
from datetime import datetime
from flask import flash, redirect

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


#   ---------------------- PAGINATIE ----------------------
def paginatie(query, page, per_page=20):
    total = query.count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    pages = (total + per_page - 1) // per_page
    return items, total, pages


# ---------------------- FIETSEN ZOEKEN ----------------------
def filter_fietsen_query(query, search_query):
    """Past de zoekfilters toe op de Item (fietsen) query."""
    if search_query:
        search_term = f"%{search_query}%"
        search_upper = search_query.upper()
        
        query = query.filter(
            or_(
                Item.merk.ilike(search_term),
                Item.model.ilike(search_term),
            )
        )
    return query


# ---------------------- KLANTEN ZOEKEN ----------------------
def filter_klanten_query(query, search_query):
    """Past de zoekfilters toe op de Verantwoordelijke (klanten) query."""
    if search_query:
        search_term = f"%{search_query}%"
        
        # JOIN Kind en Adres alvorens te filteren
        query = query.join(Adres).join(Kind, isouter=True)
        
        query = query.filter(
            or_(
                # Verantwoordelijke
                Verantwoordelijke.voornaam.ilike(search_term),
                Verantwoordelijke.achternaam.ilike(search_term),
                Verantwoordelijke.email.ilike(search_term),
                
                # Adres
                Adres.straat.ilike(search_term),
                Adres.gemeente.ilike(search_term),

                # Kind
                Kind.naam.ilike(search_term) 
            )
        )
        # Zorg ervoor dat elke klant slechts één keer verschijnt
        query = query.distinct()
        
    return query

def prepare_klant_kind_data():
    """Haalt alle verantwoordelijken op en structureert hun kindgegevens."""
    verantwoordelijken = Verantwoordelijke.query.all()
    
    klant_kind_data = {
        v.verantwoordelijke_id: [{
            "id": k.kind_id,
            "naam": k.naam,
            "leeftijd": k.leeftijd,
            "geboortedatum": k.geboortedatum.isoformat(),
        } for k in v.kinderen]
        for v in verantwoordelijken
    }
    return verantwoordelijken, klant_kind_data

def get_enum_or_none(enum_klasse, form_value):
    
    if form_value:
        try:
            return enum_klasse[form_value]
        except KeyError:
            return None
    return None

def parse_date_form(date_string, date_format="%Y-%m-%d"):
    
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, date_format).date()
    except ValueError:
        return None
    


def validate_and_parse_extension_date(form_date_string, old_end_date):
    try:
        nieuwe_datum = datetime.strptime(form_date_string, "%Y-%m-%d").date()
    except ValueError:
        flash("Ongeldige datum.", "error")
        return redirect("/verhuur"), None # Retourneer de redirect

    if nieuwe_datum <= old_end_date:
        flash("Nieuwe einddatum moet later zijn.", "error")
        return redirect("/verhuur"), None # Retourneer de redirect

    return None, nieuwe_datum # Geen fout, retourneer de nieuwe datum