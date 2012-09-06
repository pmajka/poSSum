import multiprocessing
import logging
import sys


class copier():
    def __init__(self):
        pass
   
    def __call__(self, index):
        print "sdfs %05d" % index
        return index

class manager():
    def __init__(self):
        pass
    
    def run(self):
        ii = copier()
        pool = multiprocessing.Pool(processes=4)
        result = pool.map(ii, range(10))
        print result

def worker():
    print 'Doing some work'
    sys.stdout.flush()

if __name__ == '__main__':
    multiprocessing.log_to_stderr(logging.DEBUG)
    ii = manager()
    ii.run()
#    ii = copier()   
#    multiprocessing.log_to_stderr(logging.DEBUG)
#    pool = multiprocessing.Pool(processes=4) 
#    pool.map(ii, range(10))

