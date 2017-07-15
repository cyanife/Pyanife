#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time

from framework import get, post

from models import guid, blog, comment

@get('/')
async def index(request):
    return { 
        '__template__' : 'index.html',
        }

# Simple blog

# Auxiliary classes and functions

# Page split caculator
class pageSplitter(object):

    def __init__(self, count, page):
        pass


# blog index page
@get('/blog')
def blogindex(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        blog(id='1', name='Test Blog', timestamp=time.time()-120),
        blog(id='2', name='Something New', timestamp=time.time()-3600),
        blog(id='3', name='Learn Swift', timestamp=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }