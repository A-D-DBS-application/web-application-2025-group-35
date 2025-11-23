from .models import Item
from .models import StatusEnum #dit zou het algoritme moeten zijn dit moet nog toegevoegd worden via routes aan de app zelf
from datetime import date
def leeftijd_splitsen(categorie):
    categorie = categorie.strip()#haal spaties enzo weg

    # Speciaal geval: "Ouder dan 16 jaar"
    if categorie.lower().startswith("ouder dan"):
        
        getal = int(categorie.replace("Ouder dan", "").replace("jaar", "").strip())
        return getal + 1, 90  # 90 is maximale leeftijd kan nog aangepast worden

    # Normaal geval: "X - Y jaar"
    # Verwijder "jaar"
    categorie = categorie.replace("jaar", "").strip()
    
    # Splits op '-'
    delen = categorie.split("-")
    min_leeftijd = int(delen[0].strip())
    max_leeftijd = int(delen[1].strip())

    return min_leeftijd, max_leeftijd


def fietsen_voor_leeftijd(kind):
    leeftijd=kind.leeftijd#haal de leeftijd van het kind
    
    fietsen = Item.query.filter_by(status=StatusEnum.BESCHIKBAAR).all() #alle items die beschikbaar zijn
    fiets_scores=[]

    for fiets in fietsen:
        categorie_str = fiets.leeftijdscategorie.value
        min_leeftijd, max_leeftijd = leeftijd_splitsen(categorie_str)

        if min_leeftijd <= leeftijd <= max_leeftijd:
            score=2
        elif min_leeftijd-1<=leeftijd<=max_leeftijd+1:
            score=1
        else:
            score=0
        fiets_scores.append((score,fiets))
    fiets_scores.sort(key=lambda x: x[0], reverse=True)
    return [fiets for score, fiets in fiets_scores]

