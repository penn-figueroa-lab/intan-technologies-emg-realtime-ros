# Intan EMG ROS publisher
The code for reading the Intan Technologies file in real time and publishing it into ROS. Modified the original [Python code](https://intantech.com/files/load_intan_rhd_format.zip) provided by the company to fix the existing bugs.

## Usage
1. Start the Intan Technologies [RHX software](https://intantech.com/downloads.html?tabSelect=Software).
2. Set "Write Latency" in "Performance Optimization" to "Lowest."
3. Choose "Traditional Intan File Format" and unclick "Create new save directory with timestamp for each recording" in "Select Saved Data File Format."
4. Set a file name and directory to save.
5. Source the ros and run the file with the path to the file you want to start from.
```bash
python ros_read_rhd.py [file path]
```
