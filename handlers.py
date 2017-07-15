#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from framework import get, post

from sqlmodel import guid, blog, comment

@get('/')
async def index(request):
    blogs = await blog.findAll()
    return { 
        '__template__' : 'test.html',
        'blogs' : blogs
        }