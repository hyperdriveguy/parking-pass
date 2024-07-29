import csv
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta

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

def parse_timestamp(timestamp_str):
    try:
        return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print(f"Unable to parse timestamp: {timestamp_str}")
            return datetime.min

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
    current_time = datetime.now()
    for pass_type, type_data in data_by_type.items():
        # Sort data for each pass type by timestamp
        sorted_data = sorted(type_data, key=lambda x: parse_timestamp(x['Timestamp']), reverse=True)

        # Check if the most recent data is not older than 3 days
        if sorted_data:
            latest_timestamp = parse_timestamp(sorted_data[0]['Timestamp'])
            if current_time - latest_timestamp <= timedelta(days=3):
                latest_data.append(sorted_data[0])

    # Sort the final list from most recent to oldest
    latest_data.sort(key=lambda x: parse_timestamp(x['Timestamp']), reverse=True)

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
