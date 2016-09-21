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

import argparse
import os.path
import shutil, errno
import subprocess
import time
from help_tools import get_text_in_brackets, hex_dword_to_int, get_slice_from_array, bytes__to__hex_string
from upk_helping_tools.upk_constants import FileExtensions, UpkHexFilesInternals
import copy


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


XCOM_UNPACKED_UPK_DIR = r'C:\Development\XCOM Modding\Work\OriginalCookedPCConsole_Unpacked'
XCOM_DESERIALIZED_UPK_DIR = r'C:\Development\XCOM Modding\Work\CookedPCConsole_Deserialized'
UPK_UTILS_DIR = r'C:\Tools\UPKUtils'
SEARCH_NAME = 'XComGame.XGAbility_Targeted.RollForHit'
OUTPUT_FOLDER = r'C:\Development\XCOM Modding'


def main():
    search_name = input('Enter a search name: ')
    if len(search_name) == 0:
        search_name = SEARCH_NAME
    name_bak = None
    name = search_name.split('.')
    name_bak = copy.deepcopy(name)
    name[-1] += '.txt'
    name = os.path.join(*name)
    name = os.path.join(XCOM_DESERIALIZED_UPK_DIR, name)

    data = None
    with open(name, 'r') as file:
        data = file.read()

    serial_offset_hex = get_text_in_brackets(data, 'SerialOffset:', '\n').strip()[2:]
    serial_size_hex = get_text_in_brackets(data, 'SerialSize:', '(').strip()[2:]

    serial_offset = hex_dword_to_int(serial_offset_hex)
    serial_size = hex_dword_to_int(serial_size_hex)

    print('Offset: 0x{} ({})'.format(serial_offset_hex, serial_offset))
    print('Full Size: 0x{} ({})'.format(serial_size_hex, serial_size))

    name = copy.deepcopy(name_bak)
    name = os.path.join(XCOM_UNPACKED_UPK_DIR, name[0])
    full_name = name + '.u'
    if not os.path.exists(full_name):
        full_name = name + '.upk'

    data = None
    with open(full_name, 'rb') as file:
        data = file.read()

    full_function_data = get_slice_from_array(data, serial_offset, serial_size)
    # full_function_data = data[serial_offset: serial_offset + serial_size]
    function_byte_code = full_function_data[48:-15]

    error_in_bytecode = False
    if function_byte_code[-1:] != b'\x53':
        error_in_bytecode = True

    full_function_data = bytes__to__hex_string(full_function_data).encode()
    function_byte_code = bytes__to__hex_string(function_byte_code).encode()

    name = copy.deepcopy(name_bak)
    name = '.'.join(name)
    output_file_name = os.path.join(OUTPUT_FOLDER, name)
    output_full_function_data_file_name = output_file_name + '.ffbc'
    output_function_byte_code_file_name = output_file_name + '.fbc'

    with open(output_full_function_data_file_name, 'wb') as file:
        file.write(full_function_data)
    with open(output_function_byte_code_file_name, 'wb') as file:
        file.write(function_byte_code)

    if error_in_bytecode:
        raise Exception('EndOfScript wasn\'t found at the end of function\'s bytecode')


if __name__ == "__main__":
    main()
