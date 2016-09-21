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

import cProfile
import argparse
import os.path
import shutil, errno
import subprocess
import time
import copy
import binascii
import time
import json
import sys
from enum import Enum
import IDGenerator
import struct
from help_tools import IsOK_ContextHolder, is_ok, is_ok_reader, ResultType, CriteriaType, IsOK_BlockFailed, \
    PLATFORM_NAME, hex_string__to__bytes, solid_hex_string__to__bytes, bytes__to__hex_string, float_to_bytes, \
    bytes_to_float, bytes_to_int, int_to_bytes, bytes_to_short, short_to_bytes, byte_to_bytes, bytes_to_byte, \
    IsOK_IntenalResultType, IsOK_IntenalResult, IsOK_HistoryExport
from upk_helping_tools.upk_constants import FileExtensions


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


class DebugPrintType(Enum):
    console_print = 1
    string = 2
    file = 3


class DebugPrinter:
    def __init__(self, parent=None, need_to_print_out_debug_info=None, spacing_string=None, print_type=None, file=None):
        '''
        :param parent: DebugPrinter() or None
        :param need_to_print_out_debug_info: bool()
        :param spacing_string: '', ' ', '\t', ...
        :return:
        '''
        if parent is None:
            self._need_to_print_out_debug_info = need_to_print_out_debug_info or bool(False)
            self._spacing_string = spacing_string or str()
            self._print_type = print_type or DebugPrintType.console_print
            self._file = file
        else:
            self._need_to_print_out_debug_info = need_to_print_out_debug_info or parent._need_to_print_out_debug_info
            self._spacing_string = spacing_string or parent.spacing_string
            self._print_type = print_type or parent._print_type
            self._file = file or parent._file

        self.string_buffer = list()

    @property
    def spacing_string(self):
        return self._spacing_string

    @spacing_string.setter
    def spacing_string(self, spacing_string):
        self._spacing_string = spacing_string

    def __call__(self, data_string=None, force=False):
        '''
        :param data_string: str()
        :return:
        '''
        if self._need_to_print_out_debug_info or force:
            data_string = data_string or str()
            debug_string = self._spacing_string + data_string
            self.string_buffer.append(debug_string)

            if DebugPrintType.string == self._print_type:
                pass
            elif DebugPrintType.console_print == self._print_type:
                print(debug_string)
            elif DebugPrintType.file == self._print_type:
                self._file.write(debug_string + '\r\n')
            else:
                raise RuntimeError('Unknown DebugPrintType')

    @property
    def is_print(self):
        return self._need_to_print_out_debug_info

    @property
    def full_string_log(self):
        return '\r\n'.join(self.string_buffer)


class TokenType:
    def __init__(self, token_type_data):
        self._token_type_data = token_type_data
        self.id = self._token_type_data[0]
        self.name = self._token_type_data[1]
        self.type = self._token_type_data[2]
        self.size_type = self._token_type_data[3]
        self.mem_size_type = self._token_type_data[4]

    def __getitem__(self, key):
        return self._token_type_data[key]

    def __str__(self):
        return str(self._token_type_data)


