from flask import Flask, render_template, jsonify, Response
import csv
from pass_history import scrape_and_update_data, get_cached_plots_filenames
import time
import json

subdir_endpoint = '/parking-watch'

app = Flask(__name__)

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
    latest_data = get_latest_data(read_data_from_csv())
    plot_filenames = get_cached_plots_filenames()
    return render_template('index.html', latest_data=latest_data, plot_filenames=plot_filenames)

@app.route(subdir_endpoint + '/latest')
def parking_data():
    scrape_and_update_data()
    latest_data = get_latest_data(read_data_from_csv())
    return jsonify(latest_data)

@app.route(subdir_endpoint + '/stream')
def stream():
    def event_stream():
        while True:
            latest_data = get_latest_data(read_data_from_csv())
            yield f"data: {json.dumps(latest_data)}\n\n"
            time.sleep(60)  # Wait for 60 seconds before next update

    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True)
