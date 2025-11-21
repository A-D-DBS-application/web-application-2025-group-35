from models import Item

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


def fietsen_voor_leeftijd(leeftijd):
    geschikte = []
    fietsen = Item.query.all()#alle items

    for fiets in fietsen:
        min_leeftijd, max_leeftijd = leeftijd_splitsen(fiets.Leeftijdscategorie)

        if min_leeftijd <= leeftijd <= max_leeftijd:
            geschikte.append(fiets)

    return geschikte

