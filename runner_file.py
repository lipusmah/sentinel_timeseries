if __name__ = "__main__":
    from os import system
    from time import sleep
    from datetime import datetime


    while True:
        print(datetime.now(),"-+- Starting")
        system('python main.py')
        print(datetime.now(),"-+- Crash")
        sleep(300)