import time
import threading
        

def this(i):
    print(f'Start THIS {i}')
    time.sleep(5)
    print(f'Finished THIS {i}')

def that(i):
    print(f'Start THAT {i}')
    time.sleep(3)
    print(f'Finished THAT {i}')

start = time.perf_counter()

t1 = threading.Thread(target=this, args=(5,))
t1.start()

t2 = threading.Thread(target=that, args=(3,))
t2.start()

for thread in (t1, t2):
    thread.join()

end = time.perf_counter()

print(end - start)