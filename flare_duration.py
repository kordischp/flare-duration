import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import interp1d

class obs:
    def __init__(self=None, date=None, time=None, flux=None, flux2=None, total_seconds=None):
        self.date = date #str
        self.time = time #str
        self.flux = flux #float     GOES 1-8 / additional data
        self.flux2 = flux2 #float   GOES 0.5-4
        self.total_seconds = total_seconds #float


def read_data_from_file(file_name):
    data = []
    with open(file_name, 'r') as file:
        for line in file:
            if not line.startswith("#"):
                elements = line.strip().split()
                
                date = elements[0]
                time = elements[1]
                flux = float(elements[2])
                flux2 = float(elements[3])

                hh, mm, ss = map(float, time.split(':'))
                total_seconds = 3600*hh+60*mm+ss

                data.append(obs(date, time, flux, flux2, total_seconds))           
    return data

def read_data_from_file_msdp(file_name):
    data = []
    with open(file_name, 'r') as file: #first line example: #10-Sep-2012 10:20:00.000
        for line in file:
            elements = line.strip().split()
            start_date = elements[0]
            start_date=start_date[1:] # Cut '#' sign
            start_time = elements[1]
            break
        for line in file:
            if not line.startswith("#"):
                elements = line.strip().split()
                time = float(elements[0])
                flux = float(elements[1])
                data.append(obs(time=time, flux=flux)) 
    return start_date, start_time, data

def write_data_to_file_msdp(file_name, start_date, start_time, data):
    with open(file_name, 'w') as file:  
        file.write("#Date\tTime\tSignal1\tSignal1\n") # Write the header
        start_datetime = datetime.strptime(start_date + ' ' + start_time, '%d-%b-%Y %H:%M:%S.%f') # Convert start time to datetime object
        for d in data: 
            elapsed_time = timedelta(seconds=d.time) # Calculate elapsed time in seconds
            current_datetime = start_datetime + elapsed_time # Calculate datetime for the current data point
            formatted_date = current_datetime.strftime('%d-%b-%Y') # Format date and time
            formatted_time = current_datetime.strftime('%H:%M:%S.%f')[:-3]  # Truncate microseconds to milliseconds
            file.write(f"{formatted_date}\t{formatted_time}\t{d.flux}\t{d.flux}\n") # Write to file

#===================
def event_start(data, num_points, inc, flux_type):
    flare_start = []
    flux_attr = flux_type
    if flux_type == 'flux_msdp':
        flux_attr = 'flux'
    for i in range(num_points - 1, len(data)):
        if all(getattr(data[i - j], flux_attr) >= getattr(data[i - j - 1], flux_attr) for j in range(1, num_points)):
            if (getattr(data[i], flux_attr) / getattr(data[i - num_points], flux_attr) > inc):
                flare_start.append(obs(date=data[i - num_points].date, time=data[i - num_points].time,
                                       total_seconds=data[i - num_points].total_seconds, **{flux_attr: getattr(data[i - num_points], flux_attr)}))
                print(flux_type, "Flare start Time:", flare_start[0].time, "Flux:", getattr(flare_start[0], flux_attr))
                break
    if not flare_start:
        raise ValueError("No points found for flare_start: ", flux_type)
    return flare_start


def event_max(data, flux_type):
    flare_max = []
    flux_attr = flux_type
    if flux_type == 'flux_msdp':
        flux_attr = 'flux'
    flare_max_value = max(data, key=lambda x: getattr(x, flux_attr))
    flare_max.append(obs(**{flux_attr: getattr(flare_max_value, flux_attr), 'total_seconds': None}))
    for d in data:
        if getattr(d, flux_attr) == getattr(flare_max[0], flux_attr):
            flare_max[0].total_seconds = d.total_seconds
            flare_max[0].time = d.time
            print(flux_type, "Flare max Time:", flare_max[0].time, "Flux:", getattr(flare_max[0], flux_attr))
            break
    return flare_max


def event_end(data, flare_start, flare_max, th, flux_type):
    flare_end = []
    flux_attr = flux_type
    if flux_type == 'flux_msdp':
        flux_attr = 'flux'
    for d in data:
        if d.total_seconds > flare_max[0].total_seconds:
            if getattr(d, flux_attr) < getattr(flare_start[0], flux_attr) + (getattr(flare_max[0], flux_attr) - getattr(flare_start[0], flux_attr)) * th:
                flare_end.append(obs(time=d.time, total_seconds=d.total_seconds, **{flux_attr: getattr(d, flux_attr)}))
                print(flux_type, "Flare end Time:", flare_end[0].time, "Flux:", getattr(flare_end[0], flux_attr))
                break
    if not flare_end:
        raise ValueError("No points found for flare_end: ", flux_type)
    return flare_end


