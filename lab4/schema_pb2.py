# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: schema.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cschema.proto\"\x07\n\x05\x45mpty\"=\n\x04User\x12\x0f\n\x07user_id\x18\x01 \x01(\r\x12\x16\n\tuser_name\x18\x02 \x01(\tH\x00\x88\x01\x01\x42\x0c\n\n_user_name\"\x1d\n\x05Users\x12\x14\n\x05users\x18\x01 \x03(\x0b\x32\x05.User\"\x1a\n\x08Response\x12\x0e\n\x06status\x18\x01 \x01(\x08\x32i\n\x08\x44\x61tabase\x12\x1d\n\x07PutUser\x12\x05.User\x1a\t.Response\"\x00\x12 \n\nDeleteUser\x12\x05.User\x1a\t.Response\"\x00\x12\x1c\n\x08GetUsers\x12\x06.Empty\x1a\x06.Users\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'schema_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _EMPTY._serialized_start=16
  _EMPTY._serialized_end=23
  _USER._serialized_start=25
  _USER._serialized_end=86
  _USERS._serialized_start=88
  _USERS._serialized_end=117
  _RESPONSE._serialized_start=119
  _RESPONSE._serialized_end=145
  _DATABASE._serialized_start=147
  _DATABASE._serialized_end=252
# @@protoc_insertion_point(module_scope)
