from couchbase.bucket import Bucket
from couchbase.exceptions import HTTPError
import json
bucket = Bucket("couchbase://localhost/demo")

def create_ddoc():

    try:
        bucket.design_get('demo',use_devmode=False)
        bucket.design_delete('demo',use_devmode=False)
    except HTTPError:
        pass

    bucket.design_create('demo',
                         {u'views': 
                          {u'all_keys': 
                           {u'map': u'function (doc, meta) {\n  emit(meta.id, null);\n}'}
                       }
                      },
                         use_devmode=False)
    print json.dumps(bucket.design_get('demo',use_devmode=False).value,indent=4)

def clean_all_docs():
    all_keys = [r.key for r in bucket.query('demo','all_keys')]
    print 'Found %s keys' % len(all_keys)
    if all_keys:
        bucket.delete_multi(all_keys,quiet=True)
                
    

if __name__ == '__main__':
    create_ddoc()
