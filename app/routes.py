# routes voor data ophalen, tonen en aanpassen
from flask import Blueprint, render_template, request, redirect
from .models import db, Adres, Verantwoordelijke, Kind, Item, Betaling
from .algorithm import fietsen_voor_leeftijd
from .models import StatusEnum, LeeftijdEnum

main = Blueprint("main", __name__)


# ============================================
# HOME
# ============================================
@main.route("/")
def index():
    return render_template("home.html")


# ============================================
# KLANTEN PAGINA
# ============================================
@main.route("/klanten")
def klanten():
    verantwoordelijken = Verantwoordelijke.query.all()
    return render_template("klanten.html", verantwoordelijken=verantwoordelijken)


# ---------- KLANT TOEVOEGEN ----------
@main.post("/klanten/toevoegen")
def klant_toevoegen():
    # 1. Basis klantgegevens
    voornaam = request.form.get("voornaam")
    achternaam = request.form.get("achternaam")
    email = request.form.get("email")

    # 2. Adres opslaan
    adres = Adres(
        straat=request.form.get("straat"),
        huisnummer=request.form.get("huisnummer"),
        postcode=request.form.get("postcode"),
        gemeente=request.form.get("gemeente"),
        land=request.form.get("land")
    )
    db.session.add(adres)
    db.session.flush()  # zodat adres_id meteen beschikbaar is

    # 3. Klant zelf opslaan
    klant = Verantwoordelijke(
        voornaam=voornaam,
        achternaam=achternaam,
        email=email,
        adres_id=adres.adres_id
    )
    db.session.add(klant)
    db.session.flush()

    # 4. Kinderen opslaan
    kind_namen = request.form.getlist("kind_namen[]")
    kind_geboortedata = request.form.getlist("kind_datums[]")

    for naam, datum in zip(kind_namen, kind_geboortedata):
        if naam.strip() != "":
            nieuw_kind = Kind(
                naam=naam,
                geboortedatum=datum,
                verantwoordelijke_id=klant.verantwoordelijke_id
            )
            db.session.add(nieuw_kind)

    db.session.commit()

    return redirect("/klanten")


# ---------- KLANT BEWERKEN ----------
@main.post("/klanten/bewerken/<int:id>")
def klant_bewerken(id):
    klant = Verantwoordelijke.query.get_or_404(id)

    # Klant gegevens
    klant.voornaam = request.form.get("voornaam")
    klant.achternaam = request.form.get("achternaam")
    klant.email = request.form.get("email")

    # KINDEREN
    # 1) Oude kinderen verwijderen
    Kind.query.filter_by(verantwoordelijke_id=id).delete()

    # 2) Nieuwe toevoegen
    kind_namen = request.form.getlist("kind_namen[]")
    kind_datums = request.form.getlist("kind_datums[]")

    for naam, datum in zip(kind_namen, kind_datums):
        if naam.strip() != "":
            nieuw_kind = Kind(
                naam=naam,
                geboortedatum=datum,
                verantwoordelijke_id=id
            )
            db.session.add(nieuw_kind)

    db.session.commit()
    return redirect("/klanten")

# === Fiets overzicht ===
@main.route("/fietsen")
def fietsen():
    fietsen = Item.query.all()
    verantwoordelijken = Verantwoordelijke.query.all()
    return render_template(
        "fietsen.html",
        fietsen=fietsen,
        verantwoordelijken=verantwoordelijken,
        StatusEnum=StatusEnum,
        LeeftijdEnum=LeeftijdEnum
    )

# === Nieuwe fiets toevoegen ===
@main.post("/fietsen/toevoegen")
def fiets_toevoegen():
    itemnr = request.form["itemnr"]
    status = StatusEnum[request.form["status"]]
    leeftijd_raw = request.form.get("leeftijd")
    verantwoordelijke_id = request.form.get("verantwoordelijke_id") or None

    leeftijd = LeeftijdEnum[leeftijd_raw] if leeftijd_raw else None

    nieuwe_fiets = Item(
        itemnr=itemnr,
        status=status,
        leeftijdscategorie=leeftijd,
        verantwoordelijke_id=verantwoordelijke_id
    )

    db.session.add(nieuwe_fiets)
    db.session.commit()

    return redirect("/fietsen")

# === Fiets bewerken ===
@main.post("/fietsen/bewerken/<int:itemnr>")
def fiets_bewerken(itemnr):
    fiets = Item.query.get_or_404(itemnr)

    status = request.form["status"]
    leeftijd_raw = request.form.get("leeftijd")
    verantwoordelijke_id = request.form.get("verantwoordelijke_id") or None

    fiets.status = StatusEnum[status]
    fiets.leeftijdscategorie = LeeftijdEnum[leeftijd_raw] if leeftijd_raw else None
    fiets.verantwoordelijke_id = verantwoordelijke_id

    db.session.commit()

    return redirect("/fietsen")


# ============================================
# VERHUUR
# ============================================
@main.route("/verhuur")
def verhuur():
    betalingen = Betaling.query.all()
    return render_template("verhuur.html", betalingen=betalingen)


# ============================================
# FINANCIEEL
# ============================================
@main.route("/financieel")
def financieel():
    betalingen = Betaling.query.all()
    return render_template("financieel.html", betalingen=betalingen)