def make_plot(data, flare_start, flare_max, flare_end, flux_type):
    # Convert time strings to datetime objects
    times = [datetime.strptime(d.time, "%H:%M:%S.%f") for d in data]
    flux_attr = flux_type
    if flux_type == 'flux_msdp':
        flux_attr = 'flux'
    fluxes = [getattr(d, flux_attr) for d in data]
    
    plt.figure(figsize=(10, 6)) # Create the plot
    plt.semilogy(times, fluxes, marker='o', linestyle='None', markersize=1)
    
    flare_points = [flare_start[0], flare_max[0], flare_end[0]] # Plot flare start, max and end points
    flare_colors = ['r', 'r', 'r']
    flare_markers = ['+', '+', '+']
    for flare_point, color, marker in zip(flare_points, flare_colors, flare_markers):
        flare_time = datetime.strptime(flare_point.time, "%H:%M:%S.%f")
        plt.scatter([flare_time], [getattr(flare_point, flux_attr)], color=color, marker=marker, s=400)
    
    plt.xlabel('Time')
    plt.ylabel('Flux [Watts m$^{-2}$]')
    plt.title('GOES X-ray                  ' + data[0].date)
    
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S')) # Format x-axis ticks to display only the time portion
    plt.grid(True)
    plt.tight_layout()
    plt.show()

#=================
def boxcar_average(data, window_size, new_interval, flux_type):
    """Apply a boxcar (moving average) filter to the data and resample it to have a point every 'new_interval' seconds."""
    smoothed_fluxes = []
    sm_data = []
    half_window = window_size // 2

    time_b = [d.time for d in data]
    flux_b = [getattr(d, flux_type) for d in data]
    total_seconds_b = [d.total_seconds for d in data]
    date_b = [d.date for d in data]
    start_date = date_b[0]

    for i in range(half_window, len(data) - half_window):  # Smooth the data
        smoothed_fluxes.append(np.mean(flux_b[i - half_window:i + half_window]))

    # Resample the smoothed data
    interp_func = interp1d(total_seconds_b[half_window:len(data) - half_window], smoothed_fluxes, kind='linear')
    new_total_seconds = np.arange(total_seconds_b[half_window], total_seconds_b[-half_window], new_interval)
    new_flux = interp_func(new_total_seconds)

    for total_seconds, flux in zip(new_total_seconds, new_flux):
        current_datetime = datetime.strptime(start_date, '%d-%b-%Y') + timedelta(seconds=total_seconds)
        formatted_date = current_datetime.strftime('%d-%b-%Y')
        formatted_time = current_datetime.strftime('%H:%M:%S.%f')[:-3]  # Truncate microseconds to milliseconds
        
        if flux_type == 'flux':
            sm_data.append(obs(date=formatted_date, time=formatted_time, flux=flux, total_seconds=total_seconds))
        elif flux_type == 'flux2':
            sm_data.append(obs(date=formatted_date, time=formatted_time, flux2=flux, total_seconds=total_seconds))
    return sm_data


# Plot 3 subplots
def plot_combined(data_goes, flare_start_goes, flare_max_goes, flare_end_goes, 
                  data_goes2, flare_start_goes2, flare_max_goes2, flare_end_goes2,
                  data_msdp, flare_start_msdp, flare_max_msdp, flare_end_msdp,
                  time_range=None):
    def plot_sub_data(data, flare_start, flare_max, flare_end, subplot_index, title, flux_attr, time_range, y_label, use_log_scale=True):
        # Convert time strings to datetime objects
        times = [datetime.strptime(d.time, "%H:%M:%S.%f") for d in data]
        fluxes = [getattr(d, flux_attr) for d in data]

        # Create subplot
        plt.subplot(3, 1, subplot_index)
        if use_log_scale:
            plt.semilogy(times, fluxes)
        else:
            plt.plot(times, fluxes)

        # Plot flare max and end points
        flare_points = [flare_start[0], flare_max[0], flare_end[0]]
        flare_colors = ['r', 'r', 'r']
        flare_markers = ['+', '+', '+']
        for flare_point, color, marker in zip(flare_points, flare_colors, flare_markers):
            flare_time = datetime.strptime(flare_point.time, "%H:%M:%S.%f")
            plt.scatter([flare_time], [getattr(flare_point, flux_attr)], color=color, marker=marker, s=400)

        #plt.xlabel('Time')
        plt.ylabel(y_label, fontsize=16)
        plt.title(title, fontsize=18)

        # Format x-axis ticks to display only the time portion
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))
        plt.gca().tick_params(axis='x', labelsize=15)
        plt.gca().tick_params(axis='y', labelsize=15)
        plt.grid(True)

        # Set the x-axis time range if specified
        if time_range:
            plt.xlim(time_range)

    plt.figure(figsize=(16, 16)) # Create the plot
    plot_sub_data(data_goes, flare_start_goes, flare_max_goes, flare_end_goes, 1, 'GOES 1-8 \u00C5   ' + data_goes[0].date, 'flux', time_range, 'Strumień [W*m$^{-2}$]') # Plot GOES data
    plot_sub_data(data_goes2, flare_start_goes2, flare_max_goes2, flare_end_goes2, 2, 'GOES 0.5-4 \u00C5', 'flux2', time_range, 'Strumień [W*m$^{-2}$]') # Plot GOES2 data
    plot_sub_data(data_msdp, flare_start_msdp, flare_max_msdp, flare_end_msdp, 3, 'MSDP H\u03B1', 'flux', time_range, 'Jasność [SCh]', use_log_scale=False) # Plot MSDP data

    # Adjust layout to increase vertical spacing between subplots
    plt.subplots_adjust(top=0.95, bottom=0.05, hspace=0.2)

    # Save and show the plot
    plt.savefig(data_goes[0].date+".eps", format='eps', bbox_inches='tight')
    plt.savefig(data_goes[0].date+".png", format='png')
    plt.show()


