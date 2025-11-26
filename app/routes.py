from datetime import datetime
from flask import Blueprint, render_template, request, redirect

from .models import (
    db,
    Adres,
    Verantwoordelijke,
    Kind,
    Item,
    Betaling,
    Verhuur,
    StatusEnum,
    LeeftijdEnum,
    VerhuurStatusEnum,
    BetalingswijzeEnum  
)
from.algorithm import *


main = Blueprint("main", __name__)



# ----------------------- HOME ------------------------
@main.route("/")
def index():
    return render_template("home.html")



# ---------------------- KLANTEN ----------------------
@main.route("/klanten")
def klanten():
    verantwoordelijken = Verantwoordelijke.query.all()
    return render_template("klanten.html", verantwoordelijken=verantwoordelijken)



@main.post("/klanten/toevoegen")
def klant_toevoegen():

    # --- Adres ---
    adres = Adres(
        straat=request.form.get("straat"),
        huisnummer=request.form.get("huisnummer"),
        postcode=request.form.get("postcode"),
        gemeente=request.form.get("gemeente"),
        land=request.form.get("land"),
    )
    db.session.add(adres)
    db.session.flush()

    # --- Verantwoordelijke ---
    klant = Verantwoordelijke(
        voornaam=request.form.get("voornaam"),
        achternaam=request.form.get("achternaam"),
        email=request.form.get("email"),
        adres_id=adres.adres_id,
    )
    db.session.add(klant)
    db.session.flush()

    # --- Kinderen ---
    for naam, datum in zip(
        request.form.getlist("kind_namen[]"),
        request.form.getlist("kind_datums[]")
    ):
        if naam.strip():
            db.session.add(Kind(
                naam=naam,
                geboortedatum=datum,
                verantwoordelijke_id=klant.verantwoordelijke_id
            ))

    db.session.commit()
    return redirect("/klanten")



@main.post("/klanten/bewerken/<int:id>")
def klant_bewerken(id):
    klant = Verantwoordelijke.query.get_or_404(id)

    # Basisgegevens
    klant.voornaam = request.form.get("voornaam")
    klant.achternaam = request.form.get("achternaam")
    klant.email = request.form.get("email")

    # Adres updaten
    if klant.adres:
        klant.adres.straat = request.form.get("straat")
        klant.adres.huisnummer = request.form.get("huisnummer")

        postcode_str = request.form.get("postcode")
        if postcode_str:
            try:
                klant.adres.postcode = int(postcode_str)
            except ValueError:
                pass  # (optioneel: foutafhandeling toevoegen)

        klant.adres.gemeente = request.form.get("gemeente")
        klant.adres.land = request.form.get("land")

    # Oude kinderen verwijderen
    Kind.query.filter_by(verantwoordelijke_id=id).delete()

    # Nieuwe kinderen opslaan
    for naam, datum in zip(
        request.form.getlist("kind_namen[]"),
        request.form.getlist("kind_datums[]")
    ):
        if naam.strip():
            db.session.add(Kind(
                naam=naam,
                geboortedatum=datum,
                verantwoordelijke_id=id
            ))

    db.session.commit()
    return redirect("/klanten")




# ===========================================================
# FIETSEN
# ===========================================================

@main.route("/fietsen")
def fietsen():
    fietsen = Item.query.all()
    return render_template(
        "fietsen.html",
        fietsen=fietsen,
        StatusEnum=StatusEnum,
        LeeftijdEnum=LeeftijdEnum
    )


@main.post("/fietsen/toevoegen")
def fiets_toevoegen():

    merk = request.form.get("merk")
    model = request.form.get("model")

    status = StatusEnum[request.form["status"]]

    leeftijd_raw = request.form.get("leeftijd")
    leeftijd = LeeftijdEnum[leeftijd_raw] if leeftijd_raw else None

    nieuwe_fiets = Item(
        merk=merk,
        model=model,
        status=status,
        leeftijdscategorie=leeftijd,
        verantwoordelijke_id=None    # altijd leeg
    )

    db.session.add(nieuwe_fiets)
    db.session.commit()

    return redirect("/fietsen")


@main.post("/fietsen/bewerken/<int:itemnr>")
def fiets_bewerken(itemnr):
    fiets = Item.query.get_or_404(itemnr)

    fiets.merk = request.form["merk"]
    fiets.model = request.form["model"]
    fiets.status = StatusEnum[request.form["status"]]

    leeftijd_raw = request.form.get("leeftijd")
    fiets.leeftijdscategorie = LeeftijdEnum[leeftijd_raw] if leeftijd_raw else None

    db.session.commit()
    return redirect("/fietsen")

