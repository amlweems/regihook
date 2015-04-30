#!/usr/bin/env python
# This is just an example!
# Customize this to fit your needs

import utexas
import semester

from concurrent import futures
import os

# Enable urllib3 logging if DEBUG is set
if os.getenv('DEBUG') != None:
    import logging
    logging.basicConfig(level=logging.DEBUG)

results = {}

def get_ut():
    ut = utexas.UTexas(semester.auth)
    ut.login()
    ut.choose_semester(semester.semester)
    return ut

def register(c, ut):
    success = 0
    for uid in c['uid']:
        try:
            if ut.register(uid):
                success = uid
                break
        except:
            pass
    results = { c['course']: success }
    if success == 0:
        for f in c['failure']:
            t = register(f, ut)
            results.update({k:v for k,v in t.items() if not(k in results) or v})
    return results

def register_thread(c):
    ut = get_ut()
    return register(c, ut)

with futures.ProcessPoolExecutor() as executor:
    for t in executor.map(register_thread, semester.schedule):
        results.update(t)

print("Registration complete")
for k,v in results.items():
    print(k, ":", v)
