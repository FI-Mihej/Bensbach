from ucb_tools_config import *
import hashlib
from help_tools import filtered_file_list_traversal, filtered_file_list, FilteringType, ResultCache, \
    solid_hex_string__to__bytes, bytes__to__hex_string, ResultExistence
import pickle
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

from contextlib import contextmanager


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


class FileCacheRegistry(ConfigManager):
    def __init__(self, immediate_save=True):
        default_content = {
            'db': {
                'db': ''
            },
        }
        self.global_config = GlobalConfig()
        self.dir_templates = DirTemplates()
        self.dir_templates.create_template_in_the_folder(self.global_config.get_full_dir_path(), 'global file cache')
        self.file_cache_dir_template = self.dir_templates.make_an_absolute_template(
                self.global_config.get_full_dir_path(), 'global file cache')
        self.file_cache_settings_dir = self.file_cache_dir_template['settings dir']
        self._db = ResultCache()
        super(FileCacheRegistry, self).__init__([], base_dir=self.file_cache_settings_dir,
                                                default_content=default_content,
                                                immediate_save=immediate_save)

    def get_db(self):
        if self._db:
            return copy.deepcopy(self._db.get())
        else:
            result = None
            raw_hex_db_string = self.get_property('db', 'db').strip()
            if len(raw_hex_db_string) > 0:
                raw_db_string = solid_hex_string__to__bytes(raw_hex_db_string)
                try:
                    result = pickle.loads(raw_db_string)
                except:
                    pass
            if result is None:
                result = FileCacheDB()
            self._db.set(result)
            return copy.deepcopy(result)

    def set_db(self, db):
        self._db()
        raw_db_string = pickle.dumps(db)
        raw_hex_db_string = bytes__to__hex_string(raw_db_string, '')
        self.set_property('db', 'db', raw_hex_db_string)


@contextmanager
def file_cache_db_open(file_cache):
    db = file_cache.get_db()
    db_holder = ResultExistence(False, db)
    try:
        yield db_holder
    except:
        raise
    finally:
        if db_holder:
            file_cache.set_db(db_holder.result)


class FileCacheDB:
    def __init__(self, db=None):
        db_template = {
            'unpacked upk hash by original upk hash': dict(),
            # 'deserialized upk hash by original upk hash': dict()
        }
        self.db = db or db_template
