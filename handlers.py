#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging; logging.basicConfig(level=logging.INFO)
import asyncio, json, hashlib, base64, re, json
import time
import markdown

from aiohttp import web

from framework import get, post
from models import guid, Blog, Comment, Admin

from config import configs
from exceptions import * 

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')

COOKIE_NAME = 'pyanifesession'
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
    cookie = '-'.join([admin.id, expiresat, hashlib.sha1(h.encode('utf-8')).hexdigest()])
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

# auth checker
def auth_check(request):
    if not isinstance(request.__admin__, Admin):
        raise APIPermissionError()
###########
# BLOG
###########

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

# Get blog by id
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

# get a blog API
@get('/api/blogs/{id}')
async def api_get_blog(*,id):
    blog = await Blog.find(id)
    if blog is None:
        raise APINotFountError('blog','blog not found, id: %s'%id)
    return blog

# get blogs API
@get('/api/blogs')
async def api_get_blogs(*, p=1):
    page_index = pageSplitter.str2index(p)
    count = await Blog.findNumber('count(id)')
    ps = pageSplitter(count, page_index, page_size=2)
    pager = {'total': ps.item_count, 'limit':ps.limit, 'page':ps.page_index}
    if count == 0:
        return dict(page=pager, blogs=())
    blogs = await Blog.findAll(orderBy='timestamp desc', limit=ps.limit,offset= ps.offset)
    return dict(page=pager, blogs=blogs)

# write a blog API
@post('/api/blogs')
async def api_write_blog(request,*,name,content):
    auth_check(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')
    blog = Blog(name=name.strip(), content=content.strip())
    await blog.save()
    return blog

# blog modify API
@post('/api/blogs/{id}/modify')
async def api_modify_blog(request, *, id, name, content):
    # check auth
    auth_check(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')
    #get blog
    blog = await Blog.find(id)
    blog.name = name
    blog.content = content

    #update
    await blog.update()
    return blog

# blog delete API
@post('/api/blogs/{id}/delete')
async def api_delete_blog(id, request):
    auth_check(request)
    blog = await Blog.find(id)
    if blog is None:
        raise APINotFoundError('blog','blog not found, id: %s' % id)
    # delete blog
    await blog.remove()
    return dict(id=id, result="removed")

###########
# COMMENTS
###########

# Create comment api
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
    
# get comments by page index, API
@get('/api/comments')
async def api_comments(*, p='1'):
    page_index = pageSplitter.str2index(p)
    count = await Comment.findNumber('count(id)')
    ps = pageSplitter(count, page_index, page_size=10)
    pager = {'total': ps.item_count, 'limit':ps.limit, 'page':ps.page_index}
    if count == 0:
        return dict(page=pager, comments=())
    comments = await Comment.findAll(orderBy='timestamp desc', limit=ps.limit,offset= ps.offset)
    return dict(page=pager, comments=comments)

# delete comment API
@post('/api/comments/{id}/delete')
async def delete_comment(id,request):
    auth_check(request)
    comm = await Comment.find(id)
    if comm is None:
        raise APINotFountError('comment, id:%s'%id)
    await comm.remove()
    return dict(id=id,result='removed')

########
# MANAGE
########

# sign in api
@post('/api/authenticate')
async def authenticate(*, name, passwd):
    if not name:
        raise APIValueError('name', 'Invalid name')
    if not passwd:
        raise APIValueError('passwd', 'Invalid passwd')
    admins = await Admin.findAll('name=?', [name])
    if len(admins) == 0:
        raise APIValueError('name', 'name not exist')
    if len(admins) > 1:
        raise APIValueError('name','Duplited admin name')
    admin = admins[0]
    # pw in table.admin: single hash
    pw_hash = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
    if admin.passwd != pw_hash:
        raise APIValueError('passwd', 'Invalid passwd')
    res = web.Response()
    res.set_cookie(COOKIE_NAME, cookieGen(
        admin, 86400), max_age=86400, httponly=True)
    # password shadowed
    admin.passwd = '*'
    # api, 
    # convert admin object to json
    res.content_type = 'application/json'
    res.body = json.dumps(admin, ensure_ascii=False).encode('utf-8')
    return res

# sign out
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    res = web.HTTPFound(referer or '/')
    # distroy cookie
    res.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('signed out')
    return res

# sign in page
@get('/signin')
def signin():
    return {
        '__template__' : 'manage_signin.html'
}

# manage index, redirected to comments (mostly used)
@get('/manage/')
def manage():
    return 'redirect:/manage/comments'
@get('/manage')
def manage():
    return 'redirect:/manage/comments'

# comment management page
@get('/manage/comments')
def manage_comments():
    return {
        '__template__': 'manage_comments.html'
}

# Blog manage page
@get('/manage/blogs')
def manage_blogs():
    return {
        '__template__': 'manage_blogs.html',
}



# Blog write page
@get('/manage/blogs/write')
def manage_write_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'api': '/api/blogs'
}

@get('/manage/blogs/{id}/modify')
def manage_edit_blog(id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'api': '/api/blogs/{id}/modify'
}


#############
# Image silde
#############
@get('/images')
def get_images():
    return { 
        '__template__': 'images.html',
    }