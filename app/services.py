# services.py
from .models import db, Kind, Item, StatusEnum, VerhuurStatusEnum,Adres, LeeftijdEnum, Verantwoordelijke,Betaling
from sqlalchemy import nulls_last, or_
from datetime import datetime
from flask import flash, redirect

# ---------------------- KLANTEN ----------------------

def update_kinderen(klant, ids, namen, datums):
    bestaande = {k.kind_id: k for k in klant.kinderen}
    ontvangen = set()
    
    kinderen_te_verwijderen = [] 

    for kid_str, naam, datum_str in zip(ids, namen, datums):
        datum = parse_date_form(datum_str)

        if kid_str: 
            try:
                kid = int(kid_str)
                ontvangen.add(kid)
                
                
                if kid in bestaande:
                    k = bestaande[kid]
                    k.naam = naam
                    k.geboortedatum = datum 
            except ValueError:
                
                continue

        else:  
            if naam.strip() and datum:
                nieuw = Kind(
                    naam=naam,
                    geboortedatum=datum, 
                    verantwoordelijke_id=klant.verantwoordelijke_id
                )
                db.session.add(nieuw)

   
    for kind_id, kind_object in bestaande.items():
        if kind_id not in ontvangen:
            
           
            if db.session.query(Betaling).filter_by(kind_id=kind_id).first():
                
                flash(f"Kan kind '{kind_object.naam}' niet verwijderen: er zijn betalingen gekoppeld.", "error")
            else:
                
                kinderen_te_verwijderen.append(kind_object)
    
    for kind in kinderen_te_verwijderen:
        db.session.delete(kind)


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

def prepare_klant_kind_data(query):
    klant_kind_data = {}

    for v in query:
        kinderen_list = []
        for k in v.kinderen:
            kinderen_list.append({
                "id": k.kind_id,
                "naam": k.naam,
                "leeftijd": k.leeftijd,
                "geboortedatum": k.geboortedatum.isoformat(),
                "heeft_betalingen": bool(k.betalingen),
            })
        klant_kind_data[v.verantwoordelijke_id] = kinderen_list

    return klant_kind_data
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