from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QCoreApplication, QWaitCondition, QMutex
import time
#from pyudev import Context, Monitor
import subprocess
#from pyudev import Context

i2c_mutex = QMutex()

class pHWorker(QObject):
    update_signal_pH = pyqtSignal(float,object)  # Define the signal to emit data
    
    def __init__(self, send_counter, test_time, read, data, dev, temp):
        super().__init__()
        self.is_running = True
        self.should_log = False
        self.pH_send_counter = send_counter
        self.pH_read = read
        self.pH_data = data
        self.pH_test_time = test_time
        self.pH_dev = dev
        self.pH_temp = temp
        self.pH_path = ""
        self.is_paused = False  # Pause control
        self.pause_condition = QWaitCondition()  # Condition for pausing
        self.mutex = QMutex()  # Mutex for condition

    def run(self):
        # Background task logic            
        while self.is_running:
            self.mutex.lock()
            if self.is_paused:
                self.pause_condition.wait(self.mutex)  # Wait until unpaused
            self.mutex.unlock()

            if self.pH_send_counter < time.time():
                if self.pH_read:
                    #self.pH_data, self.pH_test_time = self.pH_test(self.pH_data, self.pH_test_time)
                    try:
                        #print(f"Worker trying to lock i2c_mutex for read operation")
                        i2c_mutex.lock()
                        #print(f"i2c_mutex locked for read operation")
                        self.pH_data = float(self.pH_dev.read())
                        #print(f"Read data: {self.pH_data}")

                    except Exception as e:
                        print(f"Error reading {e}")
                    finally:
                        #print(f"i2c_mutex unlocked after read operation")
                        i2c_mutex.unlock()
                try:
                    #print(f"Worker trying to lock i2c_mutex for write operation")
                    i2c_mutex.lock()
                    #print(f"i2c_mutex locked for write operation")
                    #self.pH_dev.write(f'RT,{self.pH_temp}')
                    self.pH_dev.write(f'R')
                
                except Exception as e:
                    print(f"Error writing {e}")
                finally:
                    #print(f"i2c_mutex unlocked after write operation")
                    i2c_mutex.unlock()
                
                
                
                self.pH_send_counter = time.time() + 0.9
                self.pH_read = True
            else:
                pass

            self.update_signal_pH.emit(self.pH_data, 1)  # Emit signal with data

            time.sleep(0.9)  # Adjust the sleep time as needed

    def pause(self):
        print("Pause")
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()     
    
    def resume(self):
        self.is_paused = False
        self.mutex.lock()
        self.pause_condition.wakeAll()  # Resume execution
        self.mutex.unlock()

    def stop(self):
        self.is_running = False
        self.resume()  # Ensure the worker wakes up to stop

    def pH_test(self, data, test_time):
        increment = time.time() - test_time
        test_time = time.time()
        data += increment/25
        return data, test_time
    
class RTDWorker(QObject):
    update_signal_RTD = pyqtSignal(float,object)  # Define the signal to emit data

    def __init__(self, send_counter, test_time, read, data, dev):
        super().__init__()
        self.is_running = True
        self.should_log = False
        self.RTD_send_counter = send_counter
        self.RTD_read = read
        self.RTD_data = data
        self.RTD_test_time = test_time
        self.RTD_dev = dev
        self.RTD_path = ""
        self.RTD_is_paused = False  # Pause control
        self.RTD_pause_condition = QWaitCondition()  # Condition for pausing
        self.RTD_mutex = QMutex()  # Mutex for condition

    def run(self):
        # Background task logic
         while self.is_running:
            self.RTD_mutex.lock()
            if self.RTD_is_paused:
                self.RTD_pause_condition.wait(self.RTD_mutex)  # Wait until unpaused
            self.RTD_mutex.unlock()
            
            if self.RTD_send_counter < time.time():
                if self.RTD_read:
                    #self.RTD_data, self.RTD_test_time = self.RTD_test(self.RTD_data, self.RTD_test_time)
                    try:
                        #print(f"Worker trying to lock i2c_mutex for read operation")
                        i2c_mutex.lock()
                        #print(f"i2c_mutex locked for read operation")
                        self.RTD_data = float(self.RTD_dev.read())
                        #print(f"Read data: {self.RTD_data}")

                    except Exception as e:
                        print(f"Error reading {e}")
                    finally:
                        #print(f"i2c_mutex unlocked after read operation")
                        i2c_mutex.unlock()
                    
                try:
                    #print(f"Worker trying to lock i2c_mutex for write operation")
                    i2c_mutex.lock()
                    #print(f"i2c_mutex locked for write operation")
                    self.RTD_dev.write("R")
                except Exception as e:
                    print(f"Error writing {e}")
                finally:
                    #print(f"i2c_mutex unlocked after write operation")
                    i2c_mutex.unlock()    
    
                
                self.RTD_send_counter = time.time() + 0.6
                self.RTD_read = True
            else:
                pass

            self.update_signal_RTD.emit(self.RTD_data, 2)  # Emit signal with data
            time.sleep(0.7)  # Adjust the sleep time as needed

    def stop(self):
        self.is_running = False
    
    def pause(self):
        print("Pause")
        self.RTD_mutex.lock()
        self.RTD_is_paused = True
        self.RTD_mutex.unlock()     
    
    def resume(self):
        self.RTD_is_paused = False
        self.RTD_mutex.lock()
        self.RTD_pause_condition.wakeAll()  # Resume execution
        self.RTD_mutex.unlock()
    
    def RTD_test(self, data, test_time):
        increment = time.time() - test_time
        test_time = time.time()
        data += increment/10
        return data, test_time


