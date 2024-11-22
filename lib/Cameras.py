"""Camera classes.

    Notes
    -----
        If device is found to be other than RaspberryPi:
            RaspberryPiCamera, MultiRaspberryPiCamera, MultiRaspberryPiCamera_cv will return None
"""
import os
import sys
import traceback
import time
import cv2
import numpy as np
import PySide2.QtCore as qtcore

import platform
if platform.machine() in ['armv7l']:
    import RPi.GPIO as gp
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    
from hortilite.HikRobotCameras import HikRobotCamera, hik_MV_FRAME_OUT_INFO_EX

##******* for compatability ********##
##CameraLoopWorker - moved to PySideThreads
from hortilite.GUI.PySideThreads import LoopWorker as CameraLoopWorker, Worker as CameraWorker

class Camera(object):
    """ Base class for cameras to standardize common calls using various camera
    
    Notes
    -----
    General sequence to capture from a camera::
    
        1. Connect camera
        2. Start camera stream
        3. Capture from stream
        4. Stop camera stream
        5. Disconnect camera

    """
    def __init__(self, dev_addr: int=None, 
                 img_width: int=None, img_height: int=None,
                 metadata: dict=None, verbose: bool=False, testing: bool=False, *args, **kwargs):
        """Instantiate Camera

        Notes
        -----
        ``._initialize`` method is called upon instantiation

        Parameters
        ----------
        dev_addr : int, optional
            Device address --> Index of camera within its group; i.e. among cameras of same model, by default None
        img_width : int, optional
            Camera resolution width (pixel), by default None
        img_height : int, optional
            Camera resolution height (pixel), by default None
        metadata : dict, optional
            Metadata, by default None
        verbose : bool, optional
            Execution verbosity, by default False
        testing : bool, optional
            Whether to run camara object under testing mode, by default False
        """
        ##passed
        self._dev_addr = dev_addr
        self._img_width = img_width
        self._img_height = img_height
        self._metadata = metadata
        self._verbose = verbose
        self._testing = testing
        
        ##internal
        self.cam = None
        self.cam_stream = None  ##a stream object (PiRGBArray) to store captured frames
        self._connected = False
        self._streaming = False  ##remain False
        
        self._initialize()
    
    ################
    # utils
    ################
    def get_dev_addr(self):
        """Returns camera device address

        Returns
        -------
        int
            Device addresss
        """
        return self._dev_addr
    
    def get_img_size(self):
        """Returns camera resolution/image size in pixels

        Returns
        -------
        tuple
            (width, heigh)
        """
        return self._img_width, self._img_height
    
    def get_metadata(self):
        """Returns camera metadata

        Returns
        -------
        dict
            Metadata
        """
        return self._metadata
    
    @staticmethod
    def _encode_png(imageData):
        """Encode image data from 3-D BGR numpy array to PNG format in bytes

        Notes
        -----
            Display image as QtWidget.Label requries encoding to PNG format
            Conversion using cv.imencode function `[ref]`_
            

        Parameters
        ----------
        imageData : 3-D BGR numpy Array
            image data stored in numpy array

        Returns
        -------
        bytes or None
            encoded image if successful else None
            
        .. _[ref]:
            https://stackoverflow.com/questions/50630045/how-to-turn-numpy-array-image-to-bytes
        """        
        ##encode BGR numpy array to png bytes
        ret, encoded = cv2.imencode(".png", imageData)  
        if ret:
            return encoded.tobytes()  ##png_encoded bytes
        else:
            return None
    
    ###########################
    # for overriding
    ###########################
    def __repr__(self):
        return "Camera object addr: {}".format(self._dev_addr)
    
    def _connect(self):
        """Establish camera connection. For overriding in child.
        """
        pass

    def _initialize(self):
        """Initialize camera, settings etc. For overriding in child.
        """
        pass
    
    def _close(self):
        """Disconnect camera. For overriding in child.
        """
        pass
    
    def _stream(self):
        """Start camera stream. For overriding in child.
        """
        pass
    
    def _stop(self):
        """Stop camera stream. For overriding in child.
        """
        pass
    
    def _capture_one(self, encode=False):
        """Capture one frame from camera stream. ##commonly RGB/BGR 3-channel 8-bit image
        For overriding in child.

        Parameters
        ----------
        encode : bool, optional
            Whether to encode output image, by default False
        
        Returns
        -------
        3-D numpy Array or bytes
            Image
        """
        pass
    
    ###############
    # public
    ###############
    def connected(self):
        """Returns camera connection status

        Returns
        -------
        bool
            True if connected, False if disconnected
        """
        return self._connected

    def streaming(self):
        """Returns camera stream status

        Returns
        -------
        bool
            True if stream is started, False if stream is stopped
        """
        ##boolean state for camera stream connection
        return self._streaming

    def connect(self):
        """Establish camera connection. See :meth: `_connect`
        """
        self._connect()
        
    def initialize(self):
        """Initialize camera, settings etc. See :meth: `_initialize`
        """
        self._initialize()
    
    def close(self):
        """Disconnect camera. See :meth: `_close`
        """
        self._close()
        
    def stream(self):
        """Start camera stream. See :meth: `_stream`
        """
        self._stream()
    
    def stop(self):
        """Stop camera stream. See :meth: `_stop`
        """
        self._stop()
    
    def capture_one(self, encode=False):
        """Capture one frame from camera stream. See :meth: `_capture_one`
        """
        return self._capture_one(encode=encode)

