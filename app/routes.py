from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, flash
from functools import wraps
from sqlalchemy import nulls_last

from .models import (
    db, Adres, Verantwoordelijke, Kind, Item,
    Betaling, Verhuur, StatusEnum, LeeftijdEnum,
    VerhuurStatusEnum, BetalingswijzeEnum
)
from .algorithm import fietsen_voor_leeftijd
from .services import (
    update_kinderen, set_fiets_verhuurd,
    set_fiets_beschikbaar, verleng_verhuur, paginatie,
    filter_fietsen_query, filter_klanten_query,
    prepare_klant_kind_data,
    get_enum_or_none, parse_date_form, validate_and_parse_extension_date
)

main = Blueprint("main", __name__)

# ---------------------- DECORATOR ----------------------
def rol_required(rollen):
    def decorator(f):
        @wraps(f)
        def wrapper(*a, **k):
            rol = session.get("rol")
            if not rol:
                flash("Je moet eerst inloggen", "error")
                return redirect("/login")
            if rol not in rollen:
                flash("Geen toegang", "error")
                return redirect("/")
            return f(*a, **k)
        return wrapper
    return decorator


# ---------------------- HOME & LOGIN ----------------------
@main.route("/")
def index():
    return render_template("home.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        rol = request.form.get("rol")
        if rol in ["depotmedewerker", "financieel"]:
            session["rol"] = rol
            flash(f"Ingelogd als {rol}", "success")
            return redirect("/")
        flash("Ongeldige rol", "error")
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
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    query = Verantwoordelijke.query.order_by(Verantwoordelijke.achternaam.asc())
    query = filter_klanten_query(query, search_query)
    verantwoordelijken, total, pages = paginatie(query, page)

    for v in verantwoordelijken:
        for k in v.kinderen:
            k.heeft_betalingen = bool(k.betalingen)

    return render_template(
        "klanten.html",
        verantwoordelijken=verantwoordelijken,
        page=page,
        pages=pages,
    )

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
        request.form.getlist("kind_datums[]"),
    ):
        if naam.strip():
            db.session.add(
                Kind(
                    naam=naam,
                    geboortedatum=datum,
                    verantwoordelijke_id=klant.verantwoordelijke_id,
                )
            )

    db.session.commit()
    return redirect("/klanten")


@main.post("/klanten/bewerken/<int:id>")
@rol_required(["depotmedewerker", "financieel"])
def klant_bewerken(id):
    klant = Verantwoordelijke.query.get_or_404(id)

    klant.voornaam = request.form.get("voornaam")
    klant.achternaam = request.form.get("achternaam")
    klant.email = request.form.get("email")

    klant.adres.straat = request.form.get("straat")
    klant.adres.huisnummer = request.form.get("huisnummer")
    klant.adres.gemeente = request.form.get("gemeente")
    klant.adres.land = request.form.get("land")

    try:
        klant.adres.postcode = int(request.form.get("postcode"))
    except ValueError:
        pass

    update_kinderen(
        klant,
        request.form.getlist("kind_ids[]"),
        request.form.getlist("kind_namen[]"),
        request.form.getlist("kind_datums[]"),
    )

    db.session.commit()
    return redirect("/klanten")


# ---------------------- FIETSEN ----------------------
@main.route("/fietsen")
@rol_required(["depotmedewerker", "financieel"])
def fietsen():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    leeftijd_filter = request.args.get("leeftijdscategorie")
    status_filter = request.args.get("status_filter")

    query = Item.query.order_by(nulls_last(Item.leeftijdscategorie))

    if search_query:
        query = filter_fietsen_query(query, search_query)

    leeftijd_enum = get_enum_or_none(LeeftijdEnum, leeftijd_filter)
    if leeftijd_enum:
        query = query.filter(Item.leeftijdscategorie == leeftijd_enum)
    elif leeftijd_filter:
        flash("Ongeldige leeftijdscategorie geselecteerd.", "error")

    status_enum = get_enum_or_none(StatusEnum, status_filter)
    if status_enum:
        query = query.filter(Item.status == status_enum)
    elif status_filter:
        flash("Ongeldige status geselecteerd.", "error")

    fietsen, total, pages = paginatie(query, page)
    beschikbaar = Item.query.filter_by(status=StatusEnum.BESCHIKBAAR).count()

    return render_template(
        "fietsen.html",
        fietsen=fietsen,
        beschikbare_fietsen=beschikbaar,
        StatusEnum=StatusEnum,
        LeeftijdEnum=LeeftijdEnum,
        page=page,
        pages=pages,
    )


