#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

form framwork import get, post

from sqlmodel import guid, blog, comment

@get('/')
async def index(request):
    blogs = await blog.findAll()
    return { 
        '__template__' : 'test.html',
        'blogs' = blogs
        }