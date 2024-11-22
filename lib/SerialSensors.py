# SerialSensors.py
from SerialDevice import SerialDevice

import serial
import os
import sys
folder_path = os.path.abspath(os.path.join('..', 'tms'))
sys.path.append(folder_path)

from hortilite.Sensors import Sensor

class SerialSensor(Sensor):
    """ Class for sensors using serial communication (RS485, RS232 etc.).
    """
    
    def __init__(self, device:SerialDevice=None, num=1, name="SerialSensor", read_size=1,
                 write_db=False, write_local=False,
                 file_dir="sensors/", file_name="sensor", param_details=None, testing=False, *args, **kwargs):
        
        super().__init__(device=device, num=num,
                         name=name, read_size=read_size,
                         write_db=write_db, write_local=write_local,
                         file_dir=file_dir, file_name=file_name, param_details=param_details, testing=testing, *args, **kwargs)
        
        
        if not self.testing:
            ##link encode-decode functions to SerialDevice
            self._device._encode = self.__encode
            self._device._decode = self.__decode
    
    ########################
    #  for overriding
    ########################
    @staticmethod
    def __encode(val):
        ##function to encode values in device
        return val
    
    @staticmethod
    def __decode(val):
        return val
     
    ########################
    #  class methods
    ########################
    @classmethod
    def from_port(cls, serial_device: SerialDevice, *args, **kwargs):
        """Instantiate SerialSensor class from an exisiting SerialDevice object.

        Parameters
        ----------
        serial_device : SerialDevice
            Serial port interface object

        Returns
        -------
        :class: `SerialSensor`
            SerialSensor class instance
        """
        return cls(device=serial_device, *args, **kwargs)
    
    @classmethod
    def init_port(cls, port_name, baudRate=9600, parity=serial.PARITY_NONE, stopBits=serial.STOPBITS_ONE,
                  byteSize=serial.EIGHTBITS, timeOut=None, testing=False, *args, **kwargs):
        """Instantiate SerialSensor class by creating a SerialDevice object for specified port name.

        See :class: `SerialDevice` for port parameters
            
        Parameters
        ----------
        port_name : str
            Name of serial communication port
        testing : bool, optional
            Whether to run the sensor object under testing mode, by default False

        Returns
        -------
        :class: `SerialSensor`
            SerialSensor class instance
        """
        in_port = SerialDevice.init_port(port_name, baudRate=baudRate, parity=parity, stopBits=stopBits,
                               byteSize=byteSize, timeOut=timeOut, testing=testing)
        return cls(device=in_port, *args, **kwargs)
    
    ########################
    #  serial utils
    ########################
    def set_auto_reconnect(self, a: bool):
        """Set whether to turn on auto-connection function in SerialDevice

        Parameters
        ----------
        a : bool
            Whether to turn on auto-connection function in SerialDevice

        Returns
        -------
        bool
            Auto-connection status
        """
        self._device.auto_reconnect = a
        return self._device.auto_reconnect
    
    def _write_read(self, instruction, ret_sent=False):
        """Write data to and read response from serial device. 

        Encoding-decoding is carried out in SerialDevice class.

        Parameters
        ----------
        instruction : str or bytes
            Data to be sent to serial device
        ret_sent : bool, optional
            Whether to check the matching reply from sensor, by default False

        Returns
        -------
        str or bytes
            Sensor response

        Raises
        ------
        ValueError
            When instruction and returned data mismathed
        NameError
            When serial device is not found
        """        
        try:
            print("getting response")
            response = self._device._write_read(instruction, size=self._read_size)
            ##check signals received similar to sent if required
            print(response)
            print(ret_sent)
            if ret_sent:
                if response == instruction:
                    return response
                else:
                    raise ValueError("check signal! sent:{}; received:{}".format(instruction, response))
            else:
                return response
            
        except NameError:
            raise NameError('Device Not Found. Check connection.')

    def _trigger(self, update_stat=False, update_latest=False, update_bool=False):
        """Trigger acquisition of SerialSensor

        Parameters
        ----------
        update_stat : bool, optional
            Whether to update status labels binded to the objects, by default False
        update_latest : bool, optional
            Whether to update latest datetime label, see :meth: `_update_latest_label`, by default False
        update_bool : bool, optional
            Whether to run binded function takeing status of data as input, by default False

        Returns
        -------
        tuple or list
            Data from sensor
        """
        ##send data to device and get response
        print("getting res")
        res = self._write_read(self._dev_addr)
        
        ##update status labels
        for i, key in enumerate(self.param_details.keys()):
            if update_stat:                
                self._update_stat_labels(key, res[i])
        
        ##update latest datetime label
        if update_latest:
            self._update_latest_label()
            
        ##run binded function takeing status of data as input
        if update_bool:
            cur_stat = True
            for x in res:
                if x is None:
                    cur_stat = False
                    break
            self._update_bool(cur_stat)
        
        ##write data to local file
        if self._write_local:
            self._write_file(res)
        
        ##write data to database
        if self._write_db and (not self.db is None):
            ##input to database by passing only data, datetime stamp will be auto generated
            self.db.input_from_data(self.tab_name, res, auto_time=True)
            
        print("res obtained")
        return res 

class SoilSensor(SerialSensor):
    """ `JXCT 7 in 1 Soil`_ sensor
        
        RS485 RTU Modbus device.
        
        .. warning:: !!Hardcopy manual available with some mistakes from vendor.
        
        .. _JXCT 7 in 1 Soil:
            http://www.jxct-iot.com/product/showproduct.php?id=197
    """
    
    def __init__(self, device=None, num=1, *args, **kwargs):
        self._device = device
        self._dev_addr = num
        self._name = "SoilSensor"
        self._read_size = 13  ##read 13 bytes
        
        # Param details for sensor readings
        self.param_details = {"Temperature": [float, r"$^\circ$C", 0, 60],
                              "Moisture": [float, "%RH", 0, 100],
                              "pH": [float, "", 0, 14],
                              "EC": [float, r"$\mu$S/cm", 0, 100000], 
                              "N": [int, "mg/kg", 0, 100000],  
                              "P": [int, "mg/kg", 0, 100000],  
                              "K": [int, "mg/kg", 0, 100000]}  
        
        # Command references for triggering readings
        self.__trig_ref = {
            'Temperature': [[0x03, 0x00, 0x13, 0x00, 0x01], 10, "degC"],
            'Moisture': [[0x03, 0x00, 0x12, 0x00, 0x01], 10, "%RH"],
            'pH': [[0x03, 0x00, 0x06, 0x00, 0x01], 100, ""],
            'EC': [[0x03, 0x00, 0x15, 0x00, 0x01], 1, "us/cm"],
            'N': [[0x03, 0x00, 0x1e, 0x00, 0x01], 1, "mg/kg"],
            'P': [[0x03, 0x00, 0x1f, 0x00, 0x01], 1, "mg/kg"],
            'K': [[0x03, 0x00, 0x20, 0x00, 0x01], 1, "mg/kg"]
        }

        
        super().__init__(device=self._device, num=self._dev_addr,
                         name=self._name, read_size=self._read_size,
                         param_details=self.param_details, *args, **kwargs)

