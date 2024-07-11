# app.py
from flask import Flask, render_template, jsonify
import csv
# Import library for running scraper forever in a different process
from multiprocessing import Process
import rexburg_pass
from pass_history import generate_historical_plots, scrape_and_update_data, run_scraper_forever

subdir_endpoint = '/parking-watch'

app = Flask(__name__)

@app.route(subdir_endpoint + '/')
def index():
    # Read data from the local CSV file
    data = []
    try:
        with open('data.csv', 'r') as file:
            reader = csv.DictReader(file)
            data = list(reader)  # Convert reader to a list
    except FileNotFoundError:
        scrape_and_update_data()  # Scrape data initially

    # Get the last row as the latest data
    if data:
        latest_data = [data[-2], data[-1]]
    else:
        latest_data = []

    # Generate the historical plot
    history_plots = generate_historical_plots(data)

    # Pass the latest data and plot data to the template for rendering
    return render_template('index.html', latest_data=latest_data, history_plots=history_plots)

@app.route(subdir_endpoint + '/latest')
def parking_data():
    data = rexburg_pass.scrape_parking_pass_info()
    return jsonify(data)

def wsgi_and_scraper():
    Process(target=run_scraper_forever, daemon=True).start()
    app.run()

if __name__ == '__main__':
    Process(target=run_scraper_forever, daemon=True).start()
    app.run(debug=True) # Debug mode
