import warnings
warnings.filterwarnings('error',category=DeprecationWarning)
from couchbase.bucket import Bucket
from couchbase.exceptions import HTTPError
import json
import random
import datetime
import time
bucket = Bucket("couchbase://localhost/demo")

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
    all_keys = [r.key for r in bucket.query('demo','all_keys')]
    print 'Found %s keys' % len(all_keys)
    if all_keys:
        bucket.delete_multi(all_keys,quiet=True)
                

def get_random_date(days=365):
    """ returns random date in the last X days """
    to_time = int(time.time())
    from_time = int(time.time())
    return datetime.date.fromtimestamp(random.randint(from_time,to_time))
  
def get_user_by_phone(phone):
    user_id = bucket.get('user_by_phone:%s' % phone, quiet=True).value
    if user_id:
        return get_user(user_id)
    return None

def add_user(name,phone,join_date,verbose=True):
    existing_user = get_user_by_phone(phone)
    if existing_user:
        print 'User %s exists' % name
        return
    user = dict()
    user_id = bucket.incr("user_counter",initial=1).value
    user['name'] = name
    user['phone'] = phone
    user['join'] = join_date.isoformat()
    user['id'] = user_id
    user['doctype'] = "user"
    user['docversion'] = 1
    key = 'user:%d' % user_id
    bucket.insert(key, user)
    bucket.insert('user_by_phone:%s' % user['phone'],user_id)
    if verbose:
        print 'Added user with key: %s' % key

def add_many_users(count=10000):
    for x in xrange(1,1+count):
        add_user(name='user%s' % x,
                 phone='+97256%05d' % random.randint(1,99999),
                 join_date=get_random_date(),
                 verbose=False)
    print 'Added %s users' % count


if __name__ == '__main__':
    create_ddoc()
