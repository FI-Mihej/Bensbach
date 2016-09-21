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

from file_settings_manager.config_manager import *
from file_settings_manager.dir_templates import *

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


def get_property_as_relative_dir(manager, file, property_name, root):
    property_data = manager.get_property(file, property_name)
    property_data = property_data.split('/')
    result = os.path.join(root, *property_data)
    return result


class DirTemplates(DirTemplatesManager):
    def __init__(self):
        templates = {
            'global logs': {
                'log dir': 'Logs'
            },
            'global file cache': {
                'settings dir': 'Cache/Settings',
                'upk original dir': 'Cache/UPK Original',
                'upk unpacked dir': 'Cache/UPK Unpacked',
                'upk deserialized dir': 'Cache/UPK Deserialized',
                'temp dir': 'Cache/Temp'
            },
            'installation tool': {
                'installation temp dir': 'Install/TempProject'
            },
            'project template': {
                'settings': 'Sys/Settings',
                'upk original dir': 'Sys/UPK/Original',
                'upk unpacked dir': 'Sys/UPK/Unpacked',
                'upk patched dir': 'Sys/UPK/Patched',
                'work source dir': 'Source Work',
                'exported hex code': 'Sys/Sub/Exported HEX',
                'decompiled to UCB ': 'Decompiled to UCB',
                'compiled hex code': 'Sys/Sub/Compiled HEX',
                'compiled to UPK Utils\' code': 'Sys/Sub/Compiled to UPK Utils\' HEX mod',
                'exported to pseudo-code mod for UPK Utils': 'Exported to pseudo-code mod for UPK Utils'
            },
        }
        super(DirTemplates, self).__init__(templates)


class GlobalConfig(ConfigManager):
    def __init__(self, immediate_save=True):
        default_content = {
            'global': {
                'upk utils dir': '',
            },
            'installation tool': {
                'last install to dir': ''
            },
        }
        super(GlobalConfig, self).__init__(['UCB Tool Set'],
                                           default_content=default_content,
                                           immediate_save=immediate_save)


class ProjectsLocalConfig(ConfigManager):
    def __init__(self, project_settings_dir, immediate_save=True):
        default_content = {
            'local': {
                'install to dir': ''
            },
        }
        super(ProjectsLocalConfig, self).__init__([], base_dir=project_settings_dir,
                                                  default_content=default_content,
                                                  immediate_save=immediate_save)
