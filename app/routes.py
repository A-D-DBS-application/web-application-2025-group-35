# routes om data uit je modellen te halen en naar templates te sturen
from flask import Blueprint, render_template, request
from .models import db, Adres, Verantwoordelijke, Kind, Item, Betaling, Magazijn, Medewerker
from .algoritme import fietsen_voor_leeftijd  # ons algoritme importeren

main = Blueprint('main', __name__)  # blueprint main gebruiken zodat alles net georganiseerd is

# startpagina
@main.route('/')
def index():
    return render_template('index.html')  # Hier renderen we gewoon index.html zoals het is

# Pagina Klanten
@main.route('/klanten')
def klanten():
    verantwoordelijken = Verantwoordelijke.query.all()  # haalt alle verantwoordelijken uit de database
    return render_template('klanten.html', verantwoordelijken=verantwoordelijken)

# Pagina Fietsen
@main.route('/fietsen')
def fietsen():
    leeftijd = request.args.get('leeftijd', type=int)  # haal ?leeftijd=12 op uit URL

    if leeftijd is not None:
        items = fietsen_voor_leeftijd(leeftijd)  # filter fietsen via algoritme
    else:
        items = Item.query.all()  # toon alles als geen leeftijd is opgegeven

    return render_template('fietsen.html', items=items, leeftijd=leeftijd)

# Pagina Verhuur
@main.route('/verhuur')
def verhuur():
    betalingen = Betaling.query.all()
    return render_template('verhuur.html', betalingen=betalingen)

# Pagina Financieel
@main.route('/financieel')
def financieel():
    betalingen = Betaling.query.all()
    return render_template('financieel.html', betalingen=betalingen)
