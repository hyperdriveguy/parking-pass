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
import re

subdir_endpoint = '/parking-watch'

app = Flask(__name__)
scheduler = sched.scheduler(time.time, time.sleep)
scheduler_thread = threading.Thread(target=scheduler.run)

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

def convert_to_float(value):
    # Remove non-numeric characters from the string
    cleaned_value = re.sub(r'[^0-9\.]', '', value)
    
    # Convert the cleaned string to a float
    return float(cleaned_value)

def generate_historical_plots(data):
    # Group the data by pass type
    data_by_type = defaultdict(list)
    for row in data:
        pass_type = row['Pass Type']
        timestamp = datetime.fromisoformat(row['Timestamp'])
        available = float(row['Available'])
        cost = convert_to_float(row['Cost'])  # Convert cost to float
        data_by_type[pass_type].append((timestamp, available, cost))

    # Create a plot for available passes with different colored lines
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    for i, (pass_type, type_data) in enumerate(data_by_type.items()):
        timestamps, availables, _ = zip(*type_data)
        ax.plot(timestamps, availables, color=colors[i % len(colors)], label=pass_type)
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Available Passes')
    ax.set_title('Historical Parking Pass Data - Available Passes')
    ax.legend()
    ax.set_ylim(bottom=0)  # Set y-axis to start at 0

    # Save the plot to a buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    # Encode the plot as a base64 string
    available_plot_data = base64.b64encode(buf.read()).decode('utf-8')

    # Close the plot
    plt.close(fig)

    # Create a plot for cost with different colored lines
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, (pass_type, type_data) in enumerate(data_by_type.items()):
        timestamps, _, costs = zip(*type_data)
        ax.plot(timestamps, costs, color=colors[i % len(colors)], label=pass_type)
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Cost')
    ax.set_title('Historical Parking Pass Data - Cost in USD')
    ax.legend()
    ax.set_ylim(bottom=0)  # Set y-axis to start at 0

    # Save the plot to a buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    # Encode the plot as a base64 string
    cost_plot_data = base64.b64encode(buf.read()).decode('utf-8')

    # Close the plot
    plt.close(fig)

    return available_plot_data, cost_plot_data

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

def wsgi_runner():
    scrape_and_update_data()  # Scrape data initially
    scheduler_thread.start()
    scheduler.enter(1800, 1, scrape_and_update_data)  # Schedule the next scrape in 30 minutes
    app.run()
    scheduler_thread.join()  # Wait for the scheduler to finish

if __name__ == '__main__':
    scrape_and_update_data()  # Scrape data initially
    scheduler_thread.start()
    scheduler.enter(1800, 1, scrape_and_update_data)  # Schedule the next scrape in 30 minutes
    app.run(debug=True) # Debug mode
    scheduler_thread.join()  # Wait for the scheduler to finish
