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
    for x in xrange(3):
        all_keys = [r.key for r in bucket.query('demo','all_keys')]
        if all_keys:
            bucket.remove_multi(all_keys,quiet=True)
    print 'cleaned'
        
        
                

def get_random_date(days=365*3):
    """ returns random date in the last X days """
    to_time = int(time.time())
    from_time = int(time.time()-days*60*60*24)
    return datetime.date.fromtimestamp(random.randint(from_time,to_time))
  
def get_user_by_phone(phone):
    user_id = bucket.get('user_by_phone:%s' % phone, quiet=True).value
    if user_id:
        return bucket.get('user:%s' % user_id).value
    return None

def add_user(name,phone,join_date,verbose=True):
    existing_user = get_user_by_phone(phone)
    if existing_user:
        print 'User %s exists' % name
        return existing_user
    user_id = bucket.counter("user_counter",initial=1,delta=1).value
    user = {
        'name': name,
        'phone': phone,
        'join': join_date.isoformat(),
        'id': user_id,
        'doctype': 'user',
    }        
    key = 'user:%d' % user_id
    bucket.insert(key, user)
    bucket.insert('user_by_phone:%s' % user['phone'],user_id)
    if verbose:
        print 'Added user with key: %s' % key
    return user

def print_user(user_id):
    user = bucket.get('user:%d' % user_id).value
    print '-' * 50
    print 'user %s: %s' % (user['id'],user['name'])
    print 'phone: %s' % user['phone']
    print 'join: %s' % user['join']
    print '-' * 50

def create_chat(name,user_id):
    chat_id = bucket.counter('chat_counter',initial=1,delta=1).value
    chat = {
        'name' : name,
        'members': [user_id],
        'id' : chat_id
    }
    bucket.insert('chat:%s' % chat_id,chat)
    return chat

def join_user_to_chat(chat_id,user_id):
    chat = bucket.get('chat:%d' % chat_id).value
    chat['members'].append(user_id)
    print len(chat['members'])
    bucket.replace('chat:%d' % chat_id,chat)


def retry_cas(func):
    def _wrap(*args,**kwargs):
        for x in xrange(10):
            try:
                res = func(*args,**kwargs)
                return res
            except KeyExistsError:
                if x == 9:
                    raise 
                time.sleep(0.01)                
    return _wrap

@retry_cas
def join_user_to_chat_with_cas(chat_id,user_id):
    result = bucket.get('chat:%d' % chat_id)
    chat = result.value
    cas = result.cas
    chat['members'].append(user_id)
    print len(chat['members'])
    bucket.replace('chat:%d' % chat_id,chat,cas=cas)


    
def print_chat(chat_id):
    chat = bucket.get('chat:%d' % chat_id).value
    print '-' * 50
    print 'Chat %d: %s' % (chat['id'],chat['name'])
    print '%s members:' % len(chat['members'])
    keys = ['user:%d' % uid for uid in chat['members']]
    users = [r.value for r in bucket.get_multi(keys).values()]
    for user in users:
        print '\t%s' % user['name']
    print '--------------------------------------------'
    

def test1():
    clean_all_docs()
    eran = add_user('Eran Keydar','+12345',get_random_date())
    ido = add_user('Ido Keydar','+12346',get_random_date())
    yuval = add_user('Yuval Keydar','+12347',get_random_date())
    rotem = add_user('Rotem Keydar','+12348',get_random_date())
    print_user(eran['id'])
    chat = create_chat('the keydars',eran['id'])
    join_user_to_chat(chat['id'],ido['id'])
    join_user_to_chat(chat['id'],yuval['id'])
    join_user_to_chat(chat['id'],rotem['id'])
    print_chat(chat['id'])

def test2():
    import threading
    clean_all_docs()
    users = []
    eran = add_user('Eran Keydar','+12345',get_random_date())
    chat = create_chat('the keydars',eran['id'])
    chat_id = chat['id']
    for x in xrange(1,30):
        users.append(add_user('User %s' % x,'+123%05d' % x,get_random_date()))
    threads = []
    for user in users:
        t = threading.Thread(target=join_user_to_chat,args=(chat_id,user['id']))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print_chat(chat_id)
    

def test3():
    import threading
    clean_all_docs()
    users = []
    eran = add_user('Eran Keydar','+12345',get_random_date())
    chat = create_chat('the keydars',eran['id'])
    chat_id = chat['id']
    for x in xrange(1,30):
        users.append(add_user('User %s' % x,'+123%05d' % x,get_random_date()))
    threads = []
    for user in users:
        t = threading.Thread(target=join_user_to_chat_with_cas,args=(chat_id,user['id']))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print_chat(chat_id)
    
def test4():
	clean_all_docs()
	for x in xrange(10000):
		add_user('user %s' % x,'+123%05d' % x,get_random_date(),verbose=False)
	print bucket.get('user_counter').value
	# create the view
	
def test4_views():
	# by year
	rows = bucket.query('users','users_by_date',use_devmode=False,
		reduce=True,group_level=1)
	print 'By year'
	for row in rows:
		print row.key,row.value
	print 'Month with maximal users'
	rows = bucket.query('users','users_by_date',use_devmode=False,
		reduce=True,group_level=2)
	max_row = max(rows,key=lambda r : r.value)
	print max_row
	print 'All users joined in specific month'
	rows = bucket.query('users','users_by_date',
						 use_devmode=False,
						 reduce=False,
						 startkey=[2013,7,0],
						 endkey=[2013,7,35],
						 include_docs=True	
						 )
	for row in rows:
		u = row.doc.value
		print '%s joined in %s' % (u['name'],u['join']);

if __name__ == '__main__':
    create_ddoc()