class MultiCamera(Camera):
    """Subclass of :class: `Camera` to handle multiple channels in single instance
    """
    def __init__(self, dev_channel=None, channels=None, *args, **kwargs):
        """Instantiate MultiCamera

        Parameters
        ----------
        dev_channel : int or str, optional
            Default channel, by default None
        channels : list or tuple, optional
            List of channels for the camera, by default None

        Notes
        -----
            If `channels` is not specified, the camera channel list returns [dev_channel]

        Raises
        ------
        Exception
            When both `dev_channel` and `channels` are not specified
        """
        self._channels = channels
        self._dev_channel = dev_channel
        
        if self._dev_channel is None:
            if self._channels is None:
                raise Exception("No channels specified for {}".format(self.__repr__()))
            else:
                self._dev_channel = self._channels[0]
        super(MultiCamera, self).__init__(*args, **kwargs)
        
    def __repr__(self):
        return "MultiCamera object addr: {} channels{}".format(self._dev_addr, self._channels)
    
    def _switch_cam(self, dev_cahnnel):
        """Switch to camera channel. For overriding in child.
        """
        pass

    def switch_cam(self, dev_channel):
        """Switch to camera channel. See :meth: `_switch_cam`
        """
        return self._switch_cam(dev_channel)
        
    def get_dev_channel(self):
        """Returns current device channel

        Returns
        -------
        int or str
            Current device channel
        """
        return self._dev_channel
                 
