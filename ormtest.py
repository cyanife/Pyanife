import logging; logging.basicConfig(level=logging.INFO)
from models import Blog, Comment
import orm,asyncio
from config import configs

from handlers import pageSplitter
import re
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')

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
    kw={'user_name': '100', 'user_email': 'cyanife@gmail.com', 'content': 'hi100', 'id': '785c8795640df5bbe8443b28052df550'}
    res = await api_create_comment(**kw)



    print(res)

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()