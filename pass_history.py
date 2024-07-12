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

PLOTS_DIR = 'static/plots/'

if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)

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

def generate_historical_plots(data) -> dict:
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
    available_plot_data = io.BytesIO()
    fig.savefig(available_plot_data, format='png')
    available_plot_data.seek(0)

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
    cost_plot_data = io.BytesIO()
    fig.savefig(cost_plot_data, format='png')
    cost_plot_data.seek(0)

    # Close the plot
    plt.close(fig)

    return {'availability': available_plot_data, 'cost': cost_plot_data}

def generate_and_cache_plots(data):
    plot_data = generate_historical_plots(data)
    for data_name, plot in plot_data.items():
        filename = f'{data_name}.png'
        filepath = os.path.join(PLOTS_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(plot.getvalue())

def get_cached_plots_filenames():
    return os.listdir(PLOTS_DIR)

def trim_csv_data(csv_file):
    with open(csv_file, 'r') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # Read the header row
        
        trimmed_data = [header]
        last_seen = {}  # Dictionary to store the last seen values for each pass type

        for row in reader:
            pass_type, cost, available, valid_from, valid_to, timestamp = row
            cost = convert_to_float(cost)
            available = int(available)
            
            # Check if this pass type has been seen before
            if pass_type in last_seen:
                last_cost, last_available = last_seen[pass_type]
                # Add row only if cost or available has changed
                if cost != last_cost or available != last_available:
                    trimmed_data.append(row)
                    last_seen[pass_type] = (cost, available)
            else:
                # First occurrence of this pass type
                trimmed_data.append(row)
                last_seen[pass_type] = (cost, available)
        
        # Append the last seen data points for each pass type to the trimmed_data
        for pass_type, (cost, available) in last_seen.items():
            if trimmed_data[-1][:2] != [pass_type, str(cost)]:  # Ensure not to duplicate the last line
                trimmed_data.append([pass_type, cost, available, valid_from, valid_to, timestamp])

    with open(csv_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(trimmed_data)

def run_scraper_forever():
    # countdown = 48
    while True:
        print('Scraping data from city of Rexburg website...', flush=True)
        scrape_and_update_data()
        print('Generating plots...', flush=True)
        generate_and_cache_plots(list(csv.DictReader(open('data.csv'))))
        print('Done, next update in 30 minutes\n', flush=True)
        # if countdown == 0:
        #     print('Doing periodic data trim...this may take a while...')
        #     trim_csv_data('data.csv')
        #     print('Finished data trim')
        #     countdown = 48
        # countdown -= 1
        sleep(1800)  # Sleep for 30 minutes (1800 seconds)

if __name__ == '__main__':
    run_scraper_forever()