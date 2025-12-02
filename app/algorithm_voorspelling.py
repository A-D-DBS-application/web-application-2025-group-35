from datetime import date, timedelta
from .models import Verhuur, LeeftijdEnum, StatusEnum

def voorspelde_drukte():
    """Voorspel toekomstige vraag per leeftijdscategorie"""
    vandaag = date.today()
    toekomstige_vraag = {lev.value: 0 for lev in LeeftijdEnum}

    # Filter alleen actieve verhuren
    actieve_verhuren = Verhuur.query.filter_by(status="Actief").all()

    for verh in actieve_verhuren:
        kind = verh.kind
        if not kind: 
            continue

        # Huidige leeftijd en categorie
        leeftijd = kind.leeftijd
        huidige_categorie = None
        for cat in LeeftijdEnum:
            min_l, max_l = leeftijd_splitsen(cat.value)
            if min_l <= leeftijd <= max_l:
                huidige_categorie = cat
                break
        if not huidige_categorie:
            continue

        # Bereken toekomstige leeftijd over 6 maanden
        maanden_toekomst = 6
        toekomstige_leeftijd = leeftijd + (maanden_toekomst / 12)
        toekomstige_categorie = None
        for cat in LeeftijdEnum:
            min_l, max_l = leeftijd_splitsen(cat.value)
            if min_l <= toekomstige_leeftijd <= max_l:
                toekomstige_categorie = cat
                break

        if toekomstige_categorie:
            toekomstige_vraag[toekomstige_categorie.value] += 1

    return toekomstige_vraag

# Hergebruik de functie uit algorithm.py
from .algorithm import leeftijd_splitsen
