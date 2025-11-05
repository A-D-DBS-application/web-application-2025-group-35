from app import create_app #importeert create_app

app = create_app() #maakt flask app aan

if __name__ == '__main__': #wordt alleen uitgevoerd als we script direct runnen 
    app.run(debug=True) #start flask in debug modus