###########################
# HIKROBOT
########################### 
class HIKROBOTCamera(Camera):
    """Subclass for HIKROBOT cameras.

    Requires custom wrapper around .dll/.so --> HikRobotCameras.py in MvImport_win / MvImport_armhf
    """    
    def __init__(self, ip_addr: str=None, load_settings=False, retry=True, *args, **kwargs):
        """Instantiate HIKROBOTCamera.

            **Only for GigE HIKROBOT cameras**
            
            TODO: implement for USB interface

        Parameters
        ----------
        ip_addr : str, optional
            IP address, by default None
        load_settings : bool, optional
            Whether to load default user settings upon initialization, by default False
        retry : bool, optional
            Whether to attempt re-connection when connection broken, by default True
        """
        self._ip_addr = ip_addr
        self._load_settings = load_settings
        self._retry = retry  ##avoid throwing errors in connection and streaming, keep retrying in .stream() call
        
        super().__init__(*args, **kwargs)
        
    def __repr__(self):
        return "HIKROBOT camera @ {}; Device {}".format(self._ip_addr, self._dev_addr)
    
    ########################################
    ## public functions for trigger mode
    ########################################
    def set_trigger_mode(self, *args, **kwargs):
        """Set HIKROBOT camera trigger mode. See `set_trigger_mode` in wrapper class

        Raises
        ------
        Exception
            When camera is not connected
        """
        if not self.cam is None:
            return self.cam.set_trigger_mode(*args, **kwargs)
        else:
            raise Exception("Set trigger mode failed. Camera not connected")
    
    def set_callback(self, *args, **kwargs):
        """Set HIKROBOT camera callback function. See `set_callback` in wrapper class

        Raises
        ------
        Exception
            When camera is not connected
        """
        if not self.cam is None:
            return self.cam.set_callback(*args, **kwargs)
        else:
            raise Exception("Set callback. Camera not connected")
    
    ############
    ## override
    ############
    def _connect(self):
        """Establish HIKROBOT camera connection.
            ``initialize`` is called here.

        Raises
        ------
        Exception
            When error occurs during connection
        """
        if self._testing:
            return
        if not self._connected:
            try:
                #initialize camera
                self.cam = HikRobotCamera(cam_ip=self._ip_addr)
                #initialize camera
                self.cam.initialize()   
            except Exception as e:  ##ensure not to throw error
                self.cam = None
                self._connected = False
                self._streaming = False
                raise Exception("Error in connection " + str(e)) from e
            else:
                self._connected = True
                self._streaming = False
            
    def _close(self):
        """Disconnect HIKROBOT camera

        Raises
        ------
        Exception
            When error occurs during disconnection
        """
        if self._testing:
            return
        if self._streaming:
            self._stop()
        try:
            self.cam.close()
        except Exception as e:
            raise Exception("Error during closing " + str(e)) from e
        else:
            old_cam = self.cam
            self.cam = None
            del old_cam
            self._streaming = False
            self._connected = False
    
    def _initialize(self):
        """Initialize camera, settings etc.
        This sequence is skipped if `testing` is True
        """
        if self._testing:
            return
        self._connect()
        if self._connected and self._load_settings:
            ##user settings
            if self._verbose:
                print("Load settings")
            self._user_settings()
            
    def _user_settings(self):
        """Apply default user settings to HIKROBOT camera:
            See ``default_user_settings`` in wrapper class
        """
        self.cam.enable_func()
        self.cam.default_user_settings()
        self.cam.disable_auto()
        self.cam.disable_func()
        ##self.cam.enable_auto()
        if self._verbose:
            self.cam.details()
    
    def _reconnect(self, trials=3, sleep=2):
        """Attempt reconnection --> close and initialize

        Parameters
        ----------
        trials : int, optional
            Number of trails to attempt, by default 3
        sleep : int, optional
            Duration in seconds in between trials, by default 2
        """
        def _attempt():
            try:
                ##retry
                self._close()
                time.sleep(sleep)
                self._initialize()
            except Exception as e:
                if self._verbose:
                    print(str(e))

        j = trials
        while (not self._connected) and j > 0:
            if self._verbose:
                print("retry connection", trials-j)
            _attempt()
            if self._connected:
                break
            j -= 1
    
    def _stream(self):    ##stream will propagate o execute connect a few times if exception is raised
        """Start HIKROBOT camera stream.

        Raises
        ------
        Exception
            When error occurs during streaming
        """
        if self._testing:
            return
        ##call to stream
        if not self._streaming:
            try:
                self.cam.stream()
            except Exception as e:
                self._streaming = False
                self._connected = False
                if self._retry:
                    if self._verbose:
                        print("Error during streaming", e)
                    self._reconnect()
                else:
                    raise Exception("Error during streaming " + str(e)) from e
            else:
                time.sleep(0.1)
                self._streaming = True
    
    def _stop(self):
        """Stop camera stream.

        Raises
        ------
        Exception
            When error occurs during stopping stream
        """
        if self._testing:
            return
        ##call to stop
        if self._streaming:
            try:
                self.cam.stop()
            except Exception as e:
                raise Exception("Error during stopping " + str(e)) from e
            else:
                time.sleep(0.1)
                self._streaming = False
            
    def _capture_one(self, encode=False):
        """Capture one frame from camera stream.

        Parameters
        ----------
        encode : bool, optional
            Whether to encode image, by default False

        Returns
        -------
        numpy.ndarray or bytes or None
            BGR numpy.ndarray if `encoded` is False, bytes if `encoded` is True, else None

        Raises
        ------
        Exception
            When error occurs during acquisition
        """
        ##return numpy array
        if self._testing:
            return
        if self._streaming:
            try:
                image = self.cam.capture()
                if encode:
                    return self._encode_png(image)
                else:
                    return image
            except Exception as e:
                raise Exception("error during capture " + str(e)) from e
                return None
        else:
            return None

