import threading
import time
import random

class ThreadManager:
    def __init__(self, settings):
        self.settings = settings
        self.active_threads = 0
        self.lock = threading.Lock()

    def get_max_workers(self):
        # Work speed is 1-100%. 100% = 10 threads, 10% = 1 thread
        speed = self.settings.work_speed
        workers = max(1, int(10 * (speed / 100.0)))
        return workers

    def run_tasks(self, tasks, worker_func):
        results = []
        threads = []
        
        for task in tasks:
            # Динамически проверяем лимит. Если юзер потянул ползунок вниз, мы ждем.
            while True:
                with self.lock:
                    if self.active_threads < self.get_max_workers():
                        self.active_threads += 1
                        break
                time.sleep(0.5)

            def wrapped_worker(t):
                try:
                    res = worker_func(t)
                    results.append(res)
                finally:
                    with self.lock:
                        self.active_threads -= 1

            th = threading.Thread(target=wrapped_worker, args=(task,))
            th.start()
            threads.append(th)
            
            # Небольшая задержка, чтобы не открывать 5 браузеров в одну секунду
            time.sleep(random.uniform(1.0, 2.5))
            
        for th in threads:
            th.join()
            
        return results