# -1: unlimited
# -2: unknown
# -3: null terminated string
class TokenTypes:
    def __init__(self):
        self.TOKENTYPE_TYPE__JUST_SIZE = 0
        self.TOKENTYPE_TYPE__HAS_TYPE = 1
        self.TOKENTYPE_TYPE__TOKENS_LIST_WITH_TYPES = 2

        self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT = -1
        self.TOKENTYPE_SIZE_TYPE__NULLTERMINATED = -2
        # self.TOKENTYPE_SIZE_TYPE__UNKNOWN = -3

        self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE = -1

        self.ObjRef = 1
        self.ObjRef_class = 2
        self.ObjRef_member = 3
        self.ObjRef_struct = 4
        self.Expr = 5
        self.Expr_left = 6
        self.Expr_right = 7
        self.Expr_index = 8
        self.Expr_array = 9
        self.Expr_count = 10
        self.Expr_cond = 11
        self.Expr_ifTrue = 12
        self.Expr_ifFalse = 13
        self.Expr_name = 14
        self.Expr_value = 15
        self.Expr_item = 16
        self.Expr_val = 17
        self.Byte = 18
        self.MemOff = 19
        self.Short = 20
        self.Labels = 21
        self.MemSize = 22
        self.RetValRef = 23
        self.NameRef = 24
        self.Int32 = 25
        self.Float32 = 26
        self.NullTerminatedString = 27
        self.CastToken = 28
        self.Params = 29
        self.DelegateProperty = 30

        self.raw_types = [
            (1, 'ObjRef', self.TOKENTYPE_TYPE__JUST_SIZE, 4, 8),
            (2, 'ObjRef_class', self.TOKENTYPE_TYPE__JUST_SIZE, 4, 8),
            (3, 'ObjRef_member', self.TOKENTYPE_TYPE__JUST_SIZE, 4, 8),
            (4, 'ObjRef_struct', self.TOKENTYPE_TYPE__JUST_SIZE, 4, 8),
            (5, 'Expr', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (6, 'Expr_left', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (7, 'Expr_right', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (8, 'Expr_index', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (9, 'Expr_array', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (10, 'Expr_count', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (11, 'Expr_cond', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (12, 'Expr_ifTrue', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),  # !Need testing
            (13, 'Expr_ifFalse', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),  # !Need testing
            (14, 'Expr_name', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (15, 'Expr_value', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (16, 'Expr_item', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (17, 'Expr_val', self.TOKENTYPE_TYPE__HAS_TYPE, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (18, 'Byte', self.TOKENTYPE_TYPE__JUST_SIZE, 1, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (19, 'MemOff', self.TOKENTYPE_TYPE__JUST_SIZE, 2, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (20, 'Short', self.TOKENTYPE_TYPE__JUST_SIZE, 2, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (21, 'Labels', None, None, None),
            # # (22, 'MemSize', None, None),
            (22, 'MemSize', self.TOKENTYPE_TYPE__JUST_SIZE, 2, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (23, 'RetValRef', self.TOKENTYPE_TYPE__JUST_SIZE, 4, 8),
            # # (24, 'NameRef', None, None),
            (24, 'NameRef', self.TOKENTYPE_TYPE__JUST_SIZE, 8, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (25, 'Int32', self.TOKENTYPE_TYPE__JUST_SIZE, 4, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (26, 'Float32', self.TOKENTYPE_TYPE__JUST_SIZE, 4, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (27, 'NullTerminatedString', self.TOKENTYPE_TYPE__JUST_SIZE, self.TOKENTYPE_SIZE_TYPE__NULLTERMINATED, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (28, 'CastToken', self.TOKENTYPE_TYPE__JUST_SIZE, 1, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (29, 'Params', self.TOKENTYPE_TYPE__TOKENS_LIST_WITH_TYPES, self.TOKENTYPE_SIZE_TYPE__TYPEDEPENDENT, self.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE),
            (30, 'DelegateProperty', None, None, None)
        ]

        self.types = list()
        for raw_type in self.raw_types:
            self.types.append(TokenType(raw_type))

        self.type_info_by_name = dict()
        for type_info in self.types:
            self.type_info_by_name[type_info.name] = type_info

        self.type_info_by_number = dict()
        for type_info in self.types:
            self.type_info_by_number[type_info.id] = type_info

        self.real_type_name_by_name = dict()
        for type_info in self.types:
            if '_' in type_info.name:
                split_name = type_info.name.split('_')
                self.real_type_name_by_name[type_info.name] = split_name[0]
            else:
                self.real_type_name_by_name[type_info.name] = type_info.name
    
TOKEN_TYPES = TokenTypes()


class Token:
    def __init__(self, token_data):
        self._token_data = token_data
        self.code = self._token_data[0]
        self.name = self._token_data[1]
        self.params = self._token_data[2]
        self.termination = self._token_data[3]

    def __getitem__(self, key):
        return self._token_data[key]

    def __str__(self):
        return str(self._token_data)


class Tokens:
    def __init__(self, tokens=list(), prefix=None, ending_postfix=None):
        self.prefix = prefix
        self.ending_postfix = ending_postfix

        self.tokens = list()
        for token in tokens:
            token_info = list(token)
            if prefix is not None:
                token_info[0] = prefix + token_info[0]
            if (ending_postfix is not None) and (token_info[-1] is None):
                token_info[-1] = ending_postfix
            token_info = tuple(token_info)
            new_token = Token(token_info)
            self.tokens.append(new_token)

        self.token_by_name = dict()
        for token in self.tokens:
            self.token_by_name[token[1]] = token

        self.token_by_code = dict()
        for token in self.tokens:
            self.token_by_code[token[0]] = token

US_CODE_TABLE__NORMAL = Tokens([
    (b'\x00', 'LocalVariable', [TOKEN_TYPES.ObjRef], None),
    (b'\x01', 'InstanceVariable', [TOKEN_TYPES.ObjRef], None),
    (b'\x02', 'DefaultVariable', [TOKEN_TYPES.ObjRef], None),
    (b'\x03', 'StateVariable', [TOKEN_TYPES.ObjRef], None),
    (b'\x04', 'Return', [TOKEN_TYPES.Expr], None),
    (b'\x05', 'Switch', [TOKEN_TYPES.ObjRef, TOKEN_TYPES.Byte, TOKEN_TYPES.Expr], None),
    (b'\x06', 'Jump', [TOKEN_TYPES.MemOff], None),
    (b'\x07', 'JumpIfNot', [TOKEN_TYPES.MemOff, TOKEN_TYPES.Expr], None),
    (b'\x08', 'Stop', [], None),
    (b'\x09', 'Assert', [TOKEN_TYPES.Short, TOKEN_TYPES.Byte, TOKEN_TYPES.Expr], None),
    (b'\x0A', 'Case', [TOKEN_TYPES.MemOff, TOKEN_TYPES.Expr], None),
    (b'\x0B', 'Nothing', [], None),
    (b'\x0C', 'LabelTable', [TOKEN_TYPES.Labels], None),
    (b'\x0D', 'GotoLabel', [TOKEN_TYPES.Expr], None),
    (b'\x0E', 'EatString', [TOKEN_TYPES.ObjRef, TOKEN_TYPES.Expr], None),
    (b'\x0F', 'Let', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.Expr_right], None),
    (b'\x10', 'DynArrayElement', [TOKEN_TYPES.Expr_index, TOKEN_TYPES.Expr_array], None),
    (b'\x11', 'New', [TOKEN_TYPES.Expr, TOKEN_TYPES.Expr, TOKEN_TYPES.Expr, TOKEN_TYPES.Expr, TOKEN_TYPES.Expr], None),
    (b'\x12', 'ClassContext', [TOKEN_TYPES.Expr, TOKEN_TYPES.MemSize, TOKEN_TYPES.RetValRef, TOKEN_TYPES.Byte, TOKEN_TYPES.Expr], None),
    (b'\x13', 'MetaCast', [TOKEN_TYPES.ObjRef_class, TOKEN_TYPES.Expr], None),
    (b'\x14', 'LetBool', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.Expr_right], None),
    (b'\x15', 'EndParmValue', [], None),
    # (b'\x16', 'EndFunctionParms', [], None),
    (b'\x16', 'EndFP', [], None),
    (b'\x17', 'Self', [], None),
    (b'\x18', 'Skip', [TOKEN_TYPES.MemSize], None),
    (b'\x19', 'Context', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.MemSize, TOKEN_TYPES.RetValRef, TOKEN_TYPES.Byte, TOKEN_TYPES.Expr_right], None),
    (b'\x1A', 'ArrayElement', [TOKEN_TYPES.Expr_index, TOKEN_TYPES.Expr_array], None),
    (b'\x1B', 'VirtualFunction', [TOKEN_TYPES.NameRef, TOKEN_TYPES.Params], b'\x16'),
    (b'\x1C', 'FinalFunction', [TOKEN_TYPES.ObjRef, TOKEN_TYPES.Params], b'\x16'),
    (b'\x1D', 'IntConst', [TOKEN_TYPES.Int32], None),
    (b'\x1E', 'FloatConst', [TOKEN_TYPES.Float32], None),
    (b'\x1F', 'StringConst', [TOKEN_TYPES.NullTerminatedString], None),
    (b'\x20', 'ObjectConst', [TOKEN_TYPES.ObjRef], None),
    (b'\x21', 'NameConst', [TOKEN_TYPES.NameRef], None),
    (b'\x22', 'RotatorConst', [TOKEN_TYPES.Int32, TOKEN_TYPES.Int32, TOKEN_TYPES.Int32], None),
    (b'\x23', 'VectorConst', [TOKEN_TYPES.Float32, TOKEN_TYPES.Float32, TOKEN_TYPES.Float32], None),
    (b'\x24', 'ByteConst', [TOKEN_TYPES.Byte], None),
    (b'\x25', 'IntZero', [], None),
    (b'\x26', 'IntOne', [], None),
    (b'\x27', 'TRUE', [], None),
    (b'\x28', 'FALSE', [], None),
    (b'\x29', 'NativeParm', [], None),
    (b'\x2A', 'NoObject', [], None),
    (b'\x2B', 'Unknown_Deprecated', [], None),
    (b'\x2C', 'IntConstByte', [TOKEN_TYPES.Byte], None),
    (b'\x2D', 'BoolVariable', [TOKEN_TYPES.Expr], None),
    (b'\x2E', 'DynamicCast', [TOKEN_TYPES.ObjRef_class, TOKEN_TYPES.Expr], None),
    (b'\x2F', 'Iterator', [TOKEN_TYPES.Expr, TOKEN_TYPES.MemOff], None),
    (b'\x30', 'IteratorPop', [], None),
    (b'\x31', 'IteratorNext', [], None),
    (b'\x32', 'StructCmpEq', [TOKEN_TYPES.Expr, TOKEN_TYPES.Expr], None),
    (b'\x33', 'StructCmpNe', [TOKEN_TYPES.Expr, TOKEN_TYPES.Expr], None),
    (b'\x34', 'UniStringConst', [TOKEN_TYPES.NullTerminatedString], None),
    (b'\x35', 'StructMember', [TOKEN_TYPES.ObjRef_member, TOKEN_TYPES.ObjRef_struct, TOKEN_TYPES.Byte, TOKEN_TYPES.Byte, TOKEN_TYPES.Expr], None),
    (b'\x36', 'DynArrayLen', [TOKEN_TYPES.Expr], None),
    (b'\x37', 'GlobalFunction', [TOKEN_TYPES.Expr], None),
    (b'\x38', 'PrimitiveCast', [TOKEN_TYPES.CastToken, TOKEN_TYPES.Expr], None),
    (b'\x39', 'DynArrayInsert', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.Expr_index, TOKEN_TYPES.Expr_count], b'\x16'),
    (b'\x3A', 'ReturnNothing', [TOKEN_TYPES.RetValRef], None),
    (b'\x3B', 'DelegateCmpEq', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.Expr_right], b'\x16'),
    (b'\x3C', 'DelegateCmpNe', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.Expr_right], b'\x16'),
    (b'\x3D', 'DelegateFunctionCmpEq', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.Expr_right], b'\x16'),
    (b'\x3E', 'DelegateFunctionCmpNE', [TOKEN_TYPES.Expr_left, TOKEN_TYPES.Expr_right], b'\x16'),
    (b'\x3F', 'NoDelegate', [], None),
    (b'\x40', 'DynArrayRemove', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.Expr_index, TOKEN_TYPES.Expr_count], b'\x16'),
    (b'\x41', 'DebugInfo', [TOKEN_TYPES.Int32, TOKEN_TYPES.Int32, TOKEN_TYPES.Int32, TOKEN_TYPES.Byte], None),
    (b'\x42', 'DelegateFunction', [TOKEN_TYPES.Byte, TOKEN_TYPES.ObjRef, TOKEN_TYPES.NameRef, TOKEN_TYPES.Params], b'\x16'),
    (b'\x43', 'DelegateProperty', [TOKEN_TYPES.NameRef, TOKEN_TYPES.ObjRef], None),
    (b'\x44', 'LetDelegate', [], None),
    (b'\x45', 'TernaryCondition', [TOKEN_TYPES.Expr_cond, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_ifTrue, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_ifFalse], None),
    (b'\x46', 'DynArrFind', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_value], b'\x16'),
    (b'\x47', 'DynArrayFindStruct', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_value, TOKEN_TYPES.Expr_value], b'\x16'),
    (b'\x48', 'OutVariable', [], None),
    (b'\x49', 'DefaultParmValue', [TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_value], b'\x15'),
    (b'\x4A', 'NoParm', [], None),
    (b'\x4B', 'InstanceDelegate', [TOKEN_TYPES.NameRef], None),
    (b'\x4C', 'DynamicVariable', [], None),
    (b'\x4D', 'DynamicVariable', [], None),
    (b'\x4E', 'DynamicVariable', [], None),
    (b'\x4F', 'DynamicVariable', [], None),
    (b'\x50', 'DynamicVariable', [], None),
    (b'\x51', 'InterfaceContext', [TOKEN_TYPES.Expr], None),
    (b'\x52', 'InterfaceCast', [TOKEN_TYPES.ObjRef_class, TOKEN_TYPES.Expr], None),
    (b'\x53', 'EndOfScript', [], None),
    (b'\x54', 'DynArrAdd', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.Expr_count], None),
    (b'\x55', 'DynArrAddItem', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_item], b'\x16'),
    (b'\x56', 'DynArrRemoveItem', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_item], b'\x16'),
    (b'\x57', 'DynArrInsertItem', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.MemSize, TOKEN_TYPES.Expr_index, TOKEN_TYPES.Expr_item], b'\x16'),
    (b'\x58', 'DynArrIterator', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.Expr_val, TOKEN_TYPES.Byte, TOKEN_TYPES.Expr_index, TOKEN_TYPES.MemOff], None),
    (b'\x59', 'DynArrSort', [TOKEN_TYPES.Expr_array, TOKEN_TYPES.MemSize, TOKEN_TYPES.DelegateProperty], b'\x16'),
    (b'\x5A', 'FilterEditorOnly', [], None),
    (b'\x5B', None, [], None),
    (b'\x5C', None, [], None),
    (b'\x5D', None, [], None),
    (b'\x5E', None, [], None),
    (b'\x5F', None, [], None),
])

US_CODE_TABLE__NORMAL_CONTINUED = Tokens([
    (b'\x70', 'Concat_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x71', 'GotoState', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x72', 'EqualEqual_ObjectObject', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x73', 'Less_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x74', 'Greater_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x75', 'Enable', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x76', 'Disable', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x77', 'NotEqual_ObjectObject', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x78', 'LessEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x79', 'GreaterEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x7A', 'EqualEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x7B', 'NotEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x7C', 'ComplementEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x7D', 'StringLen', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x7E', 'InStr', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x7F', 'Mid', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x80', 'Left', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x81', 'Not_PreBool', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x82', 'AndAnd_BoolBool', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x83', 'XorXor_BoolBool', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x84', 'OrOr_BoolBool', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x85', 'MultiplyEqual_ByteByte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x86', 'DivideEqual_ByteByte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x87', 'AddEqual_ByteByte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x88', 'SubtractEqual_ByteByte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x89', 'AddAdd_PreByte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x8A', 'SubtractSubtract_PreByte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x8B', 'AddAdd_Byte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x8C', 'SubtractSubtract_Byte', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x8D', 'Complement_PreInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x8E', 'EqualEqual_RotatorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x8F', 'Subtract_PreInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x90', 'Multiply_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x91', 'Divide_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x92', 'Add_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x93', 'Subtract_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x94', 'LessLess_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x95', 'GreaterGreater_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x96', 'Less_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x97', 'Greater_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x98', 'LessEqual_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x99', 'GreaterEqual_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x9A', 'EqualEqual_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x9B', 'NotEqual_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x9C', 'And_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x9D', 'Xor_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x9E', 'Or_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x9F', 'MultiplyEqual_IntFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA0', 'DivideEqual_IntFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA1', 'AddEqual_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA2', 'SubtractEqual_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA3', 'AddAdd_PreInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA4', 'SubtractSubtract_PreInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA5', 'AddAdd_Int', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA6', 'SubtractSubtract_Int', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA7', 'Rand', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA8', 'At_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xA9', 'Subtract_PreFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xAA', 'MultiplyMultiply_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xAB', 'Multiply_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xAC', 'Divide_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xAD', 'Percent_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xAE', 'Add_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xAF', 'Subtract_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB0', 'Less_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB1', 'Greater_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB2', 'LessEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB3', 'GreaterEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB4', 'EqualEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB5', 'NotEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB6', 'MultiplyEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB7', 'DivideEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB8', 'AddEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xB9', 'SubtractEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xBA', 'Abs', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xBB', 'Sin', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xBC', 'Cos', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xBD', 'Tan', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xBE', 'Atan', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xBF', 'Exp', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC0', 'Loge', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC1', 'Sqrt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC2', 'Square', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC3', 'FRand', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC4', 'GreaterGreaterGreater_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC5', 'IsA', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC6', 'MultiplyEqual_ByteFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC7', 'Round', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xC9', 'Repl', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xCB', 'NotEqual_RotatorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD2', 'ComplementEqual_FloatFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD3', 'Subtract_PreVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD4', 'Multiply_VectorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD5', 'Multiply_FloatVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD6', 'Divide_VectorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD7', 'Add_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD8', 'Subtract_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD9', 'EqualEqual_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDA', 'NotEqual_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDB', 'Dot_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDC', 'Cross_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDD', 'MultiplyEqual_VectorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDE', 'DivideEqual_VectorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDF', 'AddEqual_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE0', 'SubtractEqual_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE1', 'VSize', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE2', 'Normal', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE4', 'VSizeSq', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE5', 'GetAxes', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE6', 'GetUnAxes', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE7', 'LogInternal', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xE8', 'WarnInternal', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xEA', 'Right', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xEB', 'Caps', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xEC', 'Chr', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xED', 'Asc', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xEE', 'Locs', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF2', 'EqualEqual_BoolBool', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF3', 'NotEqual_BoolBool', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF4', 'FMin', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF5', 'FMax', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF6', 'FClamp', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF7', 'Lerp', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF9', 'Min', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFA', 'Max', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFB', 'Clamp', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFC', 'VRand', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFD', 'Percent_IntInt', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFE', 'EqualEqual_NameName', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFF', 'NotEqual_NameName', [TOKEN_TYPES.Params], b'\x16')
])

US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_61 = Tokens([
    (b'\x00', 'Sleep', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x02', 'ClassIsChildOf', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x05', 'FinishAnim', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x06', 'SetCollision', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0A', 'Move', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0B', 'SetLocation', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0E', 'Add_QuatQuat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0F', 'Subtract_QuatQuat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x10', 'SetOwner', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x13', 'LessLess_VectorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x14', 'GreaterGreater_VectorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x15', 'Trace', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x17', 'Destroy', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x18', 'SetTimer', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x19', 'IsInState', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x1B', 'SetCollisionSize', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x1C', 'GetStateName', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x1F', 'Multiply_RotatorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x20', 'Multiply_FloatRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x21', 'Divide_RotatorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x22', 'MultiplyEqual_RotatorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x23', 'DivideEqual_RotatorFloat', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x28', 'Multiply_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x29', 'MultiplyEqual_VectorVector', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x2A', 'SetBase', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x2B', 'SetRotation', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x2C', 'MirrorVectorByNormal', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x30', 'AllActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x31', 'ChildActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x32', 'BasedActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x33', 'TouchingActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x35', 'TraceActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x37', 'VisibleActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x38', 'VisibleCollidingActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x39', 'DynamicActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x3C', 'Add_RotatorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x3D', 'Subtract_RotatorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x3E', 'AddEqual_RotatorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x3F', 'SubtractEqual_RotatorRotator', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x40', 'RotRand', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x41', 'CollidingActors', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x42', 'ConcatEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x43', 'AtEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x44', 'SubtractEqual_StringString', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF4', 'MoveTo', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xF6', 'MoveToward', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xFC', 'FinishRotation', [TOKEN_TYPES.Params], b'\x16')
], b'\x61')

US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_62 = Tokens([
    (b'\x00', 'MakeNoise', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x02', 'LineOfSightTo', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x05', 'FindPathToward', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x06', 'FindPathTo', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x08', 'ActorReachable', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x09', 'PointReachable', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0C', 'FindStairRotation', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0D', 'FindRandomDest', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0E', 'PickWallAdjust', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x0F', 'WaitForLanding', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x13', 'PickTarget', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x14', 'PlayerCanSeeMe', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x15', 'CanSee', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x18', 'SaveConfig', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x19', 'CanSeeByPoints', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x22', 'UpdateURL', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x23', 'GetURLMap', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x24', 'FastTrace', [TOKEN_TYPES.Params], b'\x16')
], b'\x62')

US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_65 = Tokens([
    (b'\xDC', 'ProjectOnTo', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDD', 'IsZero', [TOKEN_TYPES.Params], b'\x16')
], b'\x65')

US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_69 = Tokens([
    (b'\xCF', 'Subtract_PreVector2D', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD1', 'Multiply_FloatVector2D', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD5', 'EqualEqual_Vector2DVector2D', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xD6', 'NotEqual_Vector2DVector2D', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDD', 'V2DSize', [TOKEN_TYPES.Params], b'\x16'),
    (b'\xDE', 'V2DNormal', [TOKEN_TYPES.Params], b'\x16')
], b'\x69')

US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_6A = Tokens([
    (b'\x24', 'Multiply_Vector2DVector2D', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x25', 'MultiplyEqual_Vector2DVector2D', [TOKEN_TYPES.Params], b'\x16')
], b'\x6A')

US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_6F = Tokens([
    (b'\x81', 'MoveSmooth', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x82', 'SetPhysics', [TOKEN_TYPES.Params], b'\x16'),
    (b'\x83', 'AutonomousPhysics', [TOKEN_TYPES.Params], b'\x16')
], b'\x6F')

US_CODE_TABLE__PRIMITIVE_CAST_TOKENS_38 = Tokens([
    (b'\x36', 'InterfaceToBool', [TOKEN_TYPES.Expr], None),
    (b'\x37', 'InterfaceToString', [TOKEN_TYPES.Expr], None),
    (b'\x38', 'InterfaceToObject', [TOKEN_TYPES.Expr], None),
    (b'\x39', 'RotatorToVector', [TOKEN_TYPES.Expr], None),
    (b'\x3A', 'ByteToInt', [TOKEN_TYPES.Expr], None),
    (b'\x3B', 'ByteToBool', [TOKEN_TYPES.Expr], None),
    (b'\x3C', 'ByteToFloat', [TOKEN_TYPES.Expr], None),
    (b'\x3D', 'IntToByte', [TOKEN_TYPES.Expr], None),
    (b'\x3E', 'IntToBool', [TOKEN_TYPES.Expr], None),
    (b'\x3F', 'IntToFloat', [TOKEN_TYPES.Expr], None),
    (b'\x40', 'BoolToByte', [TOKEN_TYPES.Expr], None),
    (b'\x41', 'BoolToInt', [TOKEN_TYPES.Expr], None),
    (b'\x42', 'BoolToFloat', [TOKEN_TYPES.Expr], None),
    (b'\x43', 'FloatToByte', [TOKEN_TYPES.Expr], None),
    (b'\x44', 'FloatToInt', [TOKEN_TYPES.Expr], None),
    (b'\x45', 'FloatToBool', [TOKEN_TYPES.Expr], None),
    (b'\x46', 'ObjectToInterface', [TOKEN_TYPES.Expr], None),
    (b'\x47', 'ObjectToBool', [TOKEN_TYPES.Expr], None),
    (b'\x48', 'NameToBool', [TOKEN_TYPES.Expr], None),
    (b'\x49', 'StringToByte', [TOKEN_TYPES.Expr], None),
    (b'\x4A', 'StringToInt', [TOKEN_TYPES.Expr], None),
    (b'\x4B', 'StringToBool', [TOKEN_TYPES.Expr], None),
    (b'\x4C', 'StringToFloat', [TOKEN_TYPES.Expr], None),
    (b'\x4D', 'StringToVector', [TOKEN_TYPES.Expr], None),
    (b'\x4E', 'StringToRotator', [TOKEN_TYPES.Expr], None),
    (b'\x4F', 'VectorToBool', [TOKEN_TYPES.Expr], None),
    (b'\x50', 'VectorToRotator', [TOKEN_TYPES.Expr], None),
    (b'\x51', 'RotatorToBool', [TOKEN_TYPES.Expr], None),
    (b'\x52', 'ByteToString', [TOKEN_TYPES.Expr], None),
    (b'\x53', 'IntToString', [TOKEN_TYPES.Expr], None),
    (b'\x54', 'BoolToString', [TOKEN_TYPES.Expr], None),
    (b'\x55', 'FloatToString', [TOKEN_TYPES.Expr], None),
    (b'\x56', 'ObjectToString', [TOKEN_TYPES.Expr], None),
    (b'\x57', 'NameToString', [TOKEN_TYPES.Expr], None),
    (b'\x58', 'VectorToString', [TOKEN_TYPES.Expr], None),
    (b'\x59', 'RotatorToString', [TOKEN_TYPES.Expr], None),
    (b'\x5A', 'DelegateToString', [TOKEN_TYPES.Expr], None),
    (b'\x60', 'StringToName', [TOKEN_TYPES.Expr], None),
], b'\x38')

US_CODE_TABLES_LIST = [
    US_CODE_TABLE__NORMAL,
    US_CODE_TABLE__NORMAL_CONTINUED,
    US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_61,
    US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_62,
    US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_65,
    US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_69,
    US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_6A,
    US_CODE_TABLE__EXTENDED_NATIVE_FUNCTION_6F,
    US_CODE_TABLE__PRIMITIVE_CAST_TOKENS_38
]
_US_CODE_TABLE__ALL_TOKENS = list()
for code_table in US_CODE_TABLES_LIST:
    _US_CODE_TABLE__ALL_TOKENS += code_table.tokens

US_CODE_TABLE__ALL_TOKENS = Tokens(_US_CODE_TABLE__ALL_TOKENS)

DESCRIPTION_BEGIN_WORD = '/*DESCRIPTION_BEGIN*/'
DESCRIPTION_END_WORD = '/*DESCRIPTION_END*/'
LANGUAGE_VERSION_WORD = ['/*LANGUAGE_VERSION=', '*/']
LANGUAGE_VERSION = 0

# XCOMGAMEUPK__NAMES_TABLE__FILENAME = r"D:\Dev\Workspace\My\XCOM Modding\XComGame_NamesTable.json"
# XCOMGAMEUPK__NAMES_TABLE__NAME_BY_ID = dict()
# XCOMGAMEUPK__NAMES_TABLE__ID_BY_NAME = dict()
# XCOMGAMEUPK__NAMES_TABLE = dict()
# with open(XCOMGAMEUPK__NAMES_TABLE__FILENAME, 'r') as file:
#     XCOMGAMEUPK__NAMES_TABLE = json.load(file)
# for name_id, name in XCOMGAMEUPK__NAMES_TABLE.items():
#     if name_id != '__END__':
#         int_name_id = int(name_id)
#         XCOMGAMEUPK__NAMES_TABLE__NAME_BY_ID[int_name_id] = name
#         XCOMGAMEUPK__NAMES_TABLE__ID_BY_NAME[name] = int_name_id


if 'PyPy' == PLATFORM_NAME:
    def parce_nametables_line(line):
        line = line.split(': ')
        id_line_data = line[0]
        name = line[1]
        id_line_data = ''.join(id_line_data.split())
        id_line_data = id_line_data.split(')(')
        id_line_data = id_line_data[1][:-1]
        bin_id = binascii.unhexlify(id_line_data.encode())
        result = (bin_id, name)
        return result
else:
    def parce_nametables_line(line):
        line = line.split(': ')
        id_line_data = line[0]
        name = line[1]
        id_line_data = ''.join(id_line_data.split())
        id_line_data = id_line_data.split(')(')
        id_line_data = id_line_data[1][:-1]
        bin_id = binascii.unhexlify(id_line_data)
        result = (bin_id, name)
        return result


def get_names_table_and_import_table(file_name):
    data = None
    with open(file_name, 'r') as file:
        data = file.read()
    data = data.split('\n\n')

    header = list()
    name_table = list()
    import_table = list()
    export_table = list()

    for part in data:
        part_lines = part.split('\n')
        if part_lines[0] == 'NameTable:':
            name_table = part_lines[1:]
        elif part_lines[0] == 'ImportTable:':
            import_table = part_lines[1:]
        elif part_lines[0] == 'ExportTable:':
            export_table = part_lines[1:]
        else:
            header = part_lines

    tables = (name_table, import_table, export_table)
    result_tables = list()
    for table in tables:
        table_dict = dict()
        for line in table:
            try:
                result_line = parce_nametables_line(line)
            except IndexError:
                pass
            else:
                table_dict[result_line[0]] = result_line[1]
        result_tables.append(table_dict)

    # name_table, import_table, export_table = result_tables

    result = (header, result_tables)
    return result


UPK__INFO__FILENAME = r"C:\Development\XCOM Modding\Work\CookedPCConsole_Deserialized\XComGame.txt"

# UPK__NAMES_TABLE = dict()
# UPK__IMPORT_TABLE = dict()
# UPK__EXPORT_TABLE = dict()
UPK__NAMES_TABLE__NAME_BY_ID = dict()
UPK__IMPORT_TABLE__NAME_BY_ID = dict()
UPK__EXPORT_TABLE__NAME_BY_ID = dict()
UPK__NAMES_TABLE__ID_BY_NAME = dict()
UPK__IMPORT_TABLE__ID_BY_NAME = dict()
UPK__EXPORT_TABLE__ID_BY_NAME = dict()

UPK__NAMES__NAME_BY_ID = dict()
UPK__NAMES__ID_BY_NAME = dict()
UPK__NAMES = dict()

UPK_INFO_HEADER, UPK_TABLES = get_names_table_and_import_table(UPK__INFO__FILENAME)
UPK__NAMES_TABLE, UPK__IMPORT_TABLE, UPK__EXPORT_TABLE = UPK_TABLES
UPK__NAMES.update(UPK__EXPORT_TABLE)
UPK__NAMES.update(UPK__IMPORT_TABLE)
for bin_id, name in UPK__NAMES.items():
        UPK__NAMES__NAME_BY_ID[bin_id] = name
        UPK__NAMES__ID_BY_NAME[name] = bin_id
for bin_id, name in UPK__NAMES_TABLE.items():
        UPK__NAMES_TABLE__NAME_BY_ID[bin_id] = name
        UPK__NAMES_TABLE__ID_BY_NAME[name] = bin_id
for bin_id, name in UPK__IMPORT_TABLE.items():
        UPK__IMPORT_TABLE__NAME_BY_ID[bin_id] = name
        UPK__IMPORT_TABLE__ID_BY_NAME[name] = bin_id
for bin_id, name in UPK__EXPORT_TABLE.items():
        UPK__EXPORT_TABLE__NAME_BY_ID[bin_id] = name
        UPK__EXPORT_TABLE__ID_BY_NAME[name] = bin_id
print('UPK__NAMES qnt: {}'.format(len(UPK__NAMES)))
print('UPK__NAMES_TABLE qnt: {}'.format(len(UPK__NAMES_TABLE)))
print('UPK__IMPORT_TABLE qnt: {}'.format(len(UPK__IMPORT_TABLE)))
print('UPK__EXPORT_TABLE qnt: {}'.format(len(UPK__EXPORT_TABLE)))


SET_OF_DELIMITERS = {',', '(', ')'}


class PreprocessorTokens:
    to_label_token = 'to_label'
    label_token = 'label'

PREPROCESSOR_TOKENS = PreprocessorTokens()


# INPUT_FILE_NAME = r"C:\Development\XCOM Modding\XComGame.XGAbility_Targeted.CalcDamage.fbc"
INPUT_FILE_NAME = r"C:\Development\XCOM Modding\XComGame.XGAbility_Targeted.RollForHit.fbc"
OUTPUT_FILE_NAME = r"C:\Development\XCOM Modding\NewHitDamageCalc\out.ucb"
# INPUT_FILE_NAME = r"C:\Development\XCOM Modding\Work\temp\XComGame.XGAbility_Targeted.RollForHit.fbc"
# OUTPUT_FILE_NAME = r"C:\Development\XCOM Modding\Work\temp\XComGame.XGAbility_Targeted.RollForHit.ucb"


def find_label():
    pass


def decompile__add_label(labels_dict, label_mem_offset, labels_id_generator):
    '''
    :param labels_dict:
    :param label_mem_offset:
    :param labels_id_generator:
    :return:
    '''

    # labels_id_generator = IDGenerator.IDGenerator()
    # labels_dict = dict()
    label_id = None
    if label_mem_offset in labels_dict:
        # memory offset has already known label
        label_id = labels_dict[label_mem_offset]
    else:
        # need to register new label
        label_id = labels_id_generator.get_new_ID()
        # debug = True
        # if debug:
        #     # FOR DEBUG ONLY:
        #     label_id = struct.pack('<H', label_mem_offset)
        #     label_id = bytes__to__hex_string(label_id)
        labels_dict[label_mem_offset] = label_id
    return label_id


def decompile__replace_mem_offset_by_label_text(labels_dict, label_mem_offset, labels_id_generator):
    label_id = decompile__add_label(labels_dict, label_mem_offset, labels_id_generator)
    result = ''.join(['@', PREPROCESSOR_TOKENS.to_label_token, '(', str(label_id), ')'])
    return result


def decompile__get_label(labels_dict, label_mem_offset):
    result = labels_dict.get(label_mem_offset)
    return result


def decompile__get_current_label_text(labels_dict, label_mem_offset):
    label_id = decompile__get_label(labels_dict, label_mem_offset)
    label_text = None
    if label_id is not None:
        label_text = ''.join(['@', PREPROCESSOR_TOKENS.label_token, '(', str(label_id), ')'])
    return label_text


def compile__detect_and_init_new_label(working_token_list, labels_dict, current_token_mem_offset):
    current_token = working_token_list[0]
    if current_token.startswith('@'):
        if current_token[1:] == PREPROCESSOR_TOKENS.label_token:
            label_id = working_token_list[1]
            working_token_list = working_token_list[2:]
            labels_dict[label_id] = current_token_mem_offset

    return working_token_list


def compile__detect_known_label(current_token, working_token_list, labels_dict, first_pass=False):
    '''
    :param current_token:
    :param first_pass:
    :param working_token_list:
    :param labels_dict:
    :return: can be None (when label_id is not found)
    '''

    current_working_token = current_token

    try:
        if current_token.startswith('@'):
            if current_token[1:] == PREPROCESSOR_TOKENS.to_label_token:
                label_id = working_token_list[0]
                current_working_token = label_id
                label_mem_offset = labels_dict.get(label_id)
                if label_mem_offset is not None:
                    label_mem_offset = struct.pack('<H', int(label_mem_offset))
                working_token_list[0] = label_mem_offset
        else:
            # if jump to hex code, not to label
            param_bytecode = solid_hex_string__to__bytes(current_token)
            working_token_list.insert(0, param_bytecode)
    except binascii.Error as ex:
        raise UnresolvableNameReference('', current_working_token)

    return working_token_list


def compile__translate_known_label_to_mem_offset(current_token, working_token_list, labels_dict, first_pass=False):
    working_token_list = compile__detect_known_label(current_token, working_token_list, labels_dict, first_pass)
    if working_token_list[0] is None:
        working_token_list[0] = b'\x00\x00'
    return working_token_list


def debug_print(need_to_print_out=False, spacing_string=None, data_string=None):
    spacing_string = spacing_string or str()
    data_string = data_string or str()
    if need_to_print_out:
        print(spacing_string + data_string)


def decompile_token(input_data, labels_dict, labels_id_generator, spacing=None, d_print=None, memory_offset=None,
                    hex_offset=None):
    spacing = spacing or 0
    memory_offset = memory_offset or 0
    hex_offset = hex_offset or 0
    initial_memory_offset = copy.copy(memory_offset)
    d_print = d_print or DebugPrinter()
    spacing_string = ' ' * spacing
    current_token_spacing_string = '\r\n' + ' ' * spacing
    subspacing = spacing + 4
    subtokens_spacing_string = '\r\n' + ' ' * subspacing
    d_print._spacing_string = spacing_string

    if d_print.is_print: d_print('DECOMPILE DATA: {}'.format(bytes__to__hex_string(input_data)))
    unknown_text = '/*UnknownToken*/'
    params_delimiter = ', '
    number_of_found_tokens = 0
    result = (False, b'', b'', unknown_text, unknown_text, number_of_found_tokens, memory_offset, hex_offset)
    printable_result = (False, '', '', unknown_text, unknown_text,
                        number_of_found_tokens, memory_offset, hex_offset)

    working = copy.copy(input_data)
    current = b''
    token_found = False
    token_num = working[:2]
    if token_num in US_CODE_TABLE__ALL_TOKENS.token_by_code:
        token_found = True
    else:
        token_num = working[:1]
        if token_num in US_CODE_TABLE__ALL_TOKENS.token_by_code:
            token_found = True

    token_text = ''
    token_text_only = ''
    last_decompile_result = True
    if token_found:
        token_num_len = len(token_num)
        working = working[token_num_len:]
        hex_offset += token_num_len
        memory_offset += token_num_len
        current += token_num
        if d_print.is_print: d_print('TOKEN ID: {}; CURRENT: {}; WORKING: {}'.format(
            token_num,
            bytes__to__hex_string(current),
            bytes__to__hex_string(working)))

        token_info = US_CODE_TABLE__ALL_TOKENS.token_by_code[token_num]
        if d_print.is_print: d_print('TOKEN INFO: {}'.format(str(token_info)))
        token_name = token_info.name
        token_params = token_info.params
        token_termination = token_info.termination
        token_hex_representation = bytes__to__hex_string(token_info.code)
        if d_print.is_print: d_print('TOKEN PARAMS: {}'.format(token_params))
        if d_print.is_print: d_print('TOKEN TERMINATION: {}'.format(token_termination))
        
        token_params_text = ''
        token_params_text_only = ''
        for token_param_type in token_params:
            if d_print.is_print: d_print('<<token_param_type: {}'.format(token_param_type))
            token_param_type_info = TOKEN_TYPES.type_info_by_number[token_param_type]
            if d_print.is_print: d_print('<<token_param_type_info: {}'.format(str(token_param_type_info)))
            token_param_type_type = token_param_type_info.type
            token_param_type_type_name = token_param_type_info.name
            token_param_type_size = token_param_type_info.size_type
            token_param_type_mem_size = token_param_type_info.mem_size_type
            if token_param_type_type is not None:
                if TOKEN_TYPES.TOKENTYPE_TYPE__HAS_TYPE == token_param_type_type:
                    decompile_result = decompile_token(working, labels_dict, labels_id_generator, subspacing, d_print, memory_offset,
                                                       hex_offset)
                    last_decompile_result = decompile_result[0]
                    current += decompile_result[1]
                    working = decompile_result[2]
                    token_params_text += subtokens_spacing_string + decompile_result[3] + params_delimiter
                    token_params_text_only += subtokens_spacing_string + decompile_result[4] + params_delimiter
                    number_of_found_tokens += decompile_result[5]
                    memory_offset = decompile_result[6]
                    hex_offset = decompile_result[7]
                elif TOKEN_TYPES.TOKENTYPE_TYPE__JUST_SIZE == token_param_type_type:
                    last_decompile_result = True
                    if TOKEN_TYPES.TOKENTYPE_SIZE_TYPE__NULLTERMINATED == token_param_type_size:
                        zero_offset = working.find(b'\x00')
                        if zero_offset == -1:
                            last_decompile_result = False
                            token_param_type_size = 0
                        else:
                            token_param_type_size = zero_offset + 1
                    if last_decompile_result:
                        param_data = working[:token_param_type_size]
                        hex_offset += token_param_type_size
                        if token_param_type_mem_size == TOKEN_TYPES.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE:
                            memory_offset += token_param_type_size
                        else:
                            memory_offset += token_param_type_mem_size
                        current += param_data
                        working = working[token_param_type_size:]
                        param_data_hex_string = bytes__to__hex_string(param_data)
                        if token_param_type_type_name in {'NameRef'}:
                            sub_bin_id = param_data[:4]
                            if sub_bin_id in UPK__NAMES_TABLE__NAME_BY_ID:
                                param_data_hex_string = UPK__NAMES_TABLE__NAME_BY_ID[sub_bin_id]
                                if ' ' in param_data_hex_string:
                                    param_data_hex_string = decompile_put_text_into_brackets(param_data_hex_string)
                        elif token_param_type_type_name in {'ObjRef', 'ObjRef_class', 'ObjRef_member', 'ObjRef_struct',
                                                            'RetValRef'}:
                            if param_data in UPK__NAMES__NAME_BY_ID:
                                param_data_hex_string = UPK__NAMES__NAME_BY_ID[param_data]
                                if ' ' in param_data_hex_string:
                                    param_data_hex_string = decompile_put_text_into_brackets(param_data_hex_string)
                        elif token_param_type_type_name in {'NullTerminatedString'}:
                            try:
                                string_data = param_data[:-1].decode()  # may raise
                                string_data = decompile_put_text_into_brackets(string_data)
                                param_data_hex_string = string_data
                            except UnicodeError:
                                pass  # param_data_hex_string is unchanged
                        elif token_param_type_type_name in {'Byte'}:
                            param_data_hex_string = ''.join(['"', str(bytes_to_byte(param_data)), '"'])
                        elif token_param_type_type_name in {'Short'}:
                            param_data_hex_string = ''.join(['"', str(bytes_to_short(param_data)), '"'])
                        elif token_param_type_type_name in {'Int32'}:
                            param_data_hex_string = ''.join(['"', str(bytes_to_int(param_data)), '"'])
                        elif token_param_type_type_name in {'Float32'}:
                            param_data_hex_string = ''.join(['"', str(bytes_to_float(param_data)), '"'])
                        elif token_param_type_type_name in {'MemOff'}:
                            param_data_hex_string = decompile__replace_mem_offset_by_label_text(
                                    labels_dict, struct.unpack('<H', param_data)[0], labels_id_generator)
                        token_params_text += subtokens_spacing_string + '{{{}}}({})'.format(token_param_type_type_name, param_data_hex_string) + params_delimiter
                        token_params_text_only += subtokens_spacing_string + '({})'.format(param_data_hex_string) + params_delimiter
                        number_of_found_tokens += 1
                elif TOKEN_TYPES.TOKENTYPE_TYPE__TOKENS_LIST_WITH_TYPES == token_param_type_type:
                    continue_processing = True
                    while continue_processing:
                        if working.startswith(token_termination):
                            continue_processing = False
                        decompile_result = decompile_token(working, labels_dict, labels_id_generator, subspacing, d_print, memory_offset,
                                                           hex_offset)
                        last_decompile_result = decompile_result[0]
                        current += decompile_result[1]
                        working = decompile_result[2]
                        token_params_text += subtokens_spacing_string + decompile_result[3] + params_delimiter
                        token_params_text_only += subtokens_spacing_string + decompile_result[4] + params_delimiter
                        number_of_found_tokens += decompile_result[5]
                        memory_offset = decompile_result[6]
                        hex_offset = decompile_result[7]
                        if not last_decompile_result:
                            break
                pass
            else:
                unknown_param_type_text = '/*UnknownParamType*/{{{}}}'.format(token_param_type_type_name)
                token_params_text += unknown_param_type_text + params_delimiter
                token_params_text_only += unknown_param_type_text + params_delimiter
                last_decompile_result = False
                d_print('UNKNOWN PARAM TYPE: "{}" from "[{}]{}"'.format(
                    token_param_type_type_name, 
                    token_hex_representation, 
                    token_name), 
                        True)
            if not last_decompile_result:
                d_print('WRONG PARAM: "{}" from "[{}]{}"'.format(
                    token_param_type_type_name, 
                    token_hex_representation, 
                    token_name), 
                        True)
            if not last_decompile_result:
                break
            if d_print.is_print: d_print('== token_params_text: {}'.format(token_params_text))
            if d_print.is_print: d_print('== current: {}'.format(bytes__to__hex_string(current)))
            if d_print.is_print: d_print('== working: {}'.format(bytes__to__hex_string(working)))
            if d_print.is_print: d_print('')

        if not last_decompile_result:
            if d_print.is_print: d_print('== token_params_text: {}'.format(token_params_text))
            if d_print.is_print: d_print('== current: {}'.format(bytes__to__hex_string(current)))
            if d_print.is_print: d_print('== working: {}'.format(bytes__to__hex_string(working)))
            if d_print.is_print: d_print('')

        if token_params_text.endswith(params_delimiter):
            token_params_text = token_params_text[:-len(params_delimiter)]
        
        if token_params_text_only.endswith(params_delimiter):
            token_params_text_only = token_params_text_only[:-len(params_delimiter)]

        # token_text = '[{}]{}({})'.format(token_hex_representation, token_info.name, token_params_text)
        close_bracket_spacing = current_token_spacing_string
        if len(token_params_text) == 0:
            close_bracket_spacing = ''
        label_text = decompile__get_current_label_text(labels_dict, initial_memory_offset)
        if label_text is None:
            token_text = '[({}):({})]{}({}{})'.format(
                    bytes__to__hex_string(struct.pack('<H', initial_memory_offset)),
                    token_hex_representation,
                    token_info.name,
                    token_params_text,
                    close_bracket_spacing)
            token_text_only = '{}({}{})'.format(token_info.name, token_params_text_only, close_bracket_spacing)
        else:
            token_text = '[({}):({})]{}{}({}{})'.format(
                    bytes__to__hex_string(struct.pack('<H', initial_memory_offset)),
                    token_hex_representation,
                    label_text,
                    token_info.name,
                    token_params_text,
                    close_bracket_spacing)
            token_text_only = '{}{}({}{})'.format(label_text, token_info.name, token_params_text_only,
                                                  close_bracket_spacing)

        result = (last_decompile_result, current, working, token_text, token_text_only, number_of_found_tokens,
                  memory_offset, hex_offset)
        if d_print.is_print:
            printable_result = (
                last_decompile_result,
                bytes__to__hex_string(current),
                bytes__to__hex_string(working),
                token_text,
                token_text_only,
                number_of_found_tokens,
                memory_offset, hex_offset)

    if d_print.is_print: d_print('SUB RESULT: {}'.format(printable_result))
    return result


def full_decompile(input_data, d_print=None, labels_dict=None, labels_id_generator=None, first_pass=True):
    d_print = d_print or DebugPrinter()
    labels_dict = labels_dict or dict()
    labels_id_generator = labels_id_generator or IDGenerator.IDGenerator()
    result = ('', '')
    working = copy.copy(input_data)
    current = b''
    token_text = ''
    token_text_only = ''
    tokens_delimiter = '\r\n\r\n'

    number_of_found_tokens = 0
    memory_offset = 0
    hex_offset = 0
    last_decompile_result = False
    token_text += '[#Mem Offset: ({})]'.format(bytes__to__hex_string(short_to_bytes(memory_offset)))
    token_text += '[#Hex Offset: ({})]\r\n'.format(bytes__to__hex_string(short_to_bytes(hex_offset)))

    need_to_process = True
    while need_to_process:
        decompile_result = decompile_token(working, labels_dict, labels_id_generator, 0, d_print, memory_offset, hex_offset)
        working = decompile_result[2]
        last_decompile_result = decompile_result[0]
        token_text += decompile_result[3] + tokens_delimiter
        token_text_only += decompile_result[4] + tokens_delimiter
        number_of_found_tokens += decompile_result[5]
        memory_offset = decompile_result[6]
        hex_offset = decompile_result[7]
        token_text += '[#Mem Offset: ({})]'.format(bytes__to__hex_string(short_to_bytes(memory_offset)))
        token_text += '[#Hex Offset: ({})]\r\n'.format(bytes__to__hex_string(short_to_bytes(hex_offset)))
        need_to_process = decompile_result[0] and (len(working) > 0)
        if not need_to_process and (len(working) > 0):
            print('ERROR IN [{}] FROM [{}]'.format(bytes__to__hex_string(working), bytes__to__hex_string(input_data)))

    result = (last_decompile_result, token_text, token_text_only, number_of_found_tokens, memory_offset, hex_offset)
    if first_pass:
        result = full_decompile(input_data, d_print, labels_dict, labels_id_generator=None, first_pass=False)

    return result


def decompile_put_text_into_brackets(string_data):
    if '\\' in string_data:
        string_data = string_data.replace('\\', '\\\\')
    if '\"' in string_data:
        string_data = string_data.replace('\"', '\\\"')
    string_data = ''.join(['\"', string_data, '\"'])
    return string_data


def compile__get_text_token(data, id_gen=None):
    result = None
    id_gen = id_gen or IDGenerator.IDGenerator()

    l_brack = data.find('\"')
    if l_brack >= 0:
        orig_l_part = data[:l_brack]
        orig_m_part = data[l_brack + 1:]
        orig_r_part = None

        start = 0
        r_brack = orig_m_part.find('\"', start)
        if r_brack == -1: raise CompileQuotesExceptionMissedRQuote(l_brack)
        while (((r_brack - 1) >= 0) and (orig_m_part[r_brack - 1] == '\\') and
                   ((r_brack - 2) >= 0) and (orig_m_part[r_brack - 2] != '\\')) or \
                (((r_brack - 1) >= 0) and (orig_m_part[r_brack - 1] == '\\')):
            start = r_brack + 1
            r_brack = orig_m_part.find('\"', start)
            if r_brack == -1: raise CompileQuotesExceptionMissedRQuote(l_brack)
        orig_r_part = orig_m_part[r_brack + 1:]
        orig_m_part = orig_m_part[:r_brack]

        id_m_part = ''.join(['<', str(id_gen.get_new_ID()), '>'])
        new_data = ''.join([orig_l_part, id_m_part, orig_r_part])

        parced_m_part = copy.copy(orig_m_part)
        if '\\\\' in parced_m_part:
            parced_m_part = parced_m_part.replace('\\\\', '\\')
        if '\\\"' in parced_m_part:
            parced_m_part = parced_m_part.replace('\\\"', '\"')

        result = (orig_m_part, parced_m_part, id_m_part, new_data, (l_brack, l_brack + r_brack))
    return result


def compile__get_all_text_tokens(data):
    id_gen = IDGenerator.IDGenerator()
    text_tokens = dict()
    another_result = compile__get_text_token(data, id_gen)
    while another_result is not None:
        # text_tokens[another_result[2]] = another_result[1]
        text_tokens[another_result[2]] = ''.join(['"', another_result[0], '"'])
        data = another_result[3]
        another_result = compile__get_text_token(data, id_gen)

    result = (data, text_tokens)
    return result


class CompileQuotesExceptionMissedRQuote(Exception):
    def __init__(self, l_bracket_position):
        message = 'Didn\'t found Right Quote after position {}'.format(l_bracket_position)
        super(CompileQuotesExceptionMissedRQuote, self).__init__(message)
        self.l_bracket_position = l_bracket_position


class UnresolvableNameReference(Exception):
    def __init__(self, message, name_ref):
        if message == '':
            message = 'Unresolvable Name Reference {}'.format(name_ref)
        super(UnresolvableNameReference, self).__init__(message)
        self.name_ref = name_ref


class CantFindNextToken(Exception):
    pass


class UnknownToken(Exception):
    def __init__(self, message, token_name):
        if message == '':
            message = 'Unknown Token {}'.format(token_name)
        super(UnknownToken, self).__init__(message)
        self.token_name = token_name


class CompileValueError(Exception):
    def __init__(self, message, token_name, param_name):
        super(CompileValueError, self).__init__(message)
        self.message = message
        self.token_name = token_name
        self.param_name = param_name


COMPILATION_EXCEPTIONS_SET = {
    CompileQuotesExceptionMissedRQuote,
    UnresolvableNameReference,
    CantFindNextToken,
    UnknownToken,
    CompileValueError
}


class CompileException(Exception):
    def __init__(self, exception_type, exception, data, str_data):
        super(CompileException, self).__init__(str(exception))
        self.exception_type = exception_type
        self.exception = exception
        self.data = data
        self.str_data = str_data


def compile__resolve_name_ref(param_name, name_table, need_zeros=False):
    # if '\"' == param_name[0]:
    #     clean_param_name = compile__get_text_token(param_name)[1]
    #     if clean_param_name in name_table:
    #         param_bytecode = name_table[clean_param_name]
    #         if need_zeros:
    #             param_bytecode = b''.join([param_bytecode, b'\x00\x00\x00\x00'])
    #     else:
    #         raise UnresolvableNameReference()
    # else:
    #     param_bytecode = solid_hex_string__to__bytes(param_name)
    # return param_bytecode
    clean_param_name = param_name
    if '\"' == param_name[0]:
        # print('-')
        clean_param_name = compile__get_text_token(param_name)[1]
    if clean_param_name in name_table:
        param_bytecode = name_table[clean_param_name]
        if need_zeros:
            param_bytecode = b''.join([param_bytecode, b'\x00\x00\x00\x00'])
    # else:
    #     raise UnresolvableNameReference()
    else:
        try:
            param_bytecode = solid_hex_string__to__bytes(param_name)
        except binascii.Error as err:
            raise UnresolvableNameReference('', param_name)
    return param_bytecode


def compile_token(token_list, found_tokens_list, labels_dict, memory_offset, hex_offset, first_pass=False):
    result = None

    context = IsOK_ContextHolder('UE3 Bytecode Compiler - Token', None, ResultType(CriteriaType.optional, set()),
                                 False, True)
    number_of_found_tokens = 0

    working_token_list = copy.copy(token_list)
    current_token_list = copy.copy(found_tokens_list)
    current_bytecode_list = list()
    token_info = None
    token_bytecode = None
    token_name = None
    token_params = None
    token_termination_bytecode = None
    token_termination = None
    token_termination_name = None

    with is_ok(context, 'find token id'):
        if context:
            try:
                working_token_list = compile__detect_and_init_new_label(working_token_list, labels_dict, memory_offset)
                token_name = working_token_list[0]
                if 'JumpIfNot' == token_name:
                    yyy = 8
            except IndexError as err:
                raise CantFindNextToken(str(err))

            try:
                token_info = US_CODE_TABLE__ALL_TOKENS.token_by_name[token_name]
            except KeyError as err:
                raise UnknownToken(str(err), token_name)

            token_bytecode = token_info.code
            token_bytecode_len = len(token_bytecode)
            token_params = token_info.params
            token_termination_bytecode = token_info.termination
            token_termination = None
            token_termination_name = None
            if token_termination_bytecode is not None:
                token_termination = US_CODE_TABLE__ALL_TOKENS.token_by_code[token_termination_bytecode]
                token_termination_name = token_termination[1]

            current_bytecode_list.append(token_bytecode)
            current_token_list.append(token_name)
            working_token_list = working_token_list[1:]
            memory_offset += token_bytecode_len
            hex_offset += token_bytecode_len

            context.push_result(True)

    with is_ok(context, 'process token parameters'):
        if context:
            for param_t_id in token_params:
                param_t_info = TOKEN_TYPES.type_info_by_number[param_t_id]
                param_t_type = param_t_info.type
                param_t_name = param_t_info.name
                param_t_size_type = param_t_info.size_type
                param_t_mem_size_type = param_t_info.mem_size_type

                param_name = None
                param_hex_code = None
                param_bytecode = b''

                if param_t_type is None:
                    raise Exception('TOKEN COMPILATION: PARAM ID ({}) has unknown PARAM TYPE'.format(param_t_id))

                if TOKEN_TYPES.TOKENTYPE_TYPE__HAS_TYPE == param_t_type:
                    compile_result = compile_token(working_token_list, list(), labels_dict, memory_offset, hex_offset,
                                                   first_pass)
                    current_bytecode_list += compile_result[0]
                    current_token_list += compile_result[2]
                    working_token_list = compile_result[1]
                    number_of_found_tokens += compile_result[3]
                    memory_offset = compile_result[4]
                    hex_offset = compile_result[5]
                elif TOKEN_TYPES.TOKENTYPE_TYPE__TOKENS_LIST_WITH_TYPES == param_t_type:
                    if token_termination is None:
                        raise Exception('TOKEN COMPILATION: TOKEN ({}) has no termination'.format(token_name))
                    param_name = working_token_list[0]
                    # working_token_list = working_token_list[1:]
                    continue_processing = True
                    while continue_processing:
                        if param_name == token_termination_name:
                            continue_processing = False
                        compile_result = compile_token(working_token_list, list(), labels_dict, memory_offset,
                                                       hex_offset, first_pass)
                        current_bytecode_list += compile_result[0]
                        current_token_list += compile_result[2]
                        working_token_list = compile_result[1]
                        number_of_found_tokens += compile_result[3]
                        memory_offset = compile_result[4]
                        hex_offset = compile_result[5]
                        if len(working_token_list) > 0:
                            param_name = working_token_list[0]
                        else:
                            param_name = None
                elif TOKEN_TYPES.TOKENTYPE_TYPE__JUST_SIZE == param_t_type:
                    param_name = working_token_list[0]
                    # print(param_name)
                    working_token_list = working_token_list[1:]

                    try:
                        if param_t_name in {'NameRef'}:
                            param_bytecode = compile__resolve_name_ref(param_name, UPK__NAMES_TABLE__ID_BY_NAME, True)
                        elif param_t_name in {'ObjRef', 'ObjRef_class', 'ObjRef_member', 'ObjRef_struct', 'RetValRef'}:
                            param_bytecode = compile__resolve_name_ref(param_name, UPK__NAMES__ID_BY_NAME, False)
                        elif param_t_name in {'MemOff'}:
                            if param_name.startswith('@'):
                                if working_token_list[0] == '5':
                                    yyy = 6
                                working_token_list = compile__translate_known_label_to_mem_offset(param_name,
                                                                                                  working_token_list,
                                                                                                  labels_dict,
                                                                                                  first_pass)
                                param_name = working_token_list[0]
                                working_token_list = working_token_list[1:]
                                param_bytecode = param_name
                            else:
                                param_bytecode = solid_hex_string__to__bytes(param_name)
                        elif param_t_name in {'NullTerminatedString'}:
                            if '\"' == param_name[0]:
                                cleam_param_name = compile__get_text_token(param_name)[1]
                                param_bytecode = cleam_param_name.encode()
                            else:
                                param_bytecode = solid_hex_string__to__bytes(param_name)
                        elif param_t_name in {'Byte'}:
                            if '\"' == param_name[0]:
                                clean_param_number = compile__get_text_token(param_name)[1]
                                param_bytecode = byte_to_bytes(int(clean_param_number))
                            else:
                                param_bytecode = solid_hex_string__to__bytes(param_name)
                        elif param_t_name in {'Short'}:
                            if '\"' == param_name[0]:
                                clean_param_number = compile__get_text_token(param_name)[1]
                                param_bytecode = short_to_bytes(int(clean_param_number))
                            else:
                                param_bytecode = solid_hex_string__to__bytes(param_name)
                        elif param_t_name in {'Int32'}:
                            if '\"' == param_name[0]:
                                clean_param_number = compile__get_text_token(param_name)[1]
                                param_bytecode = int_to_bytes(int(clean_param_number))
                            else:
                                param_bytecode = solid_hex_string__to__bytes(param_name)
                        elif param_t_name in {'Float32'}:
                            if '\"' == param_name[0]:
                                clean_param_number = compile__get_text_token(param_name)[1]
                                param_bytecode = float_to_bytes(float(clean_param_number))
                            else:
                                param_bytecode = solid_hex_string__to__bytes(param_name)
                        else:
                            param_bytecode = solid_hex_string__to__bytes(param_name)
                    except UnresolvableNameReference as ex:
                        raise UnresolvableNameReference('PARAM ({}) OF TOKEN ({}) '
                                                        'has unresolvable name reference ({})'.format(param_t_name,
                                                                                                      token_name,
                                                                                                      param_name),
                                                        ex.name_ref)
                    except struct.error as ex:
                        raise CompileValueError(str(ex), token_name, param_name)
                    except ValueError as ex:
                        raise CompileValueError(str(ex), token_name, param_name)

                    current_bytecode_list.append(param_bytecode)
                    try:
                        param_bytecode_len = len(param_bytecode)
                    except:
                        pass
                    if param_t_mem_size_type == TOKEN_TYPES.TOKENTYPE_MEMORY_SIZE_TYPE__SAME_AS_HEX_SIZE:
                        memory_offset += param_bytecode_len
                    else:
                        memory_offset += param_t_mem_size_type
                    hex_offset += param_bytecode_len
                    if TOKEN_TYPES.TOKENTYPE_SIZE_TYPE__NULLTERMINATED == param_t_size_type:
                        current_bytecode_list.append(b'\x00')
                        memory_offset += 1
                        hex_offset += 1
                    current_token_list.append(param_name)
                    number_of_found_tokens += 1
                else:
                    raise Exception('TOKEN COMPILATION: PARAM ID ({}) has unknown PARAM TYPE'.format(param_t_id))

            context.push_result(True)

    with is_ok_reader(context):
        if context:
            result = (current_bytecode_list,
                      working_token_list,
                      current_token_list,
                      number_of_found_tokens,
                      memory_offset,
                      hex_offset)
        else:
            context.raise_bad_blocks()

    return result


def full_compile(original_input_data, labels_dict=None, first_pass=True):
    input_data = copy.deepcopy(original_input_data)
    result = None
    labels_dict = labels_dict or dict()

    context = IsOK_ContextHolder('UE3 Bytecode Compiler', None, ResultType(CriteriaType.optional, set()), False, True)

    with is_ok(context, 'remove description from the code'):
        if context:
            description_end_word_len = len(DESCRIPTION_END_WORD)
            while (DESCRIPTION_BEGIN_WORD in input_data) and (DESCRIPTION_END_WORD in input_data):
                description_begin = input_data.index(DESCRIPTION_BEGIN_WORD)
                description_end = input_data.index(DESCRIPTION_END_WORD)
                if description_end > description_begin:
                    input_data = input_data[:description_begin] + input_data[description_end + description_end_word_len:]
                else:
                    # print('ERROR: DESCRIPTION TAGS')
                    raise IsOK_BlockFailed('ERROR: DESCRIPTION TAGS')
            context.push_result(True, input_data)

    with is_ok(context, 'get all text tokens'):
        if context:
            input_data = context.read_block_result_link('remove description from the code').result
            input_data, text_tokens = compile__get_all_text_tokens(input_data)
            # try:
            #     input_data, text_tokens = compile__get_all_text_tokens(input_data)
            # except CompileQuotesExceptionMissedRQuote as ex:
            #     err_message = str(ex)
            #     raise IsOK_BlockFailed(err_message)
            context.push_result(True, (input_data, text_tokens))

    with is_ok(context, 'split to tokens list'):
        if context:
            input_data, text_tokens = context.read_block_result_link('get all text tokens').result
            input_data = ''.join(input_data.split())
            input_data = ' '.join(input_data.split(','))
            input_data = ' '.join(input_data.split('('))
            input_data = ' '.join(input_data.split(')'))

            # if ',' in input_data:
            #     input_data = input_data.replace(',', ' ')
            # if '(' in input_data:
            #     input_data = input_data.replace('(', ' ')
            # if ')' in input_data:
            #     input_data = input_data.replace(')', ' ')

            # set_of_delimiters = SET_OF_DELIMITERS
            # for delimiter in set_of_delimiters:
            #     if delimiter in input_data:
            #         input_data = input_data.replace(delimiter, ' ')

            tokens_list = input_data.split()

            new_token_list = list()
            for token in tokens_list:
                if token[0] == '<':
                    token = text_tokens[token]
                new_token_list.append(token)
            tokens_list = new_token_list
            context.push_result(True, tokens_list)

    current_token_list = list()
    found_tokens_list = list()
    working_token_list = list()

    with is_ok(context, 'tokens to bytecode'):
        if context:
            tokens_list = context.read_block_result_link('split to tokens list').result
            # print(tokens_list)
            current_token_list = list()
            found_tokens_list = list()
            working_token_list = tokens_list
            number_of_found_tokens = 0
            memory_offset = 0
            hex_offset = 0
            while len(working_token_list) > 0:
                compile_result = compile_token(working_token_list, list(), labels_dict, memory_offset, hex_offset,
                                               first_pass)
                current_token_list += compile_result[0]
                working_token_list = compile_result[1]
                found_tokens_list += compile_result[2]
                number_of_found_tokens += compile_result[3]
                memory_offset = compile_result[4]
                hex_offset = compile_result[5]
            compiled_bytecode = b''.join(current_token_list)
            context.push_result(True, (compiled_bytecode, number_of_found_tokens, memory_offset, hex_offset))

    with is_ok_reader(context):
        if context:
            result = context.read_block_result_link('tokens to bytecode').result
        else:
            # print('COMPILATION ERRORS LOG: \n{}'.format(context.get_bad_blocks_str()))
            bad_blocks = context.get_bad_blocks()
            for block in bad_blocks:
                block_result_data = block[3][1]
                if type(block_result_data) is IsOK_IntenalResult:
                    if IsOK_IntenalResultType.external_exception == block_result_data.type_id:
                        ex = block_result_data.data
                        trace = block_result_data.str_data
                        if ex[0] in COMPILATION_EXCEPTIONS_SET:
                            # print()
                            # print(trace)
                            # print(ex[0])
                            # print(ex[1])
                            # print(working_token_list)
                            raise CompileException(ex[0], ex[1], (working_token_list,), trace)
            # raise Exception(context.get_bad_blocks_str())
            context.raise_bad_blocks()

    if first_pass:
        result = full_compile(original_input_data, labels_dict, first_pass=False)

    return result


def decompile_and_then_compile_for_test_bytecode():
    some_wrong_prefix_data = ''
    # some_wrong_prefix_data = 'ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff'

    input_file_name = input('Enter Input File Path [{}]: '.format(INPUT_FILE_NAME))
    if len(input_file_name) == 0:
        input_file_name = INPUT_FILE_NAME

    input_hex_string = None
    with open(input_file_name, 'r') as file:
        input_hex_string = file.read()

    input_string = hex_string__to__bytes(some_wrong_prefix_data + input_hex_string)

    startTime = time.time()
    d_print = DebugPrinter(None, False, print_type=DebugPrintType.string)
    decompile_result = full_decompile(input_string, d_print)
    print(d_print.full_string_log)
    endTime = time.time()
    resultTime = endTime - startTime

    print()
    print('DECOMPILATION -- PROCESSED {} TOKENS IN {} SECONDS.'.format(decompile_result[3], resultTime))
    if decompile_result[0]:
        print('SUCCESS')
        # print('FULL RESULT: {}'.format(decompile_result[1]))
        # print('TEXT RESULT: {}'.format(decompile_result[2]))
        pass
    else:
        print('FULL RESULT ERROR: {}'.format(decompile_result[1]))
        print('TEXT RESULT ERROR: {}'.format(decompile_result[2]))

    for_file = DESCRIPTION_BEGIN_WORD + '\r\n' + '\r\n{}'.format(decompile_result[1]) + DESCRIPTION_END_WORD + '\r\n' \
               + '\r\n\r\n{}'.format(decompile_result[2])
    for_file = for_file.encode()
    with open(OUTPUT_FILE_NAME, 'bw') as file:
        file.write(for_file)

    print()
    print('COMPILER TEST:')
    startTime = time.time()
    compile_result = full_compile(for_file.decode())
    endTime = time.time()
    resultTime = endTime - startTime

    compiled_bytecode = compile_result[0]
    compiled_hex = bytes__to__hex_string(compiled_bytecode)
    number_of_found_tokens = compile_result[1]
    test_result = (input_hex_string == compiled_hex)
    print('COMPILATION -- PROCESSED {} TOKENS IN {} SECONDS.'.format(number_of_found_tokens, resultTime))
    print('SUCCESS')
    print()

    if test_result:
        print('IDENTITY TEST: SUCCESS')
    else:
        print('IDENTITY TEST: FAULT!')
        print('INPUT STRING: {}'.format(input_hex_string))
        print('COMPILED HEX: {}'.format(compiled_hex))
        print('STARTING DEBUG DECOMPILATION PROCESS.')

    if not test_result:
        d_print = DebugPrinter(None, False, print_type=DebugPrintType.string)
        decompile_result = full_decompile(compiled_bytecode, d_print)
        print(d_print.full_string_log)

        print()
        print('PROCESSED {} TOKENS.'.format(decompile_result[3]))
        if decompile_result[0]:
            print('SUCCESS')
        else:
            print('FULL RESULT ERROR: {}'.format(decompile_result[1]))
            print('TEXT RESULT ERROR: {}'.format(decompile_result[2]))

        for_file = DESCRIPTION_BEGIN_WORD + '\r\n' + '\r\n{}'.format(decompile_result[1]) + DESCRIPTION_END_WORD + '\r\n' \
                   + '\r\n\r\n{}'.format(decompile_result[2])
        for_file = for_file.encode()
        with open(OUTPUT_FILE_NAME+'.debug.ucb', 'bw') as file:
            file.write(for_file)

    print()
    print('DONE.')


def compile_and_reformat_source_code():
    d_print = DebugPrinter(None, False, print_type=DebugPrintType.string)
    default_source_ucb_file_name = r'C:\Development\XCOM Modding\NewHitDamageCalc\XComGame.XGAbility_Targeted.' \
                                   r'RollForHit.new.ucb'
    ucb_file_name = input('Enter source file path [{}]: '.format(default_source_ucb_file_name))
    if len(ucb_file_name) == 0:
        ucb_file_name = default_source_ucb_file_name
    original_ucb_file_data = None

    with open(ucb_file_name, 'r') as file:
        original_ucb_file_data = file.read()

    ucb_file_name_only, ucb_file_name_ext = os.path.splitext(ucb_file_name)

    with open(''.join([ucb_file_name, '.', str(int(time.time())), '.bak']), 'w') as file:
        file.write(original_ucb_file_data)

    compile_result = full_compile(original_ucb_file_data)
    compiled_bytecode = compile_result[0]
    compiled_hex_code = bytes__to__hex_string(compiled_bytecode)

    with open(''.join([ucb_file_name_only, '.fbc']), 'w') as file:
        file.write(compiled_hex_code)

    print()
    print('COMPILATION DONE.')
    print('PROCESSED {} TOKENS'.format(compile_result[1]))
    print('SUCCESS')

    decompile_result = full_decompile(compiled_bytecode, d_print)
    print(d_print.full_string_log)
    print()
    print('DECOMPILATION DONE')
    print('PROCESSED {} TOKENS.'.format(decompile_result[3]))
    if decompile_result[0]:
        print('SUCCESS')
    else:
        print('FULL RESULT ERROR: {}'.format(decompile_result[1]))
        print('TEXT RESULT ERROR: {}'.format(decompile_result[2]))

    for_file = DESCRIPTION_BEGIN_WORD + '\r\n' + '\r\n{}'.format(decompile_result[1]) + DESCRIPTION_END_WORD + '\r\n' \
               + '\r\n\r\n{}'.format(decompile_result[2])
    for_file = for_file.encode()
    with open(ucb_file_name + FileExtensions.reformatted_ucb_source_code, 'bw') as file:
        file.write(for_file)

    if decompile_result[0]:
        print('Mem size', decompile_result[4])
        print('HEX size', decompile_result[5])
        print('Bytes len', len(compiled_bytecode))

        mod_file_content_strings = [
            'MOD_NAME= ',
            'AUTHOR=',
            'DESCRIPTION= ',
            'UPK_FILE=XComGame.upk',
            'OBJECT=XGAbility_Targeted.RollForHit:AUTO',
            '[REPLACEMENT_CODE]',
            compiled_hex_code,
            # 'EXPAND_FUNCTION=XGAbility_Targeted.RollForHit:' + str(decompile_result[4])
        ]

        mod_file_content = '\n'.join(mod_file_content_strings)
        mod_file_path = r'C:\Development\XCOM Modding\Work\Mod files\new_hit_damage_calc.txt'
        with open(mod_file_path, 'w') as file:
            file.write(mod_file_content)

        print('')
        print('MOD FILE CREATED.')
        print()
        print('DONE.')


def text_preview(text_str, max_len):
    result = text_str
    if len(text_str) > max_len:
        result = ''.join([text_str[:max_len], '...'])
    return result


def run_compile_and_reformat_source_code_with_debug_out(operation_runner):
    max_error_preview_size = 100
    try:
        operation_runner()
    except CompileQuotesExceptionMissedRQuote as err:
        ex_string = 'ERROR: ({}); Didn\'t found Right Quote after position {}'.format(err.l_bracket_position)
        raise Exception(ex_string)
    except CompileException as err:
        if CompileQuotesExceptionMissedRQuote == err.exception_type:
            ex_string = '{}\nERROR: ({}); Didn\'t found Right Quote after position {}'.format(
                    err.str_data,
                    text_preview(str(err.exception), max_error_preview_size),
                    err.exception.l_bracket_position
            )
            raise Exception(ex_string)
        if UnresolvableNameReference == err.exception_type:
            ex_string = '{}\nERROR: ({}); Unresolvable name reference "{}" in this expression: ({})'.format(
                    err.str_data,
                    text_preview(str(err.exception), max_error_preview_size),
                    err.exception.name_ref,
                    err.data[0]
            )
            raise Exception(ex_string)
        elif CantFindNextToken == err.exception_type:
            ex_string = '{}\nERROR: ({}); MAYBE you forgot one or more "EndFP()" tokens in this expression: ({})'.format(
                    err.str_data,
                    text_preview(str(err.exception), max_error_preview_size),
                    err.data[0]
            )
            raise Exception(ex_string)
        elif UnknownToken == err.exception_type:
            ex_string = '{}\nERROR: ({}); Unknown token name "{}" in this expression: ({})'.format(
                    err.str_data,
                    text_preview(str(err.exception), max_error_preview_size),
                    err.exception.token_name,
                    err.data[0]
            )
            raise Exception(ex_string)
        elif CompileValueError == err.exception_type:
            ex_string = '{}\nERROR: ({}); Param "{}" of Token "{}" has a Value Error "{}" in this expression: ({})'.format(
                    err.str_data,
                    text_preview(str(err.exception), max_error_preview_size),
                    err.exception.param_name,
                    err.exception.token_name,
                    err.exception.message,
                    err.data[0]
            )
            raise Exception(ex_string)
        else:
            raise err
    except IsOK_HistoryExport as err:
        error_log = IsOK_ContextHolder._block_list_to_str(err.history)
        print('COMPILATION ERRORS LOG: \n{}'.format(error_log))


if __name__ == "__main__":
    option = input('Choose an option (\'c\' = compile; \'d\' = decompile): ')
    if 'd' == option:
        run_compile_and_reformat_source_code_with_debug_out(decompile_and_then_compile_for_test_bytecode)
        # decompile_and_then_compile_for_test_bytecode()
        # cProfile.run('decompile_and_then_compile_for_test_bytecode()', 'ue_bytecode_assembler.prof')
    elif 'c' == option:
        run_compile_and_reformat_source_code_with_debug_out(compile_and_reformat_source_code)
    else:
        print('WRONG OPTION!')
