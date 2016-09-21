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

from upk_helping_tools.upk_utils_api import *
from help_tools import IsOK_ContextHolder, is_ok, is_ok_reader, ResultType, CriteriaType
import shutil

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


def main():
    dir_table = {
        'upk utils dir': r'C:\Tools\UPKUtils',
        'xcom original upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole',
        # 'xcom original upk dir': r'C:\Games\Steam\steamapps\common\XCom-Enemy-Unknown\XEW\Long War Files',
        'xcom unpacked upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole_Unpacked',
        # 'xcom unpacked upk dir': r'C:\Development\XCOM Modding\Work\OriginalCookedPCConsole_Unpacked',
        'xcom deserialized upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole_Deserialized',
        'xcom XEW dir': r'C:\Games\Steam\steamapps\common\XCom-Enemy-Unknown\XEW\XComGame\CookedPCConsole'
    }

    dir_table = {
        'upk utils dir': r'C:\Tools\UPKUtils',
        'xcom original upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole',
        'xcom unpacked upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole_Unpacked',
        'xcom deserialized upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole_Deserialized',
        'xcom XEW dir': r'C:\Games\Steam\steamapps\common\XCom-Enemy-Unknown\XEW\XComGame\CookedPCConsole'
    }

    files_table = {
        'deserialize this file': r"C:\Development\XCOM Modding\Work\CookedPCConsole\XComGame.upk"
    }

    options_table = {
        'u': 0,
        'ud': 1,
        'ds': 2,
        'c': 3,
    }

    context = IsOK_ContextHolder(global_block_results_criteria=ResultType(CriteriaType.optional, set()))

    with is_ok(context, 'ask user'):
        if context:
            context.push_result(True, int(options_table[input('Enter option (\'c\' = "copy files from XEW folder"; '
                                                              '\'u\' = "unpack"; '
                                                              '\'ud\' = "unpack + deserialize"; '
                                                              '\'ds\' = "deserialize single file"): ')]))

    with is_ok(context, 'unpack'):
        if context:
            if context.read_block_result_link('ask user').result in {0, 1}:
                unpack_upk_files(dir_table['upk utils dir'],
                                 dir_table['xcom original upk dir'],
                                 dir_table['xcom unpacked upk dir'],
                                 True,
                                 True)
            context.push_result(True)

    with is_ok(context, 'deserialize'):
        if context:
            if context.read_block_result_link('ask user').result in {1}:
                deserialize_upk_files(dir_table['upk utils dir'],
                                      dir_table['xcom unpacked upk dir'],
                                      dir_table['xcom deserialized upk dir'])
            context.push_result(True)

    with is_ok(context, 'deserialize single file'):
        if context:
            if context.read_block_result_link('ask user').result in {2}:
                deserialize_this_file = input('Enter upk file name or leave blank for default: ')
                if deserialize_this_file == '':
                    deserialize_this_file = files_table['deserialize this file']

                deserialize_result = deserialize_single_upk_file(dir_table['upk utils dir'],
                                                                 deserialize_this_file,
                                                                 dir_table['xcom deserialized upk dir'])
                print('DESERIALIZE RESULT: {}'.format(deserialize_result))
                context.push_result(True, deserialize_result)
            context.push_result(True)

    with is_ok(context, 'copy files from XEW'):
        if context:
            if context.read_block_result_link('ask user').result in {3}:
                set_of_ext = {'.upk', '.u'}
                file_list_result = filtered_file_list(dir_table['xcom XEW dir'], FilteringType.including, set_of_ext)
                for file_name in file_list_result[2]:
                    if 'voice' not in file_name.lower():
                        source_full_file_name = os.path.join(file_list_result[0], file_name)

                        destination_full_file_name = os.path.join(dir_table['xcom original upk dir'], file_name)
                        shutil.copyfile(source_full_file_name, destination_full_file_name)
                        print('COPIED "{}" TO "{}"'.format(source_full_file_name, destination_full_file_name))

            context.push_result(True)

    with is_ok_reader(context):
        print()
        if context:
            print('DONE. SUCCESSFUL.')
        else:
            print('DONE. ERRORS LOG: \n{}'.format(context.get_bad_blocks_str()))


if __name__ == "__main__":
    main()
