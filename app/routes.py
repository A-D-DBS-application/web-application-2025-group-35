from flask import Blueprint, render_template, request
from .models import db, Adres, Verantwoordelijke, Kind, Item, Betaling, Magazijn, Medewerker
from .algorithm import fietsen_voor_leeftijd

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('home.html')

@main.route('/klanten')
def klanten():
    verantwoordelijken = Verantwoordelijke.query.all()
    return render_template('klanten.html', verantwoordelijken=verantwoordelijken)

@main.route('/fietsen')
def fietsen():
    leeftijd = request.args.get('leeftijd', type=int)

    if leeftijd is not None:
        items = fietsen_voor_leeftijd(leeftijd)
    else:
        items = Item.query.all()

    return render_template('fietsen.html', items=items, leeftijd=leeftijd)

@main.route('/verhuur')
def verhuur():
    betalingen = Betaling.query.all()
    return render_template('verhuur.html', betalingen=betalingen)

@main.route('/financieel')
def financieel():
    betalingen = Betaling.query.all()
    return render_template('financieel.html', betalingen=betalingen)