# GET-formulier toevoegen
@main.get("/fietsen/toevoegen")
@rol_required(["depotmedewerker", "financieel"])
def fiets_toevoegen_form():
    return render_template(
        "fiets_toevoegen.html",
        StatusEnum=StatusEnum,
        LeeftijdEnum=LeeftijdEnum,
    )


@main.post("/fietsen/toevoegen")
@rol_required(["depotmedewerker", "financieel"])
def fiets_toevoegen():
    fiets = Item(
        itemnr=request.form.get("itemnr", type=int),
        merk=request.form.get("merk"),
        model=request.form.get("model"),
        status=StatusEnum[request.form.get("status")],
        leeftijdscategorie=get_enum_or_none(
            LeeftijdEnum,
            request.form.get("leeftijdscategorie"),
        ),
    )
    db.session.add(fiets)
    db.session.commit()
    return redirect("/fietsen")


@main.post("/fietsen/bewerken/<int:itemnr>")
@rol_required(["depotmedewerker", "financieel"])
def fiets_bewerken(itemnr):
    fiets = Item.query.get_or_404(itemnr)
    nieuwe_status = StatusEnum[request.form.get("status")]

    if fiets.status != StatusEnum.VERHUURD:
        fiets.status = nieuwe_status

    fiets.merk = request.form.get("merk")
    fiets.model = request.form.get("model")
    fiets.leeftijdscategorie = get_enum_or_none(
        LeeftijdEnum, request.form.get("leeftijdscategorie")
    )

    db.session.commit()
    return redirect("/fietsen")


@main.post("/fietsen/archiveren/<int:itemnr>")
@rol_required(["depotmedewerker", "financieel"])
def fiets_archiveren(itemnr):
    fiets = Item.query.get_or_404(itemnr)
    fiets.status = StatusEnum.GEARCHIVEERD
    db.session.commit()
    return redirect("/fietsen")


# ---------------------- API ALGORITHM ----------------------
@main.get("/api/fietsen-advies/<int:kind_id>")
@rol_required(["depotmedewerker", "financieel"])
def api_fietsen_advies(kind_id):
    kind = Kind.query.get_or_404(kind_id)
    fietsen = fietsen_voor_leeftijd(kind)
    return [
        {
            "itemnr": f.itemnr,
            "omschrijving": f"{f.merk} {f.model}",
            "score": score,
        }
        for score, f in fietsen
    ]


@main.get("/api/kind/<int:kind_id>/lopende_verhuur")
@rol_required(["depotmedewerker", "financieel"])
def api_lopende_verhuur(kind_id):
    aantal = Verhuur.query.filter_by(
        kind_id=kind_id,
        status=VerhuurStatusEnum.ACTIEF.value,
    ).count()
    return {"aantal": aantal}


# ---------------------- VERHUUR ----------------------
@main.route("/verhuur")
@rol_required(["depotmedewerker", "financieel"])
def verhuur():
    page = request.args.get("page", 1, type=int)

    verantwoordelijken = Verantwoordelijke.query.order_by(
        Verantwoordelijke.achternaam.asc()
    ).all() 

    klant_kind_data = prepare_klant_kind_data(verantwoordelijken)

    query = Verhuur.query.order_by(Verhuur.startdatum.desc())
    verhuur_lijst, total, pages = paginatie(query, page)

    actief = Verhuur.query.filter_by(
        status=VerhuurStatusEnum.ACTIEF.value
    ).count()

    return render_template(
        "verhuur.html",
        verhuur_lijst=verhuur_lijst,
        totaal_actief=actief,
        verantwoordelijken=verantwoordelijken,
        beschikbare_fietsen=Item.query.filter_by(
            status=StatusEnum.BESCHIKBAAR
        ).all(),
        klant_kind_data=klant_kind_data,
        VerhuurStatusEnum=VerhuurStatusEnum,
        page=page,
        pages=pages,
    )