class StatWorker(QObject):
    status_signal = pyqtSignal(bool)
    pump_signal = pyqtSignal(bool)
    def __init__(self, select, pHSelect , pH):
        super().__init__()
        self.pH = pH
        self.should_start = False
        self.select = select
        self.pHSelect = pHSelect
        self.is_running = True
    
    @pyqtSlot()
    def start_processing(self):
        self.should_start = not self.should_start

        #self.should_start = True

    def run(self):
        # Background task logic
        while self.is_running:
            if self.select == 0:
                if self.pH > self.pHSelect:
                    #print(f'Bigger then = True')

                    self.status_signal.emit(True)
                else: 
                    #print(f'Bigger then = False')
                    if self.should_start:
                        self.pump_signal.emit(False)
                    else:
                        pass
                    self.status_signal.emit(False)
            else:
                if self.pH < self.pHSelect:
                    #print(f'Smaller then = True')
                    self.status_signal.emit(True)
                else:
                    if self.should_start:
                        self.pump_signal.emit(False)
                    else:
                        pass
                    self.status_signal.emit(False)                        
                    #print(f'Smaller then = False')
            
            QCoreApplication.processEvents()
            time.sleep(0.1)
            
    
    def update_pH(self, data, number):
        self.pH = data
    
    def update_select(self,select):
        self.select = select
    
    def update_pH_select(self, pHSelect):
        self.pHSelect = pHSelect
    
    def stop(self):
        self.is_running = False

    

    

class USBWorker(QObject):
    update_usb = pyqtSignal(bool, object)
    
    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        # Background task logic
        while self.is_running:
        
            self.monitor_usb()
            
            time.sleep(1)  # Adjust the sleep time as needed

    def stop(self):
        self.is_running = False
    
    def monitor_usb(self):
        context = Context()
        data = []
        for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
            properties = device.properties
            if ('ID_BUS' in properties and properties['ID_BUS'] == 'usb'
            and 'ID_FS_TYPE' in properties
            and 'ID_USB_DRIVER' in properties
            and properties['ID_USB_DRIVER'] == 'usb-storage'): #and self.Log_file.get():
                data.append(True)
            else:
                data.append(False)
        if True in data:
            self.path = self.mount_device()
            self.update_usb.emit(True, self.path)  # Emit signal with a boolean and data

            
        else:
            self.update_usb.emit(False,"")            
          
    def mount_device(self):
        context = Context()
    
        removable = [device for device in context.list_devices(subssystem='block', DEVTYPE='disk') if device.attributes.asstring('removable')=="1"]
        partition = []
        for device in removable:
            partitions = [device.device_node for device in device.parent.children if 'ID_FS_TYPE' in device.properties]
        
            if partitions:
                partition = partitions[0]

                result = subprocess.run(['findmnt', '-n', '-o', 'TARGET', partition], stdout=subprocess.PIPE, text=True)
                mount_point = result.stdout.strip()
            
                if mount_point:
                    return mount_point