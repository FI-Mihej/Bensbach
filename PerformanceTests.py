#!/usr/bin/env python

# Copyright © 2016 ButenkoMS. All rights reserved. Contacts: <gtalk@butenkoms.space>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import json
import os
import socket
import timeit
import copy
import binascii
import math
from ucb_tools_files_cache_manager import get_dir_hash, get_file_hash


"""
Module Docstring
Docstrings: http://www.python.org/dev/peps/pep-0257/
"""

__author__ = "ButenkoMS <gtalk@butenkoms.space>"
__copyright__ = "Copyright © 2016 ButenkoMS. All rights reserved. Contacts: <gtalk@butenkoms.space>"
__credits__ = ["ButenkoMS <gtalk@butenkoms.space>", ]
__license__ = "Apache License, Version 2.0"
__version__ = "0.0.1"
__maintainer__ = "ButenkoMS <gtalk@butenkoms.space>"
__email__ = "gtalk@butenkoms.space"
__status__ = "Prototype"
# __status__ = "Development"
# __status__ = "Production"


def bytes__to__hex_string(input_data, delimiter=' '):
    # 15187.773026963767 inputs per second
    result = delimiter + delimiter.join('{:02X}'.format(b) for b in input_data)
    result = result.strip()
    return result


def bytes__to__hex_string_2(input_data, delimiter=' '):
    # 25105.580648675437 inputs per second
    hex_string = binascii.hexlify(input_data).decode()
    formated_hex_string = ''
    limit = len(hex_string)
    index = 0
    while index < limit:
        formated_hex_string += hex_string[index] + hex_string[index + 1] + delimiter

        index += 2

    return formated_hex_string


def bytes__to__hex_string_3(input_data, delimiter=b' '):
    # 18713.276629462933 inputs per second
    internal_delimiter = bytearray(delimiter)
    hex_string = bytearray(binascii.hexlify(input_data))
    limit = len(hex_string)
    original_data_len = len(input_data)
    delimiter_len = len(delimiter)
    result_length = original_data_len * 2 + (original_data_len - 1) * delimiter_len
    formated_hex_string = bytearray(b' ' * result_length)
    index = 0
    formatted_index = 0
    formatted_index_increment = 2 + delimiter_len
    while index < (limit - 2):
        formated_hex_string[formatted_index] = hex_string[index]
        formated_hex_string[formatted_index + 1] = hex_string[index + 1]
        formated_hex_string[formatted_index + 2] = delimiter[0]

        index += 2
        formatted_index += formatted_index_increment
    formated_hex_string[formatted_index] = hex_string[index]
    formated_hex_string[formatted_index + 1] = hex_string[index + 1]

    return formated_hex_string


def bytes__to__hex_string_4(input_data, delimiter=' '):
    # 48508.80358249831 inputs per second
    fake_start = '00'
    hex_string = fake_start + binascii.hexlify(input_data).decode()
    result = delimiter.join(map(''.join, zip(*[iter(hex_string)]*2)))[len(fake_start):]
    result = result.strip()
    return result


def split_line_1():
    # 416423.8200194595 inputs per second
    line = '1234567890'
    n = 2
    result = [line[i:i+n] for i in range(0, len(line), n)]


import re


def split_line_2():
    # 356858.7812888186 inputs per second
    result = re.findall('..','1234567890')


def split_by_n( seq, n ):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:n]
        seq = seq[n:]
def split_line_3():
    # 357393.95695223165 inputs per second
    result = list(split_by_n("1234567890",2))


def split_line_4():
    # 832897.2556495492 inputs per second
    s = '1234567890'
    result = map(''.join, zip(*[iter(s)]*2))

def split_line_4_1():
    # 357448.78131924325 inputs per second
    s = '1234567890'
    delimiter = ' 0x'
    # result = map(''.join, zip(*[iter(s)]*2))
    result = delimiter.join(map(''.join, zip(*[iter(s)]*2)))


from functools import reduce
from operator import add
try:
    from itertools import izip
except ImportError:  #python3.x
    izip = zip
def split_line_5():
    # 175322.2368058052 inputs per second
    x = iter('1234567890')
    [reduce(add, tup) for tup in izip(x, x)]
    x = iter('1234567890')
    result = [reduce(add, tup) for tup in izip(x, x, x)]


from itertools import islice
def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))
def split_line_6():
    # 156040.4172681141 inputs per second
    s = '1234567890'
    result = list(split_every(2, list(s)))


def hex_string__to__bytes(input_data, delimiter=' '):
    result = b''.join(binascii.unhexlify(b) for b in input_data.split(delimiter))
    return result

def hex_to_bytes_test(numbe_of_iterations=5000):
    input_bytes = hex_string__to__bytes('07 1F 02 81 19 19 19 2E 54 32 00 00 19 12 20 35 FE FF FF 0A 00 92 F9 FF FF 00 '
                                         '1C D5 FB FF FF 16 09 00 50 F9 FF FF 00 01 50 F9 FF FF 09 00 46 32 00 00 00 01 '
                                         '46 32 00 00 09 00 19 12 00 00 00 01 19 12 00 00 16 00 F7 8E 00 00 00 1B DB 00 '
                                         '00 00 00 00 00 00 1B F0 3B 00 00 00 00 00 00 16 2C 23 16 16')
    print(input_bytes)
    b_to_hex_func = bytes__to__hex_string_4
    output_string = b_to_hex_func(input_bytes)
    print(output_string)
    startTime = time.time()
    index = numbe_of_iterations
    while index > 0:
        output_string = b_to_hex_func(input_bytes)
        # split_line_4_1()
        # binascii.hexlify(input_bytes)  # 1665596.0606782623 inputs per second

        index -= 1
    endTime = time.time()
    resultTime = endTime - startTime
    print('It was used', resultTime, 'seconds to make', numbe_of_iterations, 'convertions')
    if resultTime > 0:
        print('There was', numbe_of_iterations / resultTime, 'inputs per second')


def dir_hash_test(numbe_of_iterations=1):
    startTime = time.time()
    dir_name = r'C:\Development\XCOM Modding\Work\LONG WAR BETA 15F\CookedPCConsole_Deserialized\XComGame\XGAbility_Targeted'
    index = numbe_of_iterations
    while index > 0:
        print(get_dir_hash(dir_name))
        index -= 1
    endTime = time.time()
    resultTime = endTime - startTime
    print('It was used', resultTime, 'seconds to make', numbe_of_iterations, 'convertions')
    if resultTime > 0:
        print('There was', numbe_of_iterations / resultTime, 'inputs per second')


def file_hash_test(numbe_of_iterations=1):
    startTime = time.time()
    file_name = r"C:\Development\XCOM Modding\Work\LONG WAR BETA 15F\CookedPCConsole_Unpacked\XComShell.upk"
    index = numbe_of_iterations
    while index > 0:
        print(get_file_hash(file_name))
        index -= 1
    endTime = time.time()
    resultTime = endTime - startTime
    print('It was used', resultTime, 'seconds to make', numbe_of_iterations, 'convertions')
    if resultTime > 0:
        print('There was', numbe_of_iterations / resultTime, 'inputs per second')


def run_single_test():
    # hex_to_bytes_test()
    # dir_hash_test()
    file_hash_test()
    pass

if __name__ == '__main__':
    print(os.name)
    print()
    # run_all_tests()
    run_single_test()
    ...