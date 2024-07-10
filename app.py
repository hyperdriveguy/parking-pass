# app.py
from flask import Flask, render_template, jsonify
import csv
import sched
import time
import threading
import rexburg_pass
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
import os
from datetime import datetime

app = Flask(__name__)
scheduler = sched.scheduler(time.time, time.sleep)

def scrape_and_update_data():
    data = rexburg_pass.scrape_parking_pass_info()
    
    # Add a timestamp field to each row
    for row in data:
        row['Timestamp'] = datetime.now().isoformat()

    # Check if the CSV file exists
    if not os.path.isfile('data.csv'):
        # If the file doesn't exist, create a new one
        with open('data.csv', 'w', newline='') as file:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    else:
        # If the file exists, append the new data
        with open('data.csv', 'a', newline='') as file:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerows(data)

    scheduler.enter(1800, 1, scrape_and_update_data)  # Schedule the next scrape in 30 minutes

def generate_historical_plots(data):
    # Group the data by pass type
    data_by_type = defaultdict(list)
    for row in data:
        pass_type = row['Pass Type']
        timestamp = datetime.fromisoformat(row['Timestamp'])
        available = row['Available']
        data_by_type[pass_type].append((timestamp, available))

    # Create a plot for each pass type
    plots = []
    for pass_type, type_data in data_by_type.items():
        timestamps, availables = zip(*type_data)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(timestamps, availables)
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Available Passes')
        ax.set_title(f'Historical Parking Pass Data - {pass_type}')

        # Save the plot to a buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        # Encode the plot as a base64 string
        plot_data = base64.b64encode(buf.read()).decode('utf-8')
        plots.append(plot_data)

        # Close the plot
        plt.close(fig)

    return plots

@app.route('/')
def index():
    # Read data from the local CSV file
    data = []
    with open('data.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)  # Convert reader to a list

    # Get the last row as the latest data
    if data:
        latest_data = [data[-2], data[-1]]
    else:
        latest_data = []

    # Generate the historical plot
    history_plots = generate_historical_plots(data)

    # Pass the latest data and plot data to the template for rendering
    return render_template('index.html', latest_data=latest_data, history_plots=history_plots)

@app.route('/parking-data')
def parking_data():
    data = rexburg_pass.scrape_parking_pass_info()
    return jsonify(data)

if __name__ == '__main__':
    scrape_and_update_data()  # Scrape data initially
    scheduler_thread = threading.Thread(target=scheduler.run)
    scheduler_thread.start()
    app.run(debug=True)
    scheduler_thread.join()  # Wait for the scheduler to finish
