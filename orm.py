#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, aiopg
import logging

# SQL log function
def showLog(log, args=()):
    try:
        logging.info('SQL: %s' % log)
        return True
    except:
        return False

# dsn: Argument which records SQL database information
def createDistination(name, user, pw, **kw):
    dsn = 'dbname=%s user=%s password=%s' % (name, user, pw)
    host = kw.get('host', None):
    if host:
        dsn = dsn + 'host=%s' %s host 
    host = kw.get('port', None):
    if port:
        dsn = dsn + 'port=%s' %s port 
    return dsn

def createSQLArgString(num):
    L=list()
    for i in range(num):
        L.append('?')
    return ', '.join(L)

# Database connection pool creation function
async def createPool(dsn, loop, **kw):
    logging.info('begin to create connection pool...')
    global __pool
    __pool = await aiopg.create_pool(
        dsn = dsn,
        loop = loop,
        minsize = kw.get('maxsize', 1),
        maxsize = kw.get('maxsize', 10)
    ) 

async def select(sql, args, size=None):
    showLog(sql)
    global __pool
    async with __pool.acquire() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute(sql.replace('?', '%s'), args or ())
                if size:
                    res = await cur.fenchmany(size)
                else:
                    res = await cur.fenchall()
            logging.info('rows: %s', len(res))
        except BaseException as e:
            raise # exception position
    return res

async def execute(sql, args):
    showlog(sql)
    async with __pool.acquire() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                modded = cur.rowcount
        except BaseException as e:
            raise # exception position
    return modded 

# Database column field attribute
class baseField(object):

    def __init__(self, name, data_type, isprimarykey, default_value):
        self.name = name
        self.data_type = data_type
        self.isprimarykey = isprimarykey
        self.default_value = default_value

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.data_type, self.name)

class integerField(baseField):
    def __init__(self, name=None, isprimarykey=False, default_value=0):
        super.__init__(name, 'bigint', isprimarykey, default_value)

class floatField(baseField):
    def __init__(self, name=None, isprimarykey=False, default_value=0.00):
        super.__init__(name, 'double precision', isprimarykey, default_value)

class boolenField(baseField):
    def __init__(self, name=None, default_value=False):
        super.__init__(name, 'boolean', False, default_value)

class stringField(baseField):
    def __init__(self, name=None, isprimarykey=False, default_value=None, length=100):
        super.__init__(name, 'varchar(%s)' % length, isprimarykey, default_value)

class textField(baseField):
    def __init__(self, name=None, default_value=None):
        super.__init__(name, 'text', default_value)


# Metaclass to verify mappings from model to SQL table and generate class.
class modelMeta(type):

    def __new__(cls, name, bases, attrs):
        if name == 'modelBase':
            return type.__new__(cls, name, bases, attrs)
        tablename = attrs.get('__tablename__', None) or name
        fields = list()
        primarykey = None
        mappings = dict()
        for k,v in attrs.items():
            if isinstance(v, field):
                logging.info('map %s to %s' % (k, v))
                mappings[k] = v
                if v.isprimarykey:
                    if primarykey:
                        raise # Duplicate primarykey
                    primarykey = k
                else:
                    fields.append(k)
            if not primarykey:
                raise # empty primarykey
            for k in mappings.keys():
                attrs.pop(k)
            escaped_fields = list(map(lambda f: '"%s"' % f,fields))
            # SQL operation statement
            attrs['__table__'] = tablename
            attrs['__mapping__'] = mappings
            attrs['__primarykey__'] = primarykey 
            attrs['__fields__'] = fields
            attrs['__select__'] = 'select "%s", %s from "%s"' % (primaryKey, ', '.join(escaped_fields), tableName)
            attrs['__insert__'] = 'insert into "%s" (%s, "%s") values (%s)' % (tablename, ', '.join(escaped_fields), primaryKey, createSQLArgString(len(escaped_fields) + 1))
            attrs['__update__'] = 'update "%s" set %s where "%s"=?' % (tablename, ', '.join(map(lambda f: '"%s"=?' % (mappings.get(f).name or f), fields)), primarykey)
            attrs['__delete__'] = 'delete from "%s" where "%s"=?' % (tablename, primarykey)
            return type.__new__(cls, name, bases, attrs)

class modelBase(dict, metaclass=modelMeta):
    def __init__(self, **kw):
        super(modelBase, self).__init__(**kw)
    
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            currentfield = self.__mappings__[key]
            if currentfield.default is not None:
                value = currentfield.default() if callable(currentfield.default) else currentfield.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = list() 
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        res = await select(' '.join(sql), args)
        return [cls(**r) for r in res]

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        sql = ['select %s _num_ from "%s"' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        res = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    # find object by primarykey 
    @classmethod
    async def find(cls, primarykey):
        res = await select('%s where "%s"=?' % (cls.__select__, cls.__primarykey__), [primarykey], 1)
        if len(res) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primarykey__))
        res = await execute(self.__insert__, args)
        if res != 1:
            logging.warn('failed to insert: affected rows: %s' % res)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        res = await execute(self.__update__, args)
        if res != 1:
            logging.warn('failed to update : affected rows: %s' % res)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        res = await execute(self.__delete__, args)
        if res != 1:
            logging.warn('failed to remove: affected rows: %s' % res)