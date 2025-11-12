from flask import Flask
from .models import db #maakt het mogelijk om database te koppelen aan flask app
from .config import Config #zorgt ervoor dat de app weet waar de database staat
from flask_migrate import Migrate
migrate = Migrate()
def create_app():
    app=Flask(__name__)#Hier maak je de Flask app-instantie aan.
#Dit is het centrale object dat routes, configuratie en extensies vasthoudt

    app.config.from_object(Config) #Laadt alle configuratievariabelen uit de Config-klasse in de Flask-app.

    db.init_app(app) #koppel SQLalchemy database aan flask app

    
    migrate.init_app(app, db) #activeert app context zodat flask weet welke app actief is, dan maakt alle tabellen van de database aan
    
    from .routes import main  #Hier importeer je je blueprint (main), die je routes (endpoints) bevat.
    app.register_blueprint(main) #Je “registreert” de blueprint bij de Flask app, zodat de routes actief worden.

    return app
