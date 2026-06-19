import sys, time, signal, os
sys.path.insert(0, '/Users/govind/Library/Python/3.9/lib/python/site-packages')

class TimeoutError(Exception): pass

def handler(signum, frame):
    raise TimeoutError("Import timed out")

signal.signal(signal.SIGALRM, handler)

for mod in ['flask', 'yfinance', 'pandas', 'numpy']:
    signal.alarm(5)
    try:
        t0 = time.time()
        __import__(mod)
        dt = time.time() - t0
        print(f'{mod}: OK ({dt:.1f}s)')
    except TimeoutError:
        print(f'{mod}: TIMEOUT')
    except Exception as e:
        print(f'{mod}: ERROR {e}')
    finally:
        signal.alarm(0)

print('--- DONE ---')
