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

from ucb_tools_config import *
from ucb_tools_files_cache_manager import *
try:
    import ucb_compiler_decompiler
except ImportError:
    import remote_ucb_compiler_decompiler as ucb_compiler_decompiler
from help_tools import filtered_file_list, FilteringType, clear_dir, get_file_hash, IsOK_ContextHolder, is_ok, \
    ResultType, CriteriaType, is_ok_reader, IsOK_BlockFailed
from upk_helping_tools.upk_utils_api import *


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


class UcbToolsKernel:
    def __init__(self, projects_dir_full_path):
        self.global_config = GlobalConfig()
        self.dir_templates = DirTemplates()
        self.file_cache_registry = FileCacheRegistry()

        self.dir_templates.create_template_in_the_folder(projects_dir_full_path, 'project template')
        self.project_dir_template = self.dir_templates.make_an_absolute_template(
                projects_dir_full_path, 'project template')
        self.project_settings_dir = self.project_dir_template['settings']

        self.projects_local_config = ProjectsLocalConfig(self.project_settings_dir)

    def unpack_original_upk_files(self):
        func_context = IsOK_ContextHolder(
                'UCB Tools Kernel - unpack_original_upk_files()',
                None,
                ResultType(CriteriaType.any, set()))

        with file_cache_db_open(self.file_cache_registry) as db_holder:
            db = db_holder.result
            original_upk_dir_path, original_upk_dir_names, original_upk_file_names = filtered_file_list(
                    self.project_dir_template['upk original dir'], FilteringType.off)

            for original_upk_file in original_upk_file_names:
                with is_ok(func_context, 'another file loop run for "{}" file'.format(original_upk_file)):
                    original_upk_full_file_name = os.path.join(original_upk_dir_path, original_upk_file)
                    original_upk_file_hash = get_file_hash(original_upk_full_file_name)

                    context = IsOK_ContextHolder('Inside a loop',
                                                 original_upk_full_file_name,
                                                 ResultType(CriteriaType.needed, {'result check'}),
                                                 False, True)

                    with is_ok(context, 'original is already in db', ResultType(CriteriaType.any, set())):
                        if context:
                            unpacked_upk_file_hash = db['unpacked upk hash by original upk hash'].get(
                                    original_upk_file_hash)
                            context.push_result(unpacked_upk_file_hash is not None, unpacked_upk_file_hash)

                    with is_ok(context, 'unpack', ResultType(CriteriaType.forbidden, {'original is already in db'})):
                        if context:
                            clear_dir(self.file_cache_registry.file_cache_dir_template['temp dir'])

                            unpack_single_upk_file(
                                    self.global_config.get_property('global', 'upk utils dir'),
                                    original_upk_full_file_name,
                                    self.file_cache_registry.file_cache_dir_template['temp dir'])

                            unpacked_upk_full_file_name_in_temp = os.path.join(
                                    self.file_cache_registry.file_cache_dir_template['temp dir'], original_upk_file)
                            if not os.path.isfile(unpacked_upk_full_file_name_in_temp):
                                raise IsOK_BlockFailed('File Was not unpacked')

                            unpacked_upk_in_temp_hash = get_file_hash(unpacked_upk_full_file_name_in_temp)

                            unpacked_upk_full_file_name = os.path.join(
                                    self.file_cache_registry.file_cache_dir_template['upk unpacked dir'],
                                    unpacked_upk_in_temp_hash,
                                    original_upk_file)
                            shutil.copyfile(unpacked_upk_full_file_name_in_temp, unpacked_upk_full_file_name)

                            db['unpacked upk hash by original upk hash'][original_upk_file_hash] = \
                                unpacked_upk_in_temp_hash

                            context.push_result(True, unpacked_upk_in_temp_hash)

                    with is_ok(context, 'deserialize', ResultType(CriteriaType.needed, {'unpack'})):
                        if context:
                            clear_dir(self.file_cache_registry.file_cache_dir_template['temp dir'])

                            unpacked_upk_in_temp_hash = context.read_block_result_copy('unpack').result
                            unpacked_upk_full_file_name = os.path.join(
                                    self.file_cache_registry.file_cache_dir_template['upk unpacked dir'],
                                    unpacked_upk_in_temp_hash,
                                    original_upk_file)
                            deserialized_upk_full_dir_path = os.path.join(
                                    self.file_cache_registry.file_cache_dir_template['upk deserialized dir'],
                                    unpacked_upk_in_temp_hash)

                            deserialize_result = deserialize_single_upk_file(
                                    self.global_config.get_property('global', 'upk utils dir'),
                                    unpacked_upk_full_file_name,
                                    deserialized_upk_full_dir_path)

                            context.push_result(deserialize_result == 0, deserialize_result)

                    with is_ok(context, 'copy upk to the project dir', ResultType(CriteriaType.any, set())):
                        if context:
                            if context.read_block_result_link('original is already in db').existence or \
                                    context.read_block_result_link('deserialize').existence:
                                unpacked_upk_hash = None

                                if context.read_block_result_link('original is already in db').existence:
                                    unpacked_upk_hash = \
                                        context.read_block_result_copy('original is already in db').result
                                elif context.read_block_result_link('unpack').existence:
                                    unpacked_upk_hash = context.read_block_result_copy('unpack').result

                                if unpacked_upk_hash is not None:  # to improve reliability at the future
                                    # process of modification
                                    unpacked_upk_full_file_name = os.path.join(
                                            self.file_cache_registry.file_cache_dir_template['upk unpacked dir'],
                                            unpacked_upk_hash,
                                            original_upk_file)
                                    unpacked_upk_full_file_name_in_a_project = os.path.join(
                                            self.project_dir_template['upk unpacked dir'],
                                            original_upk_file)

                                    need_to_copy = True
                                    if os.path.isfile(unpacked_upk_full_file_name_in_a_project):
                                        unpacked_upk_in_project_hash = \
                                            get_file_hash(unpacked_upk_full_file_name_in_a_project)
                                        if unpacked_upk_hash == unpacked_upk_in_project_hash:
                                            need_to_copy = False
                                    if need_to_copy:
                                        shutil.copyfile(unpacked_upk_full_file_name,
                                                        unpacked_upk_full_file_name_in_a_project)

                                    context.push_result(True)

                    with is_ok(context, 'result check',
                               ResultType(CriteriaType.needed, {'copy upk to the project dir'})):
                        if context:
                            context.push_result(True)

                    with is_ok_reader(context):
                        if not context:
                            context.raise_bad_blocks()

                    func_context.push_result(True)

            db_holder.result = db
            db_holder.existence = True

        with is_ok_reader(func_context, ResultType(CriteriaType.optional, set())):
            if not func_context:
                func_context.raise_bad_blocks()

    def decompile_object(self, object_full_path):
        self.unpack_original_upk_files()
        pass

    def compile_project(self):
        self.unpack_original_upk_files()
        pass

    def install_project(self):
        func_context = IsOK_ContextHolder('UCB Tools Kernel - install_project()')

        with is_ok(func_context, 'main'):
            if func_context:
                patched_upk_dir_path, patched_upk_dir_names, patched_upk_file_names = filtered_file_list(
                        self.project_dir_template['upk patched dir'], FilteringType.off)

                install_folder_full_path = self.projects_local_config.get_property('local', 'install to dir')

                for patched_upk_file in patched_upk_file_names:
                    patched_upk_file_full_name = os.path.join(patched_upk_dir_path, patched_upk_file)
                    endpoint_patched_upk_file_full_name = os.path.join(install_folder_full_path, patched_upk_file)
                    shutil.copyfile(patched_upk_file_full_name, endpoint_patched_upk_file_full_name)

        with is_ok_reader(func_context):
            if not func_context:
                func_context.raise_bad_blocks()

    @staticmethod
    def clear_global_settings_dir():
        global_config = GlobalConfig()
        global_settings_dir_full_path = global_config.get_full_dir_path()
        clear_dir(global_settings_dir_full_path)
