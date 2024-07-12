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
        
        # Read all rows into memory
        all_rows = [row for row in reader if row]  # Filter out empty rows
        
        # Get all unique pass types
        all_pass_types = set(row[header.index('Pass Type')] for row in all_rows)
        print('All pass types:', all_pass_types)

        unique_data_points = []
        for pass_type in all_pass_types:
            # Get all updates for the current pass type sorted by timestamp
            updates = sorted([row for row in all_rows if row[header.index('Pass Type')] == pass_type],
                             key=lambda row: row[header.index('Timestamp')])
            print(f'Updates for {pass_type}:', len(updates))  # Print the number of updates instead of the full list
            
            # Iterate over the updates. For ranges of updates that don't have changes in
            # availability or cost, remove the data points between.
            # For example, if there are 3 updates that show the same cost and availability,
            # only keep the first and last updates.
            for i, update in enumerate(updates):
                if i == 0 or i == len(updates) - 1:
                    unique_data_points.append(update)
                elif (update[header.index('Cost')] != updates[i - 1][header.index('Cost')] or
                      update[header.index('Available')] != updates[i - 1][header.index('Available')]):
                    unique_data_points.append(updates[i - 1])
                    unique_data_points.append(update)
        
        print('Unique data points:', len(unique_data_points))
        
        # Write the unique data points to a new CSV file
    with open(csv_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(unique_data_points)

def run_scraper_forever():
    countdown = 0
    while True:
        print('Scraping data from city of Rexburg website...', flush=True)
        scrape_and_update_data()
        print('Generating plots...', flush=True)
        generate_and_cache_plots(list(csv.DictReader(open('data.csv'))))
        print('Done, next update in 30 minutes\n', flush=True)
        if countdown == 0:
            print('Doing periodic data trim...this may take a while...')
            trim_csv_data('data.csv')
            print('Finished data trim')
            countdown = 48
        countdown -= 1
        sleep(1800)  # Sleep for 30 minutes (1800 seconds)

if __name__ == '__main__':
    run_scraper_forever()