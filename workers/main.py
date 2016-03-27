from multiprocessing import Process
import alerter
import collector

if __name__ == '__main__':
   p1 = Process(target=alerter.main_loop, args=())
   p1.start()

   p2 = Process(target=collector.collect_chargepoint_data_by_interval, args=(300,))
   p2.start()
   p2.join()
