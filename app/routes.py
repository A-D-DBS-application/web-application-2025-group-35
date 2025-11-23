#routes om data uit je modellen te halen en naar templates te sturen
from flask import Blueprint, render_template
from .models import db, Adres, Verantwoordelijke, Kind, Item, Betaling, Magazijn, Medewerker

main = Blueprint('main', __name__)  #blueprint main gebruiken zodat alles net georganiseerd is

#startpagina
@main.route('/')
def index():
    return render_template('index.html')   ## Hier renderen we gewoon index.html zoals het is

# Pagina Klanten
@main.route('/klanten')  #route die '/klanten' URL afhandelt.
def klanten():
    verantwoordelijken = Verantwoordelijke.query.all()   #haalt alle verantwoordelijken uit de database
    return render_template('klanten.html', verantwoordelijken=verantwoordelijken) #stuurt de data naar de template

# Pagina Fietsen
@main.route('/fietsen')
def fietsen():
    items = Item.query.all()
    return render_template('fietsen.html', items=items)

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