if not platform.machine() in ['armv7l']:
    RaspberryPiCamera, MultiRaspberryPiCamera, MultiRaspberryPiCamera_cv = None, None, None
else:
    ###########################
    # RaspberryPi Camera
    ########################### 
    class RaspberryPiCamera(Camera):
        """Subclass of Camera for a single Raspi Camera. 
            
            Requires picamera package

        Notes
        -----
            PiCamera object are to be closed everytime to ensure sufficient resources. 
            Program will fail upon failure to do so. 
            To ensure continuous operation in Qt, exceptions are not propogated to higher level.

        """    
        def __init__(self, *args, **kwargs):
            """Instantiate RaspberryPiCamera. See :class: `Camera` for parameters
            """
            super().__init__(*args, **kwargs)
            
        def __repr__(self):
            return "RaspPiCam camera Device {}".format(self._dev_addr)
            
        def _connect(self):
            """Establish PiCamera camera connection.
            """
            if self._testing:
                return
            if not self._connected:
                try:
                    #initialize camera
                    self.cam = PiCamera()
                    self.cam.resolution = (self._img_width, self._img_height)
                    self.cam_stream = PiRGBArray(self.cam)
                except Exception as e:
                    if self._verbose:
                        print("Error during connecting",e)
                    self.cam = None
                    self.cam_stream = None
                    self._connected = False
                else:
                    #initialize camera
                    self._connected = True
        
        def _close(self):
            """Disconnect PiCamera camera.
            """
            if self._testing:
                return
            if self._connected:
                try:
                    self.cam.close()
                except Exception as e:
                    if self._verbose:
                        print("Error during streaming", e)
                else:
                    self.cam = None
                    self.cam_stream = None
                    self._streaming = False
                    self._connected = False
        
        def _initialize(self):
            """Initialize PiCamera camera. :meth: `_connect` is called here.
                Connect to camera if `testing` is False, else do nothing.
            """
            if self._testing:
                return
            self._connect()
                
        def _capture_one(self, encode=False):
            """Capture one frame from PiCamera camera stream.

            Parameters
            ----------
            encode : bool, optional
            Whether to encode image, by default False

            Returns
            -------
            numpy.ndarray or bytes or None
                BGR numpy.ndarray if `encoded` is False, bytes if `encoded` is True, else None
            """
            if self._testing:
                return
            ##return numpy array
            if self._streaming:
                try:
                    self.cam.capture(self.cam_stream, format="bgr")
                    ##IMPORTANT !!!! clear stream for next frame
                    self.cam_stream.truncate(0)
                    image = self.cam_stream.array
                    if encode:
                        return self._encode_png(image)
                    else:
                        return image
                except Exception as e:
                    if self._verbose:
                        print("Error during capture", e)
                    return None
            else:
                return None
            
    ###########################
    # MultiRaspberryPiCamera
    ###########################
    class MultiRaspberryPiCamera(MultiCamera):
        """ Subclass of MultiCamera for up to 4 Raspi cameras using ArduCAM Multi Camera Adapter v2.2
            and picamera package

        Notes
        -----
            `Product details`_
            `User guide`_
            `Code reference`_

            Acquisition using picamera package::
            
                * Switching using I2C channel values and GPIO outputs
                * Instances of PiCamera and corresponding PiRGBArray are to be instantiated everytime upon switching
                **Preceeding instances must be closed/cleared to avoid out of resources conditions
            
            [pseudo flow]::
                - disconnect any existing instances
                - switch I2C channel and GPIO outputs
                - instantiate new instances
                - capture
                - disconnect current instances
                - repeat

            *Tested working with Raspberry Pi HQ camera v1.0 2018.
            SONY IMX477 sensor, 12MP (max. 4056px x 3040 px resolution)
            `Raspberry Pi HQ camera`_
        
            Using picamera package::
            
            Raspberry Pi camera resolution constraint when using unencoded formats (RGB, BGR, YUV etc)
            --we're using still port here
            --buffer from camera ISP has fixed size (hardware settings) that
            --required width to be multiples of 32 or 16, height to be multiples of 16
            --see: 'raw_resolution' in picamera.array.py
        
            To avoid 'Incorrect buffer length error' in bytes_to_rgb in picamera.array.py
            specifying suitable resolutions::
            
                --To check, use (x+31) & ~31; (y+15) & ~15
                `Official picamra package resource on hardware <https://picamera.readthedocs.io/en/release-1.13/fov.html>`
                **Sensor modes for HQ camera is unclear
                --Full FoV and non-binning modes are at ratio 4:3
                --for V1: 2592x1944; for V2: 3280x2464
        
            `Official Raspberry Pi hardware documentation`_
            Camera details::
                
                HQ camera has sensor image area 6.287mm x 4.712 mm (7.9mm diagonal)
                which has ratio approx. 4:3 (need to use this to take advantage of full FoV)
                for full height 3040px, width by ratio should be 4053.33 px
                -->(x+31) & ~31 gives width=4064 (> max), so we deduct 32, width=4032
                ....
                Therefore: 
                --Some allowed shapes:
                Default ratio by width [(4032, 3024), (2048, 1536), (1024, 768)]
                Default ratio by height [(4032, 3040), (2048, 1520), (1024, 768)]
                SD by width by height (640, 480) (640, 480)
                HD by width by height (1280, 720) (1280, 720)
                Full HD by width by height (1920, 1088) (1952, 1088)
                2K by width by height (2560, 1440) (2560, 1440)
                4K by width by height (3488, 2176) (3488, 2160)
                TODO: test and confirm above shapes
            
        .. _Product details:
            https://www.arducam.com/product/multi-camera-v2-1-adapter-raspberry-pi/
        .. _User guide:
            https://www.uctronics.com/download/Amazon/B0120.pdf
        .. _Code reference:
            https://github.com/ArduCAM/RaspberryPi
        .. _Raspberry Pi HQ camera:
            https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/
        .. _Official Raspberry Pi hardware documentation:
            https://www.raspberrypi.com/documentation/accessories/camera.html#hardware-specification
        """
        
        def __init__(self, channels=["A", "B", "C", "D"], *args, **kwargs):
            """Instantiate MultiRaspberryPiCamera

            Parameters
            ----------
            channels : list, optional
                List of avaialable channels, by default ["A", "B", "C", "D"]
            """

            self.switch_gpio = [7, 11, 12]
            ##I2c command line
            ##i2cset -y [i2cbus] [chip-address] [data-address] [value]
            ##https://www.abelectronics.co.uk/kb/article/1092/i2c-part-3---i-c-tools-in-linux
            self.adapter_info = {"A":{"i2c_cmd":"i2cset -y 1 0x70 0x00 0x04",
                                      "gpio_sta":[0,0,1]},
                                 "B":{"i2c_cmd":"i2cset -y 1 0x70 0x00 0x05",
                                      "gpio_sta":[1,0,1]},
                                 "C":{"i2c_cmd":"i2cset -y 1 0x70 0x00 0x06",
                                      "gpio_sta":[0,1,0]},
                                 "D":{"i2c_cmd":"i2cset -y 1 0x70 0x00 0x07",
                                      "gpio_sta":[1,1,0]}}
            
            super().__init__(channels=channels, *args, **kwargs)
            
            ##trigger to ensure i2c is on
            ret = os.popen("i2cdetect -y 1").read()
            if self._verbose:
                print(ret)
            
        def __repr__(self):
            return "RaspPiCam camera Device picamera backend {}".format(self._dev_addr)
            
        def _connect(self):
            """Establish PiCamera camera connection.
                If `testing` is True, returns None.
            """
            if self._testing:
                return
            if not self._connected:
                try:
                    #initialize camera
                    self.cam = PiCamera(resolution=(self._img_width, self._img_height))
                    time.sleep(0.5)
                    self.cam_stream = PiRGBArray(self.cam)
                except Exception as e:
                    if self._verbose:
                        print("Exception during connecting", e)  ##silenced
                    self.cam = None
                    self.cam_stream = None
                    self._connected = False
                    self._streaming = False
                else:
                    self._connected = True
                    self._streaming = False
        
        def _close(self):
            """Disconnect PiCamera camera.
                If ``testing`` is True, returns None.

            Raises
            ------
            Exception
                When error occurs during closing connection
            """
            if self._testing:
                return
            if self._connected:
                try:
                    if not self.cam is None:
                        self.cam.close()
                except Exception as e:
                    if self._verbose:
                        print("Error during closing", e)
                    raise Exception("Error during closing " + str(e)) from e  ##trying to close something non-existence
                else:
                    self.cam = None
                    self.cam_stream = None
                    self._streaming = False
                    self._connected = False
        
        def _init_gpio(self):
            """Initilaize Raspberry Pi GPIO for I2C trigger for camera adapter.
                If ``testing`` is True, returns None.
            """
            if self._testing:
                return
            gp.setwarnings(False)
            gp.setmode(gp.BOARD)
            gp.setup(7, gp.OUT)
            gp.setup(11, gp.OUT)
            gp.setup(12, gp.OUT)
            ##initial [X, 1, 1] = no camera
            gp.output(11, True)
            gp.output(12, True)
        
        def _initialize(self):
            """Initialize camera (trigger I2C, switch to default channel).
                If ``testing`` is True, returns None.
            """
            if self._testing:
                return
            self._init_gpio()  ##initialize GPIO pins mod        
            self._switch_cam(self._dev_channel)  ##switch to default channel and connect

        def _switch_cam(self, dev_channel, init=True, rest=0.5):
            """Switch to camera channel.
                If ``testing`` is True, returns None.

            Parameters
            ----------
            dev_channel : string
                Channel to switch to eg. "A", "B", "C", "D"
            init : bool, optional
                Whether to instantiate new instances, by default True
            rest : float, optional
                Time sleep in between switching in seconds, by default 0.5

            Returns
            -------
            bool
                True when swithing is successful, else False

            Raises
            ------
            Exception
                When PiCamera or PiRGBArray stream is not initialized
            """    
            if self._testing:
                return

            if dev_channel in self._channels:
                state = False    
                try:
                    if init:
                        self._close()
                        time.sleep(rest)
                    
                    if not self._testing:
                        ret = os.popen(self.adapter_info[dev_channel]["i2c_cmd"]).read()  ##returned value can be use to indicate error
                        for i in range(len(self.switch_gpio)):
                            gp.output(self.switch_gpio[i], bool(self.adapter_info[dev_channel]["gpio_sta"][i]))
                        time.sleep(rest)
                    
                    if init:  ##initialize new PiCamera object
                        self._connect()
                        # print("cam", self.cam)
                        # print("cam_stream", self.cam_stream)
                        
                except Exception as e:
                    if self._verbose:
                        print("Exception during switching", e)
                    self._close()
                    raise Exception(e)
                else:
                    self._dev_channel = dev_channel
                    state = True
                    if self._verbose:
                        print("Switch to {}".format(self.__dev_channel))
                finally:
                    if self.cam is None:
                        raise Exception("PiCamera instance not initialized")
                    elif self.cam_stream is None:
                        raise Exception("PiCamera RGBArray stream not initialized")
                    return state

        def _stream(self):
            """Do nothing. Camera stream handled by internal PiRGBArray stream.
            """
            pass
        
        def _stop_capture(self):
            """Do nothing. Camera stream handled by internal PiRGBArray stream.
            """
            pass
                
        def _capture_one(self, encode=False):
            """ Capture one frame from camera PiRGBArray stream.
                If ``testing`` is True, returns None

            Parameters
            ----------
            encode : bool, optional
                Whether to encode image data into png format bytes, by default False

            Returns
            -------
            3-D BGR numpy Array or bytes
                image data
            """
            if self._testing:
                return
            
            if self._connected:
                image = None
                try:
                    self.cam.capture(self.cam_stream, format="bgr")
                    image = self.cam_stream.array
                    ##IMPORTANT !!!! clear stream for next frame
                    self.cam_stream.truncate(0)
                    
                except Exception as e:
                    raise Exception("Exception during streaming " + str(e)) from e
                    return None
                else:
                    if not image is None:
                        if encode:
                            return self._encode_png(image)
                        else:
                            return image
                    else:
                        return None
                finally:
                    del image
            else:
                self._streaming = False
                return None

    ###########################
    # MultiRaspberryPiCamera_cv
    ###########################
    class MultiRaspberryPiCamera_cv(MultiRaspberryPiCamera):
        """ Subclass of MultiRaspberryPiCamera that uses OpenCV package to handle camera streams. 
            See more in :class: `MultiRaspberryPiCamera`.

            *Tested working with `Raspberry Pi v1.3 5MP cameras <https://uk.pi-supply.com/products/raspberry-pi-camera-board-v1-3-5mp-1080p>`
        """
        
        def __init__(self, *args, **kwargs):
            """Instantiate MultiRaspberryPiCamera_cv
            See :class: `MultiRaspberryPiCamera` for parameters
            """
            super().__init__(*args, **kwargs)
                
        def __repr__(self):
            return "RaspPiCam camera Device OpenCV backend {}".format(self._dev_addr)
            
        def _connect(self):
            """Establish camera connection via OpenCV VideoCapture.
                If `testing` is True, returns None

            Raises
            ------
            Exception
                _description_
            """
            if self._testing:
                return
            if not self._connected:
                try:
                    #initialize camera
                    self.cam = cv2.VideoCapture(-1)
                    time.sleep(1)
                    self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                    self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self._img_width)
                    self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self._img_height)
                except Eception as e:
                    self.cam.release()
                    self.cam = None
                    self._connected = False
                    raise Exception("Exception during connecting " + str(e)) from e
                else:
                    #initialize camera
                    self._connected = True
        
        def _close(self):
            """Disconnect camera (release OpenCV resources).
                If ``testing`` is True, returns None
            """
            if self._testing:
                return
            if self._connected:
                try:
                    self.cam.release()
                except Exception as e:
                    if self._verbose:
                        print("Exception: during closing", e)
                else:
                    self.cam = None
                    self._streaming = False
                    self._connected = False
        
        def _initialize(self):
            """Initialize camera (trigger I2C, switch to default channel).
                If ``testing`` is True, returns None
            """
            if self._testing:
                return
            self._init_gpio()  ##initialize GPIO pins mode
            self._connect()
            
            checks = []
            for chn in self._channels:
                os.system(self.adapter_info[chn]["i2c_cmd"])
                for i in range(len(self.switch_gpio)):
                    gp.output(self.switch_gpio[i], bool(self.adapter_info[chn]["gpio_sta"][i]))
                ret, frame = self.cam.read()
                checks.append(ret)
                time.sleep(1)
            self._close()  ##release right after checking
        
            self._switch_cam(self._dev_channel)  ##switch to default channel and connect      
                
        def _capture_one(self, encode=False):
            """ Capture one frame from OpenCV video stream.
                If ``testing`` is True, returns None

            Parameters
            ----------
            encode : bool, optional
                Whether to encode image data into png format bytes, by default False

            Returns
            -------
            3-D BGR numpy Array or bytes
                Image data
            """
            if self._testing:
                return
            if self._connected:
                ##return numpy array
                try:
                    self.cam.grab()
                    ret, image = self.cam.read()
                    image.dtype=np.uint8
                    if encode:
                        return self._encode_png(image)
                    else:
                        return image
                    
                except Exception as e:
                    if self._verbose:
                        print("Exception during capture", e)
                    return None
            else:
                return None
            
