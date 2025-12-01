from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, flash
from functools import wraps

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
from .algorithm import *

main = Blueprint("main", __name__)

# ---------------------- DECORATOR ----------------------
def rol_required(toegestane_roles):
    """Decorator om toegang te beperken op basis van rol"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            rol = session.get("rol")
            if not rol:
                flash("Je moet eerst inloggen", "error")
                return redirect("/login")
            if rol not in toegestane_roles:
                flash("Je hebt geen toegang tot deze pagina", "error")
                return redirect("/")
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ----------------------- HOME ------------------------
@main.route("/")
def index():
    return render_template("home.html")

# ---------------------- LOGIN ----------------------
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rol = request.form.get("rol")
        if rol in ["depotmedewerker", "financieel"]:
            session["rol"] = rol
            flash(f"Ingelogd als {rol}", "success")
            return redirect("/")
        else:
            flash("Ongeldige rol", "error")
            return redirect("/login")
    return render_template("login.html")

@main.route("/logout")
def logout():
    session.pop("rol", None)
    flash("Uitgelogd", "info")
    return redirect("/login")

# ---------------------- KLANTEN ----------------------
@main.route("/klanten")
@rol_required(["depotmedewerker", "financieel"])
def klanten():
    verantwoordelijken = Verantwoordelijke.query.all()
    return render_template("klanten.html", verantwoordelijken=verantwoordelijken)

@main.post("/klanten/toevoegen")
@rol_required(["depotmedewerker", "financieel"])
def klant_toevoegen():
    adres = Adres(
        straat=request.form.get("straat"),
        huisnummer=request.form.get("huisnummer"),
        postcode=request.form.get("postcode"),
        gemeente=request.form.get("gemeente"),
        land=request.form.get("land"),
    )
    db.session.add(adres)
    db.session.flush()

    klant = Verantwoordelijke(
        voornaam=request.form.get("voornaam"),
        achternaam=request.form.get("achternaam"),
        email=request.form.get("email"),
        adres_id=adres.adres_id,
    )
    db.session.add(klant)
    db.session.flush()

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
@rol_required(["depotmedewerker", "financieel"])
def klant_bewerken(id):
    klant = Verantwoordelijke.query.get_or_404(id)
    klant.voornaam = request.form.get("voornaam")
    klant.achternaam = request.form.get("achternaam")
    klant.email = request.form.get("email")

    if klant.adres:
        klant.adres.straat = request.form.get("straat")
        klant.adres.huisnummer = request.form.get("huisnummer")
        postcode_str = request.form.get("postcode")
        if postcode_str:
            try:
                klant.adres.postcode = int(postcode_str)
            except ValueError:
                pass
        klant.adres.gemeente = request.form.get("gemeente")
        klant.adres.land = request.form.get("land")

    # --- KINDEREN ---
    bestaande_kinderen = {k.kind_id: k for k in klant.kinderen}
    nieuwe_namen = request.form.getlist("kind_namen[]")
    nieuwe_datums = request.form.getlist("kind_datums[]")

    nieuwe_kinderen = []
    for naam, datum in zip(nieuwe_namen, nieuwe_datums):
        if naam.strip():
            nieuwe_kinderen.append((naam, datum))

    bestaand_set = {(k.naam, k.geboortedatum.isoformat()) for k in bestaande_kinderen.values()}
    nieuw_set = set(nieuwe_kinderen)

    te_verwijderen = bestaand_set - nieuw_set
    toe_te_voegen = nieuw_set - bestaand_set

    for naam, datum in te_verwijderen:
        kind = next(k for k in bestaande_kinderen.values()
                    if k.naam == naam and k.geboortedatum.isoformat() == datum)
        if not kind.betalingen and not getattr(kind, 'verhuren', []):
            db.session.delete(kind)

    for naam, datum in toe_te_voegen:
        nieuw_kind = Kind(
            naam=naam,
            geboortedatum=datum,
            verantwoordelijke_id=id
        )
        db.session.add(nieuw_kind)

    db.session.commit()
    return redirect("/klanten")

# ---------------------- FIETSEN ----------------------
@main.route("/fietsen")
@rol_required(["depotmedewerker", "financieel"])
def fietsen():
    fietsen = Item.query.all()
    return render_template(
        "fietsen.html",
        fietsen=fietsen,
        StatusEnum=StatusEnum,
        LeeftijdEnum=LeeftijdEnum
    )

@main.post("/fietsen/toevoegen")
@rol_required(["depotmedewerker", "financieel"])
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
        verantwoordelijke_id=None
    )

    db.session.add(nieuwe_fiets)
    db.session.commit()
    return redirect("/fietsen")

@main.post("/fietsen/bewerken/<int:itemnr>")
@rol_required(["depotmedewerker", "financieel"])
def fiets_bewerken(itemnr):
    fiets = Item.query.get_or_404(itemnr)
    gekozen_status = StatusEnum[request.form["status"]]

    if gekozen_status == StatusEnum.VERHUURD:
        gekozen_status = fiets.status

    if fiets.status != StatusEnum.VERHUURD:
        fiets.status = gekozen_status

    fiets.merk = request.form["merk"]
    fiets.model = request.form["model"]

    leeftijd_raw = request.form.get("leeftijd")
    fiets.leeftijdscategorie = (
        LeeftijdEnum[leeftijd_raw] if leeftijd_raw else None
    )

    db.session.commit()
    return redirect("/fietsen")

# ---------------------- ALGORITHME ----------------------
@main.get("/api/fietsen-advies/<int:kind_id>")
@rol_required(["depotmedewerker", "financieel"])
def api_fietsen_advies(kind_id):
    kind = Kind.query.get_or_404(kind_id)
    fietsen = fietsen_voor_leeftijd(kind)
    result = [{"itemnr": f.itemnr, "omschrijving": f"{f.merk} {f.model}", "score": score} for score, f in fietsen]
    return result

@main.get("/api/kind/<int:kind_id>/lopende_verhuur")
@rol_required(["depotmedewerker", "financieel"])
def api_lopende_verhuur(kind_id):
    aantal = Verhuur.query.filter_by(
        kind_id=kind_id,
        status=VerhuurStatusEnum.ACTIEF.value
    ).count()

    return {"aantal": aantal}


# ---------------------- VERHUUR ----------------------
@main.route("/verhuur")
@rol_required(["depotmedewerker", "financieel"])
def verhuur():
    verantwoordelijken = Verantwoordelijke.query.all()

    klant_kind_data = {
        v.verantwoordelijke_id: [
            {
                "id": k.kind_id,
                "naam": k.naam,
                "leeftijd": k.leeftijd,
                "geboortedatum": k.geboortedatum.isoformat(),
            }
            for k in v.kinderen
        ]
        for v in verantwoordelijken
    }

    # aantal actieve verhuren tellen
    actieve_verhuur = Verhuur.query.filter_by(
        status=VerhuurStatusEnum.ACTIEF.value
    ).count()

    return render_template(
        "verhuur.html",
        verhuur_lijst=Verhuur.query.order_by(Verhuur.startdatum.desc()).all(),
        totaal_actief=actieve_verhuur,
        verantwoordelijken=verantwoordelijken,
        beschikbare_fietsen=Item.query.filter(
            Item.status == StatusEnum.BESCHIKBAAR
        ).all(),
        klant_kind_data=klant_kind_data,
        VerhuurStatusEnum=VerhuurStatusEnum,
    )

@main.post("/verhuur/toevoegen")
@rol_required(["depotmedewerker", "financieel"])
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
@rol_required(["depotmedewerker", "financieel"])
def verhuur_beeindigen(verhuur_id):
    verh = Verhuur.query.get_or_404(verhuur_id)
    verh.status = VerhuurStatusEnum.BEEINDIGD.value
    fiets = Item.query.get(verh.itemnr)
    if fiets:
        fiets.status = StatusEnum.BESCHIKBAAR
        fiets.verantwoordelijke_id = None
    db.session.commit()
    return redirect("/verhuur")


@main.post("/verhuur/verleng/<int:verhuur_id>")
@rol_required(["depotmedewerker", "financieel"])
def verhuur_verleng(verhuur_id):
    # Haal de verhuur op
    verh = Verhuur.query.get_or_404(verhuur_id)

    # Alleen actieve verhuren kunnen verlengd worden
    if verh.status != VerhuurStatusEnum.ACTIEF.value:
        flash("Alleen actieve verhuur kan verlengd worden.", "error")
        return redirect("/verhuur")

    # Nieuwe einddatum ophalen uit formulier
    nieuwe_einddatum_str = request.form.get("nieuwe_einddatum")
    if not nieuwe_einddatum_str:
        flash("Geen nieuwe einddatum opgegeven.", "error")
        return redirect("/verhuur")

    try:
        nieuwe_einddatum = datetime.strptime(nieuwe_einddatum_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Ongeldige datum.", "error")
        return redirect("/verhuur")

    # Controleer dat nieuwe einddatum later is dan huidige einddatum
    if nieuwe_einddatum <= verh.einddatum:
        flash("Nieuwe einddatum moet na de huidige einddatum liggen.", "error")
        return redirect("/verhuur")

    # Verhuur verlengen
    verh.einddatum = nieuwe_einddatum
    db.session.commit()

    flash(f"Verhuur {verhuur_id} verlengd tot {nieuwe_einddatum}.", "success")
    return redirect("/verhuur")


# ---------------------- FINANCIEEL ----------------------
@main.route("/financieel")
@rol_required(["financieel"])
def financieel():
    verantwoordelijken = Verantwoordelijke.query.all()
    klant_kind_data = {v.verantwoordelijke_id: [{"id": k.kind_id, "naam": k.naam, "leeftijd": k.leeftijd, "geboortedatum": k.geboortedatum.isoformat()} for k in v.kinderen] for v in verantwoordelijken}
    return render_template(
        "financieel.html",
        betalingen=Betaling.query.order_by(Betaling.datum.desc()).all(),
        fietsen=Item.query.all(),
        verantwoordelijken=verantwoordelijken,
        klant_kind_data=klant_kind_data,
        BetalingswijzeEnum=BetalingswijzeEnum
    )

@main.post("/financieel/toevoegen")
@rol_required(["financieel"])
def betaling_toevoegen():
    betaling = Betaling(
        itemnr=request.form.get("itemnr", type=int),
        kind_id=request.form.get("kind_id", type=int),
        betalingswijze=BetalingswijzeEnum[request.form.get("betalingswijze")],
        bedrag=float(request.form.get("bedrag")),
        datum=datetime.strptime(request.form.get("datum"), "%Y-%m-%d").date(),
        tijd=datetime.now().time()
    )
    db.session.add(betaling)
    db.session.commit()
    flash("Betaling toegevoegd.", "success")
    return redirect("/financieel")

@main.post("/financieel/bewerken/<int:betaling_id>")
@rol_required(["financieel"])
def betaling_bewerken(betaling_id):
    betaling = Betaling.query.get_or_404(betaling_id)
    betaling.itemnr = request.form.get("itemnr", type=int)
    betaling.kind_id = request.form.get("kind_id", type=int)
    betaling.betalingswijze = BetalingswijzeEnum[request.form.get("betalingswijze")]
    betaling.bedrag = float(request.form.get("bedrag"))
    betaling.datum = datetime.strptime(request.form.get("datum"), "%Y-%m-%d").date()
    betaling.tijd = datetime.now().time()
    db.session.commit()
    flash(f"Betaling {betaling_id} aangepast.", "success")
    return redirect("/financieel")
