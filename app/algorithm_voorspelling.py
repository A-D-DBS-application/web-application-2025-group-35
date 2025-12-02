from .models import Verhuur
from datetime import date

def leeftijdscategorie(leeftijd):
    if leeftijd <= 4:
        return "1 - 4 jaar (loopfietsen)"
    elif 2 <= leeftijd <= 3:
        return "2 - 3 jaar"
    elif 4 <= leeftijd <= 6:
        return "4 - 6 jaar"
    elif 6 <= leeftijd <= 8:
        return "6 - 8 jaar"
    elif 8 <= leeftijd <= 12:
        return "8 - 12 jaar"
    elif 14 <= leeftijd <= 16:
        return "14 - 16 jaar"
    else:
        return "Ouder dan 16 jaar"

def voorspelde_drukte():
    vandaag = date.today()

    # 6 maanden vooruit
    toekomst_maand = (vandaag.month + 6 - 1) % 12 + 1
    toekomst_jaar = vandaag.year + ((vandaag.month + 6 - 1) // 12)
    eind_tijdvak = date(toekomst_jaar, toekomst_maand, 1)

    categorieen = [
        "1 - 4 jaar (loopfietsen)",
        "2 - 3 jaar",
        "4 - 6 jaar",
        "6 - 8 jaar",
        "8 - 12 jaar",
        "14 - 16 jaar",
        "Ouder dan 16 jaar"
    ]

    # Huidige bezetting
    huidig = {c: 0 for c in categorieen}

    # Toekomstige inflow (kinderen die doorschuiven)
    inflow = {c: 0 for c in categorieen}

    actieve_verhuren = Verhuur.query.filter(
        Verhuur.einddatum >= vandaag
    ).all()

    for verhuur in actieve_verhuren:
        kind = verhuur.kind
        if not kind:
            continue

        leeftijd_nu = kind.leeftijd
        cat_now = leeftijdscategorie(leeftijd_nu)
        huidig[cat_now] += 1

        if verhuur.einddatum <= eind_tijdvak:
            leeftijd_later = leeftijd_nu + (
                verhuur.einddatum.year - vandaag.year
            )
            inflow[leeftijdscategorie(leeftijd_later)] += 1

    # Netto toekomst = inflow - huurders die in dezelfde categorie blijven
    netto = {}

    for c in categorieen:
        # Blijven dezelfde categorie behouden?
        blijven = huidig[c] - inflow[c] if inflow[c] < huidig[c] else 0
        netto[c] = max(0, inflow[c] - blijven)

    return netto
