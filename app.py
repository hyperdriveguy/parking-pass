import csv
import json
import time
from collections import defaultdict

from flask import Flask, Response, jsonify, render_template

from pass_history import get_cached_plots_filenames, scrape_and_update_data

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
    if not data:
        return []

    # Group the data by pass type
    data_by_type = defaultdict(list)
    for row in data:
        pass_type = row['Pass Type']
        data_by_type[pass_type].append(row)

    # Get the latest data for each pass type
    latest_data = []
    for pass_type, type_data in data_by_type.items():
        latest_data.append(type_data[-1])

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