def calc_picamera():
    """Utility to calculate suitable resolution for PiCamera.

        TODO: verify computed resolutions on hardware
    """
    def calc(x, y):
        return (x + (y - 1)) & ~(y - 1)

    def calc_compatible(side, ratio, max_width, max_height):
        if ratio >= 1:  ##width side
            side = calc(side, 16)
            while (side > max_height):
                side -= 16
            other = int(side * ratio)
            other = calc(other, 32)
            if other > max_width:
                other -= 32
            if other > max_width:  ##if matching width still exceed limit
                return None
            return (other, side)
        else:  ##height side
            side = calc(side, 32)
            while (side > max_width):
                side -= 32
            other = int(side * ratio)
            other = calc(other, 16)
            if other > max_height:
                other -= 16
            if other > max_height:  ##if matching height still exceed limit
                return None
            return (side, other)

    def get_compatible_list(max_width, max_height, follow="w", ratio=None):
        assert follow in ["w", "h"]
        if follow == "w":
            max_side = max_width
            if ratio is None:
                ratio = max_height/max_width
        else:
            max_side = max_height
            if ratio is None:
                ratio = max_width/max_height
        
        out = []
        for i in range(3):  ##up to 8 times smaller
            side = max_side // (2 ** i)
            out.append(calc_compatible(side, ratio, max_width, max_height))
        
        return out, ratio


    ##Example for RaspberryPi HQ camera
    max_width = 4056
    max_height = 3040
    
    print("By width, default ratio")
    print(get_compatible_list(max_width, max_height, follow="w")[0])
    print("By width, 4:3 ratio")
    print(get_compatible_list(max_width, max_height, follow="w", ratio=3/4)[0])
    print("By width, 16:9 ratio")
    print(get_compatible_list(max_width, max_height, follow="w", ratio=9/16)[0])
    print("By height, default ratio")
    print(get_compatible_list(max_width, max_height, follow="h")[0])
    print("By height, 4:3 ratio")
    print(get_compatible_list(max_width, max_height, follow="h", ratio=4/3)[0])
    print("By height, 16:9 ratio")
    print(get_compatible_list(max_width, max_height, follow="h", ratio=16/9)[0])

    print("common resolution")
    for name, x, y in [("SD", 640, 480),
                       ("HD", 1280, 720),
                       ("Full HD", 1920, 1080),
                       ("2K", 2560, 1440),
                       ("4K", 3480, 2160),
                       ("8K", 7680, 4320)]:
        print(name, "by width", "by height")
        print(calc_compatible(x, y/x, max_width, max_height),
              calc_compatible(y, x/y, max_width, max_height))