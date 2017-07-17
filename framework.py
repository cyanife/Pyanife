#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import asyncio, functools
import inspect
import os
import json

from aiohttp import web

from urllib import parse

# implement @get decorator
def get(route):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = route 
        return wrapper
    return decorator

# @post decorator
def post(route):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = route 
        return wrapper
    return decorator

def parameterCheck(func):
    param_dict = dict()
    sign = inspect.signature(func)
    # pick (*, kw) without default value 
    required_param = list()
    # pick (*, kw) with default
    kw_param = list()
    # has a kw param?
    need_kw_param = False
    # has a varkw(**kw)?
    need_varkw_param = False
    # has a (request =)? 
    # TIP: request must be the last kw parameter(forced, to prevent error)
    need_request_param = False
    for name, param in sign.parameters.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            if param.default == inspect.Parameter.empty:
                required_param.append(name)
            kw_param.append(name)
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            need_varkw_param = True

        if name == 'request':
            need_request_param = True
            continue
        if need_request_param and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('requist parameter must be the last named parameter in function: %s%s' % (func.__name__,str(sign)))
    if len(required_param) or len(kw_param):
        need_kw_param = True
    param_dict['requied'] = tuple(required_param)
    param_dict['kw'] = tuple(kw_param)
    param_dict['need_kw'] = need_kw_param 
    param_dict['need_varkw'] = need_varkw_param 
    param_dict['need_request'] =  need_request_param
    return param_dict

# A callable handler get function's parameters from request
class requestHandler(object):

    def __init__(self, app, func):
        self.app = app
        self.func = func
        self.parameter = parameterCheck(func)

    async def __call__(self, request):
        kw = None

        if self.parameter.get('need_varkw') or self.parameter.get('need_kw') or self.parameter.get('need_request'):
            # recognize POST content and grab parameters
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type!')
                cont = request.content_type.lower()
                if cont.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return  web.HTTPBadRequest('JSON ERROR!')
                    kw = params
                elif cont.startswith('application/x-www-form-urlencoded') or cont.startswith('multipart/form-data'):
                    # TIPS: request.post() is a courotine!
                    params = await request.post() 
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
        if request.method == 'GET':  
            qs = request.query_string
            if qs:
                kw = dict()
                for k, v in parse.parse_qs(qs, True).items():
                    kw[k] = v[0]
        # if kw is empty, use request.match_info
        if not kw:
            kw = dict(**request.match_info)
        elif not self.parameter.get('need_varkw') and self.parameter.get('kw'):
            res =dict()
            # delete unnecessary params
            for name in self.parameter.get('kw'):
                if name in kw:
                    res[name] = kw[name]
            kw = res
        for k, v in request.match_info.items():
            if k in kw:
                logging.warning('Duplicate arg name in named arg and kw args: %s' % k) 
            kw[k] = v
        if self.parameter.get('need_request'):
            kw['request'] = request
        
        if self.parameter.get('required', None):
            for name in self.parameter.get('requierd'):
                if name not in kw:
                    return web.HTTPBadRequest('Missing Parameter :%s' % name)
        try:
            logging.info(kw)
            # give kw to func, get response
            result = await self.func(**kw)
            logging.info('handler result:%s'%result)
            return result
        except:
            pass

# static wrapper
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)

def isUrlFunction(func):
    method = getattr(func, '__method__', None)
    route = getattr(func, '__route__', None)
    if route and method:
        return True 
    return False

def add_route(app, func):
    if not isUrlFunction(func):
        raise TypeError('Not a wrapped URL functions: %s' % func.__name__)
    if not asyncio.iscoroutine(func) and not inspect.isgeneratorfunction(func):
        func = asyncio.coroutine(func)
    method = getattr(func, '__method__')
    route = getattr(func, '__route__')
    app.router.add_route(method, route, requestHandler(app, func))

def add_routes(app, module):
    funcs = __import__(module.split('.')[0])
    for attr in dir(funcs):
        # omit internal attributes
        if attr.startswith('_'):
            continue
        func = getattr(funcs, attr) 
        if callable(func) and isUrlFunction(func):
            add_route(app, func)
