import logging; logging.basicConfig(level=logging.INFO)
from models import Blog, Comment, Admin
import orm,asyncio
from config import configs
from aiohttp import web
from handlers import COOKIE_NAME, cookieGen
import json

from handlers import pageSplitter
import re
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
import hashlib
# async def blogindex(* , query='', page='1'):
#     page_index = pageSplitter.str2index(page) 
#     count = await blog.findNumber('count(id)')
#     logging.info('count: %s' % count)
#     ps = pageSplitter(count, page_index)
#     if count == 0:
#         blogs = list()
#     else:
#         # use pageSplitter to fetch results
#         blogs = await blog.findAll(orderBy='timestamp desc', limit=ps.limit, offset=ps.offset)
#         pager = {'total': ps.item_count, 'limit':ps.limit, 'curr_page': ps.page_index}
#     return {
#         '__template__': 'blogs.html',
#         'p' : pager,
#         'query' : query,
#         'blogs': blogs
#     }

# async def api_create_comment(*,id, user_name, user_email, user_website=None, content):
#     if (user_name is None) or (user_email is None) or (content.strip() is None):
#         raise APIValueError('requied value is missing')
#     if not _RE_EMAIL.match(user_email):
#         raise APIValueError('Email address is invalid')
#     blog = await Blog.find(id)
#     if blog is None:
#         raise APINotFountError('blog is missing id:%s'%id)
#     comment = Comment(blog_id = id, user_name = user_name, user_email=user_email,user_website=user_website,content=content.strip())
#     await comment.save()
#     return comment

# async def authenticate(*, name, passwd):
#     if not name:
#         raise APIValueError('name', 'Invalid name')
#     if not passwd:
#         raise APIValueError('passwd', 'Invalid passwd')
#     admins = await Admin.findAll('name=?', [name])
#     if len(admins) == 0:
#         raise APIValueError('name', 'name not exist')
#     if len(admins) > 1:
#         raise APIValueError('name','Duplited admin name')
#     admin = admins[0]
#     # pw in table.admin: single hash
#     pw_hash = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
#     if admin.passwd != pw_hash:
#         raise APIValueError('passwd', 'Invalid passwd')
#     res = web.Response()
#     res.set_cookie(COOKIE_NAME, cookieGen(
#         admin, 86400), max_age=86400, httponly=True)
#     # password shadowed
#     admin.passwd = '*'
#     # api, 
#     # convert admin object to json
#     res.content_type = 'application/json'
#     res.body = json.dumps(admin, ensure_ascii=False).encode('utf-8')
#     return res

# async def api_comments(*, p='1'):
#     page_index = pageSplitter.str2index(p)
#     count = await Comment.findNumber('count(id)')
#     ps = pageSplitter(count, page_index)
#     pager = {'total': ps.item_count, 'limit':ps.limit, 'page':ps.page_index}
#     if count == 0:
#         return dict(page=pager, comments=())
#     comments = await Comment.findAll(orderBy='timestamp desc', limit=ps.limit,offset= ps.offset)
#     return dict(page=pager, comments=comments)

async def delete_comment(id):
    comm = await Comment.find(id)
    if comm is None:
        raise APINotFountError('comment, id:%s'%id)
    await comm.remove()
    return dict(id=id,result='removed')

async def test(loop):

    dst=orm.createDistination(configs)
    await orm.createPool(dst,loop=loop)
    # b = blog(name='test',content='hello')
    # await b.save()
    # blogs = await blog.findAll()
    # count = await blog.findNumber('count(id)')
    # blogs = await blog.findAll(orderBy='timestamp desc', limit=10, offset=0)
    # res = await blogindex()

    # kw={'user_name': 'dddddddsdd', 'user_email': 'd@d.d', 'content': 'd', 'id': '785c8795640df5bbe8443b28052df550'}
    # kw={'user_name': '100', 'user_email': 'cyanife@gmail.com', 'content': 'hi100', 'id': '785c8795640df5bbe8443b28052df550'}
    # res = await api_create_comment(**kw)



    # print(res)
    # passwd = 'w7aw1314'
    # pw_hash = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
    # admin = Admin(name='cyanife',passwd=pw_hash)
    # await admin.save()
    # name = 'cyanife'
    # passwd = 'w7aw1314'
    # res = await authenticate(name=name,passwd=passwd)
    # print(res.cookies.get(COOKIE_NAME))

    # res = await  api_comments(p='1')
    # print(res['comments'])

    id = '36fe935167a56ca5228d2f558317939e'
    res = await delete_comment(id=id)
    print(res)



loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()