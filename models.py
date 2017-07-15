#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from uuid import uuid4
from hashlib import md5

from orm import modelBase, floatField, stringField, textField

def guid():
    id = '%015d%s' % (int(time.time()*1000), uuid4().hex)
    return md5(id.encode('utf-8')).hexdigest()

class blog(modelBase):
    __table__ = 'blogs'

    id = stringField(isprimarykey=True, default=guid, length=32)
    name = stringField(length=100)
    content = textField()
    timestamp = floatField(default=time.time)

class comment(modelBase):
    __table__ = 'comments'

    id = stringField(isprimarykey=True, default=guid, length=32)
    blog_id = stringField(length=32)
    user_name = stringField(length=50)
    user_email = stringField(length=100)
    user_website = stringField(length=100)
    content = textField()
    timestamp = floatField(default=time.time)

class admin(modelBase):
    __table__ = 'admins'

    id = stringField(isprimarykey=True, default=guid, length=32)
    name = stringField(length=100)
    passwd = stringField(length=100)
