from time import time, sleep

from recorder import connect, disconnect, take_sample
from demofile import Demofile

SAMPLE_RATE_HZ = 20
RECORD_DURATION_S = 10

def record():
    # init
    demofile = Demofile(SAMPLE_RATE_HZ)
    connect()

    # record
    try:
        t = time()
        while True:
            start_time = time()
            sample = take_sample()

            if time() - t > RECORD_DURATION_S:
                break

            demofile.process_sample(sample)

            elapsed_time = time() - start_time
            remaining_time = max(0, (1/SAMPLE_RATE_HZ) - elapsed_time)
            sleep(remaining_time)
    finally:
        # Cleanup
        disconnect()
        demofile.commit(sample)

def main():
    record()

if __name__ == "__main__":
    main()