#algoritme toevoegen
@main.get("/api/fietsen-advies/<int:kind_id>")
def api_fietsen_advies(kind_id):
    kind = Kind.query.get_or_404(kind_id)

    # ⬇️ jouw eigen algoritme wordt hier gebruikt!
    fietsen = fietsen_voor_leeftijd(kind)

    # ⬇️ fietsen_voor_leeftijd() geeft tuples → (score, fiets)
    result = []
    for score, f in fietsen:
        result.append({
            "itemnr": f.itemnr,
            "omschrijving": f"{f.itemnr} – {f.merk} {f.model}",
            "score": score
        })

    return result
#hier eindigt het


@main.route("/verhuur")
def verhuur():

    verantwoordelijken = Verantwoordelijke.query.all()

    klant_kind_data = {
        v.verantwoordelijke_id: [
            {
                "id": k.kind_id,
                "naam": k.naam,
                "leeftijd": k.leeftijd,
                "geboortedatum": k.geboortedatum.isoformat()
            }
            for k in v.kinderen
        ]
        for v in verantwoordelijken
    }

    return render_template(
        "verhuur.html",
        verhuur_lijst=Verhuur.query.order_by(Verhuur.startdatum.desc()).all(),
        verantwoordelijken=verantwoordelijken,
        beschikbare_fietsen=Item.query.filter(Item.status == StatusEnum.BESCHIKBAAR).all(),
        klant_kind_data=klant_kind_data,
        VerhuurStatusEnum=VerhuurStatusEnum   # ✅ extra
    )




@main.post("/verhuur/toevoegen")
def verhuur_toevoegen():

    start = datetime.strptime(request.form.get("startdatum"), "%Y-%m-%d").date()
    einde = datetime.strptime(request.form.get("einddatum"), "%Y-%m-%d").date()

    verh = Verhuur(
        itemnr=request.form.get("itemnr", type=int),
        kind_id=request.form.get("kind_id", type=int),
        verantwoordelijke_id=request.form.get("verantwoordelijke_id", type=int),
        startdatum=start,
        einddatum=einde,
        status=VerhuurStatusEnum.ACTIEF.value
    )

    db.session.add(verh)

    fiets = Item.query.get(verh.itemnr)
    if fiets:
        fiets.status = StatusEnum.VERHUURD
        fiets.verantwoordelijke_id = verh.verantwoordelijke_id

    db.session.commit()
    return redirect("/verhuur")



@main.post("/verhuur/beëindigen/<int:verhuur_id>")
def verhuur_beeindigen(verhuur_id):

    verh = Verhuur.query.get_or_404(verhuur_id)
    verh.status = VerhuurStatusEnum.BEEINDIGD.value

    fiets = Item.query.get(verh.itemnr)
    if fiets:
        fiets.status = StatusEnum.BESCHIKBAAR
        fiets.verantwoordelijke_id = None

    db.session.commit()
    return redirect("/verhuur")



# ---------------------- FINANCIEEL ----------------------
@main.route("/financieel")
def financieel():
    from .models import Betaling, BetalingswijzeEnum, Item

    verantwoordelijken = Verantwoordelijke.query.all()

    klant_kind_data = {
        v.verantwoordelijke_id: [
            {
                "id": k.kind_id,
                "naam": k.naam,
                "leeftijd": k.leeftijd,
                "geboortedatum": k.geboortedatum.isoformat()
            }
            for k in v.kinderen
        ]
        for v in verantwoordelijken
    }

    return render_template(
        "financieel.html",
        betalingen=Betaling.query.all(),
        fietsen=Item.query.all(),
        verantwoordelijken=verantwoordelijken,
        klant_kind_data=klant_kind_data,
        BetalingswijzeEnum=BetalingswijzeEnum
    )


@main.post("/financieel/toevoegen")
def betaling_toevoegen():
    betaling = Betaling(
        itemnr=request.form.get("itemnr"),
        kind_id=request.form.get("kind_id"),
        betalingswijze=BetalingswijzeEnum[request.form.get("betalingswijze")],
        bedrag=float(request.form.get("bedrag")),
        datum=datetime.strptime(request.form.get("datum"), "%Y-%m-%d").date(),
        tijd=datetime.now().time()
    )

    db.session.add(betaling)
    db.session.commit()

    return redirect("/financieel")







