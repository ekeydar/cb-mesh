import warnings
warnings.filterwarnings('error',category=DeprecationWarning)
from couchbase.bucket import Bucket,LOCKMODE_WAIT
from couchbase.exceptions import HTTPError,KeyExistsError
import json
import random
import datetime
import time

bucket = Bucket("couchbase://localhost/demo",
                lockmode=LOCKMODE_WAIT)

def create_ddoc():
    bm = bucket.bucket_manager()
    try:
        bm.design_get('demo',use_devmode=False)
        bm.design_delete('demo',use_devmode=False)
    except HTTPError:
        pass

    bm.design_create('demo',
                     {u'views': 
                      {u'all_keys': 
                       {u'map': u'function (doc, meta) {\n  emit(meta.id, null);\n}'}
                   }
                  },
                     use_devmode=False)
    print json.dumps(bm.design_get('demo',use_devmode=False).value,indent=4)

def clean_all_docs():
    for x in xrange(2):
        clean_all_docs_once()
    print 'cleaned'

def clean_all_docs_once():
    skip = 0
    limit = 1000
    while True:
        keys = [r.key for r in bucket.query('demo','all_keys',skip=skip,limit=limit)]
        if keys:
            bucket.remove_multi(keys,quiet=True)
            skip+=limit
        else:
            return
        

def get_random_date(days=365*3):
    """ returns random date in the last X days """
    to_time = int(time.time())
    from_time = int(time.time()-days*60*60*24)
    return datetime.date.fromtimestamp(random.randint(from_time,to_time))
  
def get_random_country():
    countries = ['US','IL','GB','UA','CA','IT']
    return random.choice(countries)

def get_random_phone():
    return '+%08d' % (random.randint(0,99999999))


def create_random_env():
    users = []
    for x in xrange(10000):
        users.append(create_user('user:%s' % x,CU.get_random_phone(),CU.get_random_country(),CU.get_random_date()))
    print 'Created %s users'



if __name__ == '__main__':
    create_ddoc()
