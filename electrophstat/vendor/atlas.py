import io
import fcntl

class atlas_i2c:
    
    long_timeout = 1.5
    short_timeout = .3
    default_bus = 1
    #default_address = 100 #ORP
    
    #102 RTD
    #98 ORP
    
    def __init__(self,address, bus = default_bus):
        self.file_read = io.open("/dev/i2c-" +str(bus),"rb",buffering = 0)
        self.file_write = io.open("/dev/i2c-" +str(bus),"wb", buffering = 0)
        self.set_i2c_address(address)
    
    def set_i2c_address(self, addr):
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, addr)
    
    def write(self, string):
        string +="\00"
        self.file_write.write(string.encode('utf-8'))
    
    def read(self, num_of_bytes = 31):
        res = self.file_read.read(num_of_bytes).decode('utf-8').replace('\x00', '').replace('\x01', '') 
       
        return res
    
    def query(self,string):
        self.write(string)
        
        #if((string.upper().startswith("R")) or
        #   (string.upper().startswith("CAL"))):
        #    querytimer = time.time() + long_timeout
        #    #time.sleep(self.long_timeout)
        #else:
        #    querytimer = time.time() + short_timeout
            #time.sleep(self.short_timeout)
        #if querytimer < time.time():
        #return self.read()
    def close(self):
        self.file_read.close()
        self.file_write.close()

#Creating the GUI

#Creating the main GUI
