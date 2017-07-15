import logging; logging.basicConfig(level=logging.INFO)
from models import blog, comment
import orm,asyncio
from config import configs

async def test(loop):

    dst=orm.createDistination(configs)
    await orm.createPool(dst,loop=loop)
    b = blog(name='test',content='hello')
    await b.save()
    blogs = await blog.findAll()
    print(blogs)

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()