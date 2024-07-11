<br />
<div align="center">
  
<h3 align="center">Flare Duration and Parameters</h3>

  <p align="center">
    Calculate flare parameters, such as the start, maximum and end time.
</div>

## About The Project
The program aims to analyze solar flare data from the GOES satellite and other 
sources. The analysis consists of:
* Reading solar flare data from files. 
* Optionally smoothing the data using a boxcar (moving average) filter.
* Identifying the start, maximum, and end points of solar flares.
* Plotting the data and marking these points.
* Calculating the duration
* Optionally combining and comparing data from multiple sources.

By default plots of each type are displayed individually and not saved automatically (GOES flux from both ranges and additional data). Then a multiplot of all 3 plots is
displayed and save to png and eps files.

## Methods
The start time of a flare is defined as the first point in a series of consecutive 
points that have increasing value. The number of points for this series is 
defined in a variable `num_points`. Another condition that must be fulfilled
is that the increase in value between the first and last point in the series
must exceed a set value - defined in the `inc` variable.

The point of maximum is trivial to find, while the end point is harder to
determine. In this program it is defined as a multiplication (`th`) of
the difference of the max and start values. So if the variable `th` is set
to 0.0 then the end point is the first point after maximum, which has the
same signal (flux) value as the start point. 

Duration of the flare is simply the time from the start point to the end point. All
of the parameters should be set separately for GOES 1-8, GOES 0.5-4 and additional 
data.

## Usage
To use the program download GOES data or use the sample data provided in this
repository. Optionally provide additional data from a different source, this is
often called MSDP data in the code as it was originally used with data from
a Multichannel Subtractive Double Pass spectrograph. The data from GOES needs
to have a *#* as the first sign in the first 14 lines. Additional data needs to
have the time of the beginning of observations in the first line, in this format:
`#10-Sep-2012 10:20:00.000`, then it should have the signal in the seconds column
and the time in the first column. Time should be specified as seconds after the
beginning of observations. To use additional data, set `MSDP` variable to `True`.

All the parameters need to be specified inside the code, these include:
* file names for goes and optionally for the additional data
* num_points - recommended 3 to 7
* inc - recommended 1.01 to 1.1
* th - depends on the data and criteria, set to 0.0, increase if end not found
* start_time_range - start time for the multiplot 
* end_time_range - end time for the multiplot

Here is how to multiplot looks, red crosses represent found points:
![alt text](/images/image1.png)


## Prerequisites
To run the program, a few packages are required:

* numpy, scipy and matplotlib
  ```sh
  pip install numpy matplotlib scipy
  ```




