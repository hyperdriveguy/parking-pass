import csv
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
from time import sleep

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
    fig, ax = plt.subplots(figsize=(10, 6))
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
    fig, ax = plt.subplots(figsize=(10, 6))
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

def run_scraper_forever():
    while True:
        print('Scraping data from city of Rexburg website...', flush=True)
        scrape_and_update_data()
        print('Done, next scrape in 20 seconds\n', flush=True)
        # sleep(1800)  # Sleep for 30 minutes (1800 seconds)
        sleep(20)

if __name__ == '__main__':
    run_scraper_forever()