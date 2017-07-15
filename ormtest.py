import logging; logging.basicConfig(level=logging.INFO)
from models import blog, comment
import orm,asyncio
from config import configs

from handlers import pageSplitter
async def blogindex(* , query='', page='1'):
    page_index = pageSplitter.str2index(page) 
    count = await blog.findNumber('count(id)')
    logging.info('count: %s' % count)
    ps = pageSplitter(count, page_index)
    if count == 0:
        blogs = list()
    else:
        # use pageSplitter to fetch results
        blogs = await blog.findAll(orderBy='timestamp desc', limit=ps.limit, offset=ps.offset)
        pager = {'total': ps.item_count, 'limit':ps.limit, 'curr_page': ps.page_index}
    return {
        '__template__': 'blogs.html',
        'p' : pager,
        'query' : query,
        'blogs': blogs
    }

async def test(loop):

    dst=orm.createDistination(configs)
    await orm.createPool(dst,loop=loop)
    # b = blog(name='test',content='hello')
    # await b.save()
    # blogs = await blog.findAll()
    # count = await blog.findNumber('count(id)')
    # blogs = await blog.findAll(orderBy='timestamp desc', limit=10, offset=0)
    res = await blogindex()
    print(res)

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()