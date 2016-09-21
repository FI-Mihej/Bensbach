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

from upk_helping_tools.upk_utils_api import patch_upk_file, export_from_upk_to_pseudo_code
from help_tools import IsOK_ContextHolder, is_ok, is_ok_reader, ResultType, CriteriaType, IsOK_BlockFailed, \
    filtered_file_list, FilteringType, get_text_in_brackets
import shutil
import os.path

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


def get_upk_file_names_from_upk_mod_file(upk_mod_file_name):
    upk_files_list = list()

    parameter_name = 'UPK_FILE'
    data_brackets = ('=', '\n')
    data = None
    with open(upk_mod_file_name, 'r') as file:
        data = file.readlines()

    for line in data:
        if parameter_name in line:
            strip_line = line.strip()
            if line.startswith(parameter_name):
                strip_line = strip_line[len(parameter_name):]
                if not strip_line.endswith('\n'):
                    strip_line = ''.join([strip_line, '\n'])
                upk_file_name = get_text_in_brackets(strip_line, data_brackets[0], data_brackets[1])
                upk_file_name = upk_file_name.strip()
                upk_files_list.append(upk_file_name)
                # print('UPK FILE "{}"'.format(upk_file_name))

    return upk_files_list


def main():
    dir_table = {
        'upk utils dir': r'C:\Tools\UPKUtils',
        'xcom original upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole',
        'xcom unpacked upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole_Unpacked',
        'xcom deserialized upk dir': r'C:\Development\XCOM Modding\Work\CookedPCConsole_Deserialized',
        'xcom unpacked upk dir in change': r'C:\Development\XCOM Modding\Work\InChange',
        'exported pseudo code dir': r"C:\Development\XCOM Modding\Work\pseudocode"
    }

    files_table = {
        'mod file': r"C:\Development\XCOM Modding\Work\Mod files\new_hit_damage_calc.txt"
    }

    options_table = {
        'i': False,
        'u': True
    }

    context = IsOK_ContextHolder(global_block_results_criteria=ResultType(CriteriaType.optional, set()),
                                 save_debug_trace=True)

    with is_ok(context, 'get mod file name'):
        if context:
            mod_file_name = input('Enter mod file name [{}]: '.format(files_table['mod file']))
            if mod_file_name == '':
                mod_file_name = files_table['mod file']
            context.push_result(True, mod_file_name)

    with is_ok(context, 'choose an option'):
        if context:
            option_name = input('Choose an option( \'i\' = "install"; \'u\' = "uninstall"): ')
            if option_name not in options_table:
                raise IsOK_BlockFailed('Unknown option "{}"'.format(option_name))
            context.push_result(True, options_table[option_name])

    is_uninstall = False
    with is_ok(context, 'copy files to in change dir'):
        if context:
            mod_file_name = context.read_block_result_link('get mod file name').result
            is_uninstall = context.read_block_result_link('choose an option').result
            if not is_uninstall:
                # set_of_ext = {'.upk', '.u'}
                # file_list_result = filtered_file_list(dir_table['xcom unpacked upk dir'], FilteringType.including,
                #                                       set_of_ext)
                upk_files_list = get_upk_file_names_from_upk_mod_file(mod_file_name)
                print('COPIED FILES:')
                for file_name in upk_files_list:
                    source_full_file_name = os.path.join(dir_table['xcom unpacked upk dir'], file_name)

                    destination_full_file_name = os.path.join(dir_table['xcom unpacked upk dir in change'], file_name)
                    shutil.copyfile(source_full_file_name, destination_full_file_name)
                    # print('COPIED "{}" TO "{}"'.format(source_full_file_name, destination_full_file_name))
                    print('    ', file_name)
            context.push_result(True)

    with is_ok(context, 'apply initial patch'):
        if context:
            file_name = context.read_block_result_link('get mod file name').result
            is_uninstall = context.read_block_result_link('choose an option').result

            patch_result = patch_upk_file(dir_table['upk utils dir'],
                                          dir_table['xcom unpacked upk dir in change'],
                                          file_name,
                                          is_uninstall)

            if patch_result == 0:
                context.push_result(True)
            else:
                raise IsOK_BlockFailed('Patch failed with exitcode "{}"'.format(patch_result))

    if not is_uninstall:
        with is_ok(context, 'read info from initial mod file'):
            if context:
                initial_mod_file_name = context.read_block_result_link('get mod file name').result
                function_object_name = None
                upk_file_name = None
                with open(initial_mod_file_name, 'r') as file:
                    initial_mod_content = file.readlines()
                    for line in initial_mod_content:
                        if 'OBJECT' in line:
                            if ':' in line:
                                function_object_name = get_text_in_brackets(line, '=', ':').strip()
                            else:
                                function_object_name = get_text_in_brackets(line, '=', '\n').strip()
                        if 'UPK_FILE' in line:
                            upk_file_name = get_text_in_brackets(line, '=', '\n').strip()
                if (function_object_name is not None) and (upk_file_name is not None):
                    context.push_result(True, (function_object_name, upk_file_name))

        with is_ok(context, 'reread function\'s bytecode to mod file with pseudo code'):
            if context:
                function_object_name, upk_file_name = context.read_block_result_link(
                        'read info from initial mod file').result
                upk_full_file_name = os.path.join(dir_table['xcom unpacked upk dir in change'], upk_file_name)
                output_mod_full_file_name = os.path.join(dir_table['exported pseudo code dir'],
                                                         ''.join([function_object_name, '.code']))
                export_from_upk_to_pseudo_code(dir_table['upk utils dir'],
                                               upk_full_file_name,
                                               function_object_name,
                                               output_mod_full_file_name)
                context.push_result(True, output_mod_full_file_name)

        with is_ok(context, 'apply final patch'):
            if context:
                file_name = context.read_block_result_link(
                        'reread function\'s bytecode to mod file with pseudo code').result
                is_uninstall = context.read_block_result_link('choose an option').result
                patch_result = patch_upk_file(dir_table['upk utils dir'],
                                              dir_table['xcom unpacked upk dir in change'],
                                              file_name,
                                              is_uninstall)

                if patch_result == 0:
                    context.push_result(True)
                else:
                    raise IsOK_BlockFailed('Patch failed with exitcode "{}"'.format(patch_result))

    with is_ok_reader(context):
        print()
        if context:
            print('DONE. SUCCESSFUL.')
        else:
            print('DONE. ERRORS LOG: \n{}'.format(context.get_bad_blocks_str()))

if __name__ == "__main__":
    main()
