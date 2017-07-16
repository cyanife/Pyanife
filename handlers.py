#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging; logging.basicConfig(level=logging.INFO)
import asyncio, json, hashlib, base64, re
import time
import markdown

from aiohttp import web

from framework import get, post
from models import guid, Blog, Comment, Admin

from config import configs
from exceptions import * 

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_COOKIE_SALT = configs['session']['salt']

@get('/')
async def index(request):
    return { 
        '__template__' : 'index.html',
        }

# Simple blog

# Auxiliary classes and functions

# Page split caculator
class pageSplitter(object):
    def __init__(self, item_count, page_index=1, page_size=2):
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size >0 else 0)
        # If out of range, display nothing 
        if (item_count == 0) or (page_index > self.page_count) or (page_index < 1):
            self.page_index = 1
            self.offset = 0
            self.limit = 0
        else:
            self.page_index = page_index
            # offset calc
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size
        self.has_next_page = self.page_index < self.page_count
        self.has_previous_page = self.page_index > 1 

    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

    __repr__ = __str__

    # when page index has some problems, auto go to page 1
    @classmethod
    def str2index(self,page_str):
        try:
            i = int(page_str)
        except:
            i = 1
        if i < 1:
            i = 1
        return i

# cookie generator
# generate as format: id-expiresat-hash

def cookieGen(admin, validtime):
    expiresat = str(int(time.time() + validtime))
    h = '%s-%s-%s-%s' % (admin.id, admin.passwd, expiresat, _COOKIE_SALT)
    cookie = '-'.join([admin.id, expires, hashlib.sha1(h.encode('utf-8')).hexdigest()])
    return cookie

# cookie checker
async def cookiechk(cookie):
    if not cookie:
        return None
    try:
        cookie_list = cookie.split('-')
        if len(cookie_list) != 3:
            return None
        id, expiresat, hash = cookie_list
        if int(expiresat) < time.time():
            return None
        admin = await Admin.find(id)
        if admin is None:
            return None
        h = '%s-%s-%s-%s' % (id, admin.passwd, expiresat, _COOKIE_SALT)
        if hash != hashlib.sha1(h.encode('utf-8')).hexdigest():
            logging.info('invalid hash')
            return None
        admin.passwd = '*'
        return admin
    except Exception as e:
        logging.exceptions(e)
        return None

# # blog index page
# @get('/blog')
# async def blogindex(*, page='1'):
#     page_index = pageSplitter.str2index(page) 
#     count = await blog.findNumber('count(id)')
#     logging.info('count: %s' % count)
#     ps = pageSplitter(count, page_index)
#     if count == 0:
#         blogs = list()
#     else:
#         # use pageSplitter to fetch results
#         blogs = await blog.findAll(orderBy='timestamp desc', limit=ps.limit, offset=ps.offset)
#     return {
#         '__template__': 'blogs.html',
#         'page' : ps,
#         'blogs': blogs
#     }

# Blog index page
@get('/blog')
async def blogindex(* , p='1'):
    page_index = pageSplitter.str2index(p) 
    count = await Blog.findNumber('count(id)')
    logging.info('count: %s' % count)
    ps = pageSplitter(count, page_index)
    if count == 0:
        blogs = list()
    else:
        # use pageSplitter to fetch results
        blogs = await Blog.findAll(orderBy='timestamp desc', limit=ps.limit, offset=ps.offset)
        pager = {'total': ps.item_count, 'limit':ps.limit, 'page': ps.page_index}
    return {
        '__template__': 'blogs.html',
        'page' : pager,
        'blogs': blogs
    }

# get blog by id
@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id)
    blog.html_content = markdown.markdown(blog.content)
    comments = await Comment.findAll('blog_id=?', [id], orderBy='timestamp desc')
    return {
        '__template__' : 'blog.html',
        'blog' : blog,
        'comments' : comments
}

# create comment api
@post('/api/blogs/{id}/comments')
async def api_create_comment(*,id, user_name, user_email, user_website=None, content):
    if (user_name is None) or (user_email is None) or (content.strip() is None):
        raise APIValueError('requied value is missing')
    if not _RE_EMAIL.match(user_email):
        raise APIValueError('Email address is invalid')
    blog = await Blog.find(id)
    if blog is None:
        raise APINotFountError('blog is missing id:%s'%id)
    comment = Comment(blog_id = id, user_name = user_name, user_email=user_email,user_website=user_website,content=content.strip())
    await comment.save()
    return comment
    