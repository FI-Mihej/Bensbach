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

from unreal_script_byte_code_compiller_decompiller import run_compile_and_reformat_source_code_with_debug_out, \
    compile_and_reformat_source_code
from patch_upk import main as patch_upk_main
from help_tools import filtered_file_list, FilteringType
import os.path
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


def install_files_to_steam_folder():
    dir_table = {
        'steam folder': r'C:\Games\Steam',
        'steam xcom xew upk dir': r'steamapps\common\XCom-Enemy-Unknown\XEW\XComGame\CookedPCConsole',
        'xcom unpacked upk dir in change': r'C:\Development\XCOM Modding\Work\InChange',
    }

    output_dir = os.path.join(dir_table['steam folder'], dir_table['steam xcom xew upk dir'])

    original_current_dir = os.getcwd()
    try:
        os.chdir(output_dir)
        print('CURRENT DIR: {}'.format(output_dir))

        set_of_ext = {'.upk', '.u'}
        file_list_result = filtered_file_list(dir_table['xcom unpacked upk dir in change'],
                                              FilteringType.including, set_of_ext)
        for filename in file_list_result[2]:
            full_file_name = os.path.join(file_list_result[0], filename)
            print('COPY FILE: {} TO {}'.format(full_file_name, filename))
            shutil.copyfile(full_file_name, filename)
    finally:
        os.chdir(original_current_dir)


def main():
    print('COMPILATION...')
    run_compile_and_reformat_source_code_with_debug_out(compile_and_reformat_source_code)
    print('COMPILATION IS DONE.')
    print()
    print()
    print('PATCHING...')
    patch_upk_main()
    print('PATCHING IS DONE.')
    print()
    print('INSTALLATION...')
    install_files_to_steam_folder()
    print('INSTALLATION IS DONE.')
    print()
    print('________')
    print('COMPILED AND INSTALLED.')
    print('DONE.')


if __name__ == "__main__":
    main()
