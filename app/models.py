from flask_sqlalchemy import SQLAlchemy
from datetime import datetime     #Dit importeert de datetime klasse uit Python’s standaardbibliotheek (datetime module).
                                  #Die wordt gebruikt om tijdstempels te maken (dit is dus voor die created_at kolom die supabase automatisch erbij zet hierin te krijgen).

db = SQLAlchemy()   

class Adres(db.Model):
    __tablename__ = 'adres'      #zie chatgpt wrm dit nodig is
    adres_id = db.Column(db.Integer, primary_key=True)
    straat = db.Column(db.Text, nullable=False)
    huisnummer = db.Column(db.String(20), nullable=False)   #in python gebruik je string(20) ipv. varchar maar komt op hetzelfde neer
    postcode = db.Column(db.Integer, nullable=False)
    gemeente = db.Column(db.Text, nullable=False)
    land = db.Column(db.Text, nullable=False)

    verantwoordelijken = db.relationship('Verantwoordelijke', backref='adres', lazy=True)   #verantwoordelijken =       dit betekent: “Ik wil op elk Adres-object een lijst hebben met de verantwoordelijken die daarbij horen.”
                                                                                            #Dus als je later in Python zegt: adres.verantwoordelijken
                                                                                            #dan krijg je alle verantwoordelijken (personen) die dit adres gebruiken.
                                                                                            #Je kunt de naam zelf kiezen — je zou dit ook personen_op_adres kunnen noemen. Maar verantwoordelijken klinkt logisch, want dat is de naam van de andere tabel.
    #db.relationship is de functie van SQLalchemy die een "relatie" legt tussen twee moddelen. Ze vertelt: “Deze klasse (Adres) is verbonden met een andere klasse (Verantwoordelijke).”
    #Belangrijk:db.relationship() maakt geen kolom in de database, het is puur een hulpmiddel in Python om objecten makkelijker te koppelen.
    #backref='adres'  Dit betekent letterlijk: “Maak automatisch ook de link terug beschikbaar, en noem die adres.”
    #illustratie: van een adres kun je nu naar al zijn verantwoordelijken: adres.verantwoordelijken
                  #Van een verantwoordelijke kun je terug naar zijn adres:verantwoordelijke.adres
    #Zonder backref zou je die tweede (“terugweg”) zelf moeten aanmaken in het andere model.
    #lazy=True Laadt gegevens pas als ze nodig zijn      “Haalt de verantwoordelijken pas op als je ze opvraagt.”
    def __repr__(self):
        return f"<Adres {self.straat} {self.huisnummer}, {self.gemeente}>"


class Verantwoordelijke(db.Model):
    __tablename__ = 'verantwoordelijke'
    verantwoordelijke_id = db.Column(db.Integer, primary_key=True)
    voornaam = db.Column(db.Text, nullable=False)
    achternaam = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    adres_id = db.Column(db.Integer, db.ForeignKey('adres.adres_id'), nullable=False)  #FK die verwijst naar de class adres and the adres_id van die klasse

    kinderen = db.relationship('Kind', backref='verantwoordelijke', lazy=True)
    items = db.relationship('Item', backref='verantwoordelijke', lazy=True)

    def __repr__(self):
        return f"<Verantwoordelijke {self.voornaam} {self.achternaam}>"


class Kind(db.Model):
    __tablename__ = 'kind'
    kind_id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.Text, nullable=False)
    geboortedatum = db.Column(db.Date, nullable=False)
    verantwoordelijke_id = db.Column(db.Integer, db.ForeignKey('verantwoordelijke.verantwoordelijke_id'), nullable=False)

    betalingen = db.relationship('Betaling', backref='kind', lazy=True)

    def __repr__(self):
        return f"<Kind {self.naam} ({self.geboortedatum})>"


class Magazijn(db.Model):
    __tablename__ = 'magazijn'
    magazijn_id = db.Column(db.Integer, primary_key=True)
    adres_id = db.Column(db.Integer, db.ForeignKey('adres.adres_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)      #Wanneer een nieuw record wordt aangemaakt, wordt automatisch het huidige tijdstip (UTC) ingevuld.
                                                                        #Bijvoorbeeld bij een nieuwe Medewerker of Magazijn.   #bespreek dit doorstreepte eens in groep, chatgpt legt uit hoe we het kunnen aanpassen

    medewerkers = db.relationship('Medewerker', backref='magazijn', lazy=True)

    def __repr__(self):
        return f"<Magazijn {self.magazijn_id}>"


class Medewerker(db.Model):
    __tablename__ = 'medewerker'
    medewerker_id = db.Column(db.Integer, primary_key=True)
    voornaam = db.Column(db.String(100), nullable=False)
    achternaam = db.Column(db.String(100), nullable=False)
    werknemersnummer = db.Column(db.String(50), nullable=False)
    magazijn_id = db.Column(db.Integer, db.ForeignKey('magazijn.magazijn_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Medewerker {self.voornaam} {self.achternaam}>"


class Item(db.Model):
    __tablename__ = 'item'
    itemnr = db.Column(db.Integer, primary_key=True)   #vraag: moet dit geen item_id ofs zijn, staat in database gewoon als "item"
    status = db.Column(db.String(50), nullable=False)  #vraag: we willen hier dat ze kunnen kiezen uit beschikbaar,... maar ik weet niet hoe je dit implementeert in de code dus moeten we nog even uitzoeken
    verantwoordelijke_id = db.Column(db.Integer, db.ForeignKey('verantwoordelijke.verantwoordelijke_id'))

    betalingen = db.relationship('Betaling', backref='item', lazy=True)

    def __repr__(self):
        return f"<Item {self.itemnr} - {self.status}>"


class Betaling(db.Model):
    __tablename__ = 'betaling'
    id = db.Column(db.Integer, primary_key=True)
    itemnr = db.Column(db.Integer, db.ForeignKey('item.itemnr'), nullable=False)
    kind_id = db.Column(db.Integer, db.ForeignKey('kind.kind_id'), nullable=False)
    betalingswijze = db.Column(db.Text, nullable=False)
    bedrag = db.Column(db.Float, nullable=False)
    datum = db.Column(db.Date, nullable=False)
    tijd = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f"<Betaling €{self.bedrag} via {self.betalingwijze} op {self.datum}>"