@main.post("/verhuur/toevoegen")
@rol_required(["depotmedewerker", "financieel"])
def verhuur_toevoegen():
    verh = Verhuur(
        itemnr=request.form.get("itemnr", type=int),
        kind_id=request.form.get("kind_id", type=int),
        verantwoordelijke_id=request.form.get(
            "verantwoordelijke_id", type=int
        ),
        startdatum=parse_date_form(request.form.get("startdatum")),
        einddatum=parse_date_form(request.form.get("einddatum")),
        status=VerhuurStatusEnum.ACTIEF.value,
    )
    db.session.add(verh)

    fiets = Item.query.get(verh.itemnr)
    if fiets:
        set_fiets_verhuurd(fiets, verh.verantwoordelijke_id)

    db.session.commit()
    return redirect("/verhuur")


@main.post("/verhuur/beëindigen/<int:verhuur_id>")
@rol_required(["depotmedewerker", "financieel"])
def verhuur_beeindigen(verhuur_id):
    verh = Verhuur.query.get_or_404(verhuur_id)
    verh.status = VerhuurStatusEnum.BEEINDIGD.value

    fiets = Item.query.get(verh.itemnr)
    if fiets:
        set_fiets_beschikbaar(fiets)

    db.session.commit()
    return redirect("/verhuur")


@main.post("/verhuur/verleng/<int:verhuur_id>")
@rol_required(["depotmedewerker", "financieel"])
def verhuur_verleng(verhuur_id):
    verh = Verhuur.query.get_or_404(verhuur_id)

    if verh.status != VerhuurStatusEnum.ACTIEF.value:
        flash("Alleen actieve verhuur kan verlengd worden.", "error")
        return redirect("/verhuur")

    redirect_response, nieuwe_datum = validate_and_parse_extension_date(
        request.form.get("nieuwe_einddatum"),
        verh.einddatum,
    )
    if redirect_response:
        return redirect_response

    verleng_verhuur(verh, nieuwe_datum)
    db.session.commit()
    flash("Verhuur verlengd.", "success")
    return redirect("/verhuur")


# ---------------------- FINANCIEEL ----------------------
@main.route("/financieel")
@rol_required(["financieel"])
def financieel():
    page = request.args.get("page", 1, type=int)

    query = Betaling.query.order_by(Betaling.datum.desc())
    betalingen, total, pages = paginatie(query, page)

    verantwoordelijken = Verantwoordelijke.query.order_by(
        Verantwoordelijke.achternaam.asc()
    ).all()

    klant_kind_data = prepare_klant_kind_data(verantwoordelijken)

    niet_voltooid = Betaling.query.filter_by(
        betalingswijze=BetalingswijzeEnum.OVERSCHRIJVEN_NIET_VOLDAAN
    ).count()

    return render_template(
        "financieel.html",
        betalingen=betalingen,
        fietsen=Item.query.all(),
        verantwoordelijken=verantwoordelijken,
        klant_kind_data=klant_kind_data,
        BetalingswijzeEnum=BetalingswijzeEnum,
        niet_voltooid=niet_voltooid,
        page=page,
        pages=pages,
    )


@main.post("/financieel/toevoegen")
@rol_required(["financieel"])
def betaling_toevoegen():
    betaling = Betaling(
        itemnr=request.form.get("itemnr", type=int),
        kind_id=request.form.get("kind_id", type=int),
        betalingswijze=BetalingswijzeEnum[
            request.form.get("betalingswijze")
        ],
        bedrag=float(request.form.get("bedrag")),
        datum=parse_date_form(request.form.get("datum")),
        tijd=datetime.now().time(),
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
    betaling.betalingswijze = BetalingswijzeEnum[
        request.form.get("betalingswijze")
    ]
    betaling.bedrag = float(request.form.get("bedrag"))
    betaling.datum = datetime.strptime(
        request.form.get("datum"), "%Y-%m-%d"
    ).date()
    betaling.tijd = datetime.now().time()

    db.session.commit()
    flash(f"Betaling {betaling_id} aangepast.", "success")
    return redirect("/financieel")


# ---------------------- VOORSPELLING ----------------------
@main.route("/voorspelling")
@rol_required(["depotmedewerker", "financieel"])
def voorspelling():
    from .algorithm_voorspelling import voorspelde_drukte
    try:
        voorspelling_data = voorspelde_drukte()
    except:
        voorspelling_data = {}
    return render_template(
        "voorspelling.html",
        voorspelling=voorspelling_data,
    )
