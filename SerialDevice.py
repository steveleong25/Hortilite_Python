"""Base class to interface serial communication
"""
import serial
import time
import platform
if platform.machine() in ['armv7l']:
    serial_prefix = "/dev/"
else:    
    serial_prefix = "\\\\.\\"

class SerialDevice(object):
    """Base class to interface serial communication
    
    Features::
    
        Encoding, decoding of data
        Write to and read from device

    Parameters
    ----------
    object : Python object
        Base object
    """
    def __init__(self, port: serial.Serial, port_name=None, testing=False, auto_reconnect=False, verbose=False):  
        """Instantiate Serial Device
            default timeout=None --> wait forever

        Parameters
        ----------
        port : serial.Serial
            pySerial object
        port_name : str, optional
            Port name of serial object, by default None
        testing : bool, optional
            Whether to run the class in testing mode, by default False
        auto_reconnect : bool, optional
            Whether to run reconnection when found broken, by default False
        verbose : bool, optional
            Execution verbosity, by default False

        Raises
        ------
        ValueError
            When string or others is passed for serial port object
        """
        self._device = port
        self._port_name = port_name
        self._testing = testing
        self._auto_reconnect = auto_reconnect
        self._verbose = verbose
        
        if self._testing:
            if self._verbose:
                print("Serial device in testing mode")
            self._device = None  ##force to testing mode
        
        ###for testing
        if self._device is None:
            if self._verbose:
                print("a fake port")
        else:
            if not isinstance(self._device, serial.Serial):
                if type(self._device) == str:
                    raise ValueError("not a serial port object. use .init_port")
                else:
                    raise ValueError("not a serial port object")
            else:
                self.initialize()
                time.sleep(2)  ##!!important to wait device to be responsive
        
    def __repr__(self):
        if self._testing:
            return "Fake SerialDevice"
        out = []
        for x in ["name", "baudrate", "bytesize", "stopbits", "parity", "timeout"]:
            out.append(str(self._device.__getattribute__(x)))
        return "SerialDevice({})".format("-".join(out))   
    
    @classmethod
    def from_port(cls, port:serial.Serial, testing=False, *args, **kwargs):
        if testing:
            return cls(None, port_name=None, testing=testing, *args, **kwargs)
        return cls(port, port_name=port.name, *args, **kwargs)
    
    @classmethod
    def init_port(cls, port_name, baudRate=9600, parity=serial.PARITY_NONE, stopBits=serial.STOPBITS_ONE,
                 byteSize=serial.EIGHTBITS, timeOut=None, testing=False, *args, **kwargs):
        ##default timeout wait forever
        if testing:
            return cls(None, port_name=port_name, testing=testing, *args, **kwargs)
        
        if not serial_prefix in port_name:
            to_open = serial_prefix+port_name 
        else:
            to_open = port_name
        try:
            this_port = serial.Serial(port=to_open,baudrate=baudRate,
                                      parity=parity, stopbits=stopBits,
                                      bytesize=byteSize, timeout=timeOut)  ##timeout in seconds, important to flow control
        except IOError:
            raise IOError("failed to initialize device port at {}".format(port_name))
        except ValueError:
            raise ValueError("Parameter are out of range, e.g. baud rate, data bits. at {}".format(port_name))
        except Exception as e:  ##do not throw error
            print("Error", e)
        else:
            return cls(this_port, port_name=port_name, *args, **kwargs)
    
    @property
    def port_name(self):
        return self._port_name
    
    @property
    def auto_reconnect(self):
        return self._auto_reconnect
    
    @auto_reconnect.setter
    def auto_reconnect(self, a:bool):
        self._auto_reconnect = a
        if self._verbose:
            if a:
                print("device auto-reconnection turn ON")
            else:
                print("device auto-reconnection turn OFF")
    
    @staticmethod
    def _encode(val):  ##for overriding
        return val
    @staticmethod
    def _decode(val):  ##for overriding
        return val
    
    def initialize(self):
        """Reset port buffers and internal status boolean
        """
        self._device.reset_input_buffer()
        self._device.reset_output_buffer()
        self._device_error = False
    
    def connect(self):
        """Open port object
        """
        self._device.open()
    
    def disconnect(self):
        """Close port object
        """
        try:
            self._device.close()
        except Exception as e:
            if self._verbose:
                print("Error", e)
        else:
            if self._verbose:
                print("Disconnect ", self.__repr__())
        finally:
            old_device = self._device
            self._device = None   
            del old_device  ##discard the device anyways
        
    def _write_read(self, instruction, size=None, sleep=0, 
                    reset=True, reset_out=True, reset_in=True, check=False):
        """Write to and read by size from port

        Parameters
        ----------
        instruction : str or bytes
            data to be written to port
        size : int ot None, optional
            number of byte to be read from port after write command, by default None
            If specified, read from port
        sleep : int, optional
            Duration in seconds to delay after writing to port , by default 0
        reset : bool, optional
            Whether to reset input and output buffer, by default True
            If True, force reset_out and reset_in to True
        reset_out : bool, optional
            Whether to reset buffers before writing to port, by default True
        reset_in : bool, optional
            Whether to reset input buffer after reading from port, by default True
        check : bool, optional
            Whether to check matching reply after writing to port, by default False

        Returns
        -------
        str or bytes or None
            Data read from port if any
        """
        if reset:  ##retain compatible with older version
            reset_out = True
            reset_in = True
        if not self._device is None:
            ret = self._write(instruction, sleep=sleep, reset=reset_out, check=check)
            if check:
                if ret is None:
                    return None
            if not size is None:
                return self._read(size, reset=reset_in)
            else:
                return None
        
    def _write(self, instruction, sleep=0, reset=True, check=False, reset_check=False, force_timeout=None):
        """Write to port

        Parameters
        ----------
        instruction : str or bytes
            Data to be written to port
        sleep : int, optional
            Duration in seconds to delay after writing to port, by default 0
        reset : bool, optional
            Whether to reset buffers before writing to port, by default True
        check : bool, optional
            Whether to check matching reply after writing to port, by default False
        reset_check : bool, optional
            Whether to reset input buffer after checking matching reply from port after writing, by default False
        force_timeout : _type_, optional
            Duration in seconds to force break of write or read actions, useful when port is in blocking mode, by default None

        Returns
        -------
        str or byte or None
            If write is successful, return matching reply if any
            Else, None
        """
        if not self._device is None:
            if reset:
                self._device.reset_input_buffer()
                self._device.reset_output_buffer()  ##discard output buffer
            to_send = self._encode(instruction)
            if self._verbose:
                print("write", instruction.hex(), to_send.hex())
            try:
                self._device.write(to_send)
            except Exception as e:
                if self._verbose:
                    print("Serial write error " + str(e))
                self._device_error = True
            else:
                time.sleep(sleep)
                if self._verbose:
                    print("done")
                if check: 
                    if force_timeout:  ##time sleep to break in seconds
                        ret = None
                        start = time.time()
                        while (time.time() - start) < force_timeout:
                            ##check if there's data to read
                            if self._device.in_waiting >= len(to_send):
                                ret = self._device.read(len(to_send))
                                if self._verbose:
                                    print("read before timeout", ret)
                                break
                        if self._verbose:
                            print("read timeout")
                    else:
                        ret = self._device.read(len(to_send))
                    if reset_check:
                        self._device.reset_input_buffer()
                    if self._verbose:
                        print("check", ret)
                    if ret == to_send:
                        return self._decode(ret)
                    else:
                        return None
                else:
                    return None

        if self._device_error:  ##execute reconnection if failed
            print("force reconnection")
            self.reconnect()
            return None
        
    def _read(self, size, sleep=0, reset=True, decode=True, force_timeout=None):
        """Read specific bytes from port

        Parameters
        ----------
        size : int
            Number of byte to be read from port
        sleep : int, optional
            Duration in seconds to delay before reading from port, by default 0
        reset : bool, optional
            Whether to reset input buffer after reading from port, by default True
        decode : bool, optional
            Whether to execute decode function on received data, by default True
        force_timeout : _type_, optional
            Duration in seconds to force break of write or read actions, useful when port is in blocking mode, by default None

        Returns
        -------
        str or bytes or None
            If data received and decoded sucesssully
            Else, None
        """
        if not self._device is None:  ##not reading if size is None
            time.sleep(sleep)
            ret = None
            try:
                if force_timeout:  ##time sleep to break in seconds
                    start = time.time()
                    while (time.time() - start) < force_timeout:
                        ##check if there's data to read
                        if self._device.in_waiting >= size:
                            ret = self._device.read(size)
                            if self._verbose:
                                print("read before timeout", ret)
                            break
                    if self._verbose:
                        print("read timeout")
                else:
                    ret = self._device.read(size)
            except Exception as e:
                if self._verbose:
                    print("Serial read error " + str(e))
                self._device_error = True
            else:
                if self._verbose:
                    print("read", size, ret.hex())
                if not ret is None:
                    if len(ret) > 0:
                        if decode:
                            response = self._decode(ret)
                        else:
                            response = ret
                        if reset:
                            self._device.reset_input_buffer()  ##discard input buffer
                        return response
                    else:  ##read failed
                        if self._auto_reconnect:  ##execute reconnection if failed
                            if self._device_error:  ##execute reconnection if failed
                                print("force reconnection")
                                self.reconnect()
                        return None
                else:  ##read failed
                    if self._auto_reconnect:  ##execute reconnection if failed
                        if self._device_error:  ##execute reconnection if failed
                            print("force reconnection")
                            self.reconnect()
                    return None
    
    def _read_while(self, sleep=0, sleep_inner=0, reset=False, decode=True):
        """Read from port by one byte at a time while data available

        Parameters
        ----------
        sleep : int, optional
            Duration in seconds to delay before start reading from port, by default 0
        sleep_inner : int, optional
            Duration in seconds to delay before reading each byte from port, by default 0
        reset : bool, optional
            Whether to reset input buffer after finish reading, by default False
        decode : bool, optional
            Whether to execute decode function on received data, by default True

        Returns
        -------
        str or bytes or None
            If data received and decoded sucesssully
            Else, None
        """
        time.sleep(sleep)
        out = None
        while self._device.in_waiting:
            if out is None:
                out = self._read(1, sleep=sleep_inner, reset=False, decode=False)
            else:
                out += self._read(1, sleep=sleep_inner, reset=False, decode=False)

        if reset:
            self._device.reset_input_buffer()  ##discard input buffer

        ##accum only decode
        if decode:
            return self._decode(out)
        else:
            return out
    
    def reconnect(self, trials=3):
        """Reconnect to port and retry by a number of trials

        Returns
        -------
        bool or None
            if reconnection is successful, True
            Else, None
        """
        ## TODO: check difference for converter and RS232 port
        ## connected directly
            ## force reconnect
        ## connected with intermediate converter
            ## but which connection? signal converter or the device unresponsive?
            ## if it's signal converter, need to make new object / clear buffer etc. given the port name is locked
            ## if it's device, just wait until it responses??
        ##obtain current port settings
        prop = {x: self._device.__dict__["_"+x]for x in ["baudrate", "parity", "stopbits", "bytesize", "timeout"]}
        self.disconnect()
        time.sleep(2)
        if not serial_prefix in self._port_name:
            to_open = serial_prefix + self._port_name 
        else:
            to_open = self._port_name
        self._device = serial.Serial(port=to_open,**prop)
        j = trials
        while (self._device is None) and j > 0:
            if self._verbose:
                print("retry serial connection", trials-j)
            self.disconnect()
            time.sleep(2)
            self._device = serial.Serial(port=to_open,**prop)
            j -= 1
            
            if not self._device is None:
                break
        if self._device is None:   ##after retry also fail then pass None, handle at higher levels
            return None
        else:
            self._device_error = False
            return True
    
    def write_read(self, *args, **kwargs):
        """Write to and read from port
        """
        return self._write_read(*args, **kwargs)
    
    def write(self, *args, **kwargs):
        """Write to port
        """
        return self._write(*args, **kwargs)
    
    def read(self, *args, **kwargs):
        """Read specific bytes from port
        """
        return self._read(*args, **kwargs)
    
    def read_while(self, *args, **kwargs):
        """Read from port by one byte at a time while data available
        """
        return self._read_while(*args, **kwargs)
       