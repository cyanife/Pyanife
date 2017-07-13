import orm
from sqlmodels import blogModel, commentModel

def test():
   dst = orm.createDistination(name='pyanife', user='"user_pyanife"', pw='w7aw1314')

   yield from orm.createPool(dsn)

   b = blog(name='Test', content='HELLO')

   yield from blog.save()

for x in test():
    pass