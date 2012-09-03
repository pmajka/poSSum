import multiprocessing
import multiprocessing_3a

if __name__ == '__main__':
    jobs = []
    for i in range(5):
        p = multiprocessing.Process(target=multiprocessing_3a.worker)
        jobs.append(p)
        p.start()
