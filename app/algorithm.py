from .models import Item, StatusEnum
from datetime import date


# ------------------------------
#  LEFETIJDSCATEGORIE PARSER
# ------------------------------
def leeftijd_splitsen(categorie):
    """
    Zet leeftijdscategorieën om naar (min, max).
    Werkt met alle formaten zoals:
    - '1-4 jaar'
    - '1 - 4'
    - 'Ouder dan 16 jaar'
    - 'ouder dan 16'
    """

    if not categorie:
        return None, None

    categorie = categorie.lower().replace("jaar", "").strip()

    # ---- Speciaal geval ----
    if categorie.startswith("ouder dan"):
        getal = int(categorie.replace("ouder dan", "").strip())
        return getal + 1, 99  # max leeftijd = 99

    # ---- Normale gevallen ----
    # verwijder spaties → "1-4"
    categorie = categorie.replace(" ", "")

    delen = categorie.split("-")
    if len(delen) != 2:
        return None, None  # ongeldige categorie

    try:
        min_leeftijd = int(delen[0])
        max_leeftijd = int(delen[1])
    except ValueError:
        return None, None

    return min_leeftijd, max_leeftijd



# ------------------------------
#  MATCHING ALGORITME
# ------------------------------
def fietsen_voor_leeftijd(kind):
    leeftijd = kind.leeftijd  # leeftijd property werkt

    fietsen = Item.query.filter_by(status=StatusEnum.BESCHIKBAAR).all()
    fiets_scores = []

    for fiets in fietsen:

        # fiets heeft geen categorie → onmogelijk te matchen
        if not fiets.leeftijdscategorie:
            continue

        categorie_str = fiets.leeftijdscategorie.value

        min_leeftijd, max_leeftijd = leeftijd_splitsen(categorie_str)

        # categorie kon niet gesplit worden → skip
        if min_leeftijd is None:
            continue

        # ---- score bepalen ----
        if min_leeftijd <= leeftijd <= max_leeftijd:
            score = 2       # perfect
        elif min_leeftijd - 1 <= leeftijd <= max_leeftijd + 1:
            score = 1       # bijna goed
        else:
            score = 0       # geen match

        fiets_scores.append((score, fiets))

    # beste voorstellen eerst
    fiets_scores.sort(key=lambda x: x[0], reverse=True)
    return fiets_scores
