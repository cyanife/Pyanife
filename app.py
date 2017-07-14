#!/usr/bin/env python
# coding=utf8

import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, json, time

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import orm
from config import configs

from framework import add_route, add_routes, add_static

# jinja2 init function
def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    # jinja2 options. default:autoescape, blk {% %} , var {{ }} , autoreload
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'), 
        block_end_string=kw.get('block_end_string', '%}'), 
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),  
        auto_reload=kw.get('auto_reload', True)
    )
    # give template file's path
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    # add filters (bar|foo pipe functions in template) 
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env

async def response_factory(app, handler):
    async def response(request):
        # first get response
        res = await handler(request)
        # if response is bytes:
        if isinstance(res, web.StreamResponse):
            resp = web.Response(body=res)
            resp.content_type = 'application/octet-stream'
            return resp
        # if response is string:
        if isinstance(res, str):
            # is redirecting?
            if res.startswith('redirect:'):
                return web.HTTPFound(res[9:])
            else:
                resp = web.Response(body=res.encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        # if response is dict
        if isinstance(res, dict):
            # template or json?
            if res.get('__template__', None) is None:
                # is json.
                resp = web.Response(body=json.dumps(res, ensure_ascii=False, default=lambda j: j.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                # is template
                # use template
                resp = web.Response(body=app['__templating__'].get_template(res.get('__template__')).render(**res).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
        # if response is int
        if isinstance(res, int):
            if res >=100 and res < 600:
                # is http condition code
                return web.Response(res)
        # if response is 2-tuple
        if isinstance(res, tuple) and len(res) == 2:
            n, m = res
            # is http condition code and message
            if isinstance(n, int):
                return web.Response(status=n, text=str(m))
        
        # default: response as string
        resp = web.Response(body=str(res).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


# app init
async def init(loop):
    # create sql connection pool
    await orm.createPool(orm.createDistination(configs),loop)
    app = web.application(loop=loop, middlewares=[response_factory])
    init_jinja2(app)
    add_static(app)
    add_routes(app, 'handlers')
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 5000)
    logging.info('Server started at http://127.0.0.0.1:5000...')
    return srv

# event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

            
            






        
