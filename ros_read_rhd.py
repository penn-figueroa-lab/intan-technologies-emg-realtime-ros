#!/usr/bin/env python
import sys
import time
import numpy as np
import struct
import glob
import re

from intanutil.header import read_header, get_timestamp_signed
from intanutil.data import read_one_block, get_bytes_per_data_block
import matplotlib.pyplot as plt

import rospy
from std_msgs.msg import Float64MultiArray, Int32MultiArray


def analog_read(fid, num_samples, num_channels):
    return np.fromfile(fid, dtype='uint16', count=num_samples * num_channels).reshape(num_channels, num_samples)


def get_header(fid):
    header = read_header(fid)

    samples_per_block = header['num_samples_per_data_block']
    format_sign = 'i' if get_timestamp_signed(header) else 'I'
    format_expression = '<' + format_sign * samples_per_block

    read_length = 4 * samples_per_block + 2 * (
            header['num_supply_voltage_channels'] + header['num_temp_sensor_channels'] + samples_per_block *
            header['num_amplifier_channels'] + int(samples_per_block / 4) * header['num_aux_input_channels']
            + samples_per_block * header['num_board_adc_channels']
            + samples_per_block * header['num_board_dig_in_channels']
            + samples_per_block * header['num_board_dig_out_channels'])
    return header, samples_per_block, format_expression, read_length


def read_data(filename):
    fid = open(filename, 'rb')
    common_name, date_info, time_info, _ = re.split('\.|_', filename)
    datetime_info = int(date_info + time_info)
    
    pub = rospy.Publisher('emg_reading', Int32MultiArray, queue_size=10)
    rospy.init_node('emg_reading')
    data_to_send = Int32MultiArray()

    header, samples_per_block, format_expression, read_length = get_header(fid)

    pointer_wo_header = fid.tell()
    fid.seek(0, 2)
    pointer_eo = fid.tell()
    data_length = pointer_eo - pointer_wo_header
    extra_length = data_length % read_length
    pointer_current = pointer_eo - extra_length
    fid.seek(pointer_current)

    while True:
        fid.seek(0, 2)  # Move the file pointer to the end of the file.
        file_size = fid.tell()

        if file_size - pointer_current >= read_length:
            fid.seek(pointer_current)
            print(get_timestamp_signed(header))
            timestamp = np.array(struct.unpack(format_expression, fid.read(4 * samples_per_block)),
                                 dtype=np.int_ if get_timestamp_signed(header) else np.uint)

            amplifier_data = analog_read(fid, samples_per_block, header['num_amplifier_channels'])
            aux_input_data = analog_read(fid, int(samples_per_block / 4), header['num_aux_input_channels'])
            supply_voltage_data = analog_read(fid, 1, header['num_supply_voltage_channels'])
            temp_sensor_data = analog_read(fid, 1, header['num_temp_sensor_channels'])
            board_adc_data = analog_read(fid, samples_per_block, header['num_board_adc_channels'])

            digital_in = np.array(struct.unpack('<' + 'H' * samples_per_block * header['num_board_dig_in_channels'], fid.read(2 * samples_per_block * header['num_board_dig_in_channels'])))
            digital_out = np.array(struct.unpack('<' + 'H' * samples_per_block * header['num_board_dig_out_channels'], fid.read(2 * samples_per_block * header['num_board_dig_out_channels'])))
            pointer_current = fid.tell()
        else:
            files = glob.glob(filename[:1] + '*.rhd')
            files_split = [re.split('\.|_', file) for file in files]
            times_split = [int(file[1] + file[2]) for file in files_split]
            max_val = max(times_split)

            if max_val > datetime_info:
                datetime_info = max_val
                index = times_split.index(max_val)
                fid = open(files[index], 'rb')
                fid.seek(0, 2)
                file_size = fid.tell()
                while file_size < 8082:
                    fid.seek(0, 2)
                    file_size = fid.tell()
                fid.seek(0)
                header, samples_per_block, format_expression, read_length = get_header(fid)
                pointer_current = fid.tell()

            continue
        for i in range(amplifier_data.shape[1]):
            data_to_send.data = amplifier_data[:, i].tolist()
            pub.publish(data_to_send)
        


if __name__ == '__main__':
    a = read_data(sys.argv[1])
