import os
from flask import Flask, render_template, jsonify, send_from_directory, Response, url_for
import csv
from multiprocessing import Process
from pass_history import generate_historical_plots, scrape_and_update_data, run_scraper_forever
import time
import json

subdir_endpoint = '/parking-watch'

app = Flask(__name__)

STATIC_DIR = os.path.join(app.root_path, 'static')
PLOTS_DIR = os.path.join(STATIC_DIR, 'plots')

if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)

def read_data_from_csv():
    data = []
    try:
        with open('data.csv', 'r') as file:
            reader = csv.DictReader(file)
            data = list(reader)
    except FileNotFoundError:
        scrape_and_update_data()
        with open('data.csv', 'r') as file:
            reader = csv.DictReader(file)
            data = list(reader)
    return data

def get_latest_data(data):
    if data:
        latest_data = [data[-2], data[-1]]
    else:
        latest_data = []
    return latest_data

@app.route(subdir_endpoint + '/')
def index():
    data = read_data_from_csv()
    latest_data = get_latest_data(data)
    plot_filenames = generate_and_cache_plots(data)
    return render_template('index.html', latest_data=latest_data, plot_filenames=plot_filenames)

def generate_and_cache_plots(data):
    plot_data = generate_historical_plots(data)
    for data_name, plot in plot_data.items():
        filename = f'{data_name}.png'
        filepath = os.path.join(PLOTS_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(plot.getvalue())
    return tuple(plot_data.keys())

@app.route(subdir_endpoint + '/latest')
def parking_data():
    scrape_and_update_data()
    latest_data = get_latest_data(read_data_from_csv())
    return jsonify(latest_data)

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            latest_data = get_latest_data(read_data_from_csv())
            yield f"data: {json.dumps(latest_data)}\n\n"
            time.sleep(60)  # Wait for 60 seconds before next update

    return Response(event_stream(), mimetype="text/event-stream")

def wsgi_and_scraper():
    Process(target=run_scraper_forever, daemon=True).start()
    app.run()

if __name__ == '__main__':
    Process(target=run_scraper_forever, daemon=True).start()
    app.run(debug=True)