def main():
    data = read_data_from_file("goes_data.txt") # Read GOES data

    MSDP = True # Read additional data from file: True/False
    if MSDP:
        # Read additional data, convert data to match the GOES format, read again from formatted file
        start_date, start_time, data_msdp = read_data_from_file_msdp("MSDP_python.dat")
        write_data_to_file_msdp("MSDP_python_v2.dat", start_date, start_time, data_msdp)
        data_msdp = read_data_from_file("MSDP_python_v2.dat")
   
    # Goes 1-8A
    flare_start = event_start(data, num_points=6, inc=1.02, flux_type='flux') # num_points- number of consecutive increasing points, inc - inclination between the first and last point
    flare_max = event_max(data, flux_type='flux')
    flare_end = event_end(data, flare_start, flare_max, th=0.05, flux_type='flux') # th - threshhold level, 0.0 - same end value as start value, 1.0 - same end value as max value
    print("Flare duration: ", (flare_end[0].total_seconds - flare_start[0].total_seconds)/60, "min")

    # Goes 0.5-4A
    sm_data=boxcar_average(data, window_size=4, new_interval=6, flux_type='flux2') # Smooth GOES 0.5-4 data

    flare_start2 = event_start(sm_data, num_points=6, inc=1.02, flux_type='flux2')
    flare_max2 = event_max(sm_data, flux_type='flux2')
    flare_end2 = event_end(sm_data, flare_start2, flare_max2, th=0.01, flux_type='flux2')
    print("Flare2 duration: ", (flare_end2[0].total_seconds - flare_start2[0].total_seconds)/60, "min")

    # MSDP
    if MSDP:
        sm_data_msdp=boxcar_average(data_msdp, window_size=40, new_interval=2, flux_type='flux') # Smooth data

        flare_start_msdp = event_start(sm_data_msdp, num_points=3, inc=1.02, flux_type='flux_msdp')
        flare_max_msdp = event_max(sm_data_msdp, flux_type='flux_msdp')
        flare_end_msdp = event_end(sm_data_msdp, flare_start_msdp, flare_max_msdp, th=-0.6, flux_type='flux_msdp')
        print("Flare msdp duration: ", (flare_end_msdp[0].total_seconds - flare_start_msdp[0].total_seconds)/60, "min")

    make_plot(data,flare_start,flare_max,flare_end, flux_type='flux')
    make_plot(sm_data,flare_start2,flare_max2,flare_end2, flux_type='flux2')

    if MSDP:
        make_plot(sm_data_msdp,flare_start_msdp,flare_max_msdp,flare_end_msdp, flux_type='flux_msdp')

    
    # Set time range for plots, adjust range manually
    if MSDP:
        start_time_range = datetime.strptime("10:17:00.000", "%H:%M:%S.%f")
        end_time_range = datetime.strptime("10:52:00.000", "%H:%M:%S.%f")
        time_range = (start_time_range, end_time_range)
        plot_combined(data, flare_start, flare_max, flare_end,
                    sm_data, flare_start2, flare_max2, flare_end2,
                    sm_data_msdp, flare_start_msdp, flare_max_msdp, flare_end_msdp, time_range )


    """  
    # Quick plot to check data, e.g. before or after smoothing
    plt.figure(figsize=(10, 6))
    plt.plot(sm_time, sm_flux, marker='o', linestyle='-', markersize=1)
    plt.tight_layout()
    plt.show()
    for d in data:
        print("data:", d.time,d.flux)
    print(data[0].time, data[0].flux)
    """

if __name__ == "__main__":
    main()
