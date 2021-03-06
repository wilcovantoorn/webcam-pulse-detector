from lib.device import Camera, ipCamera
from lib.processors import findFaceGetPulse
from lib.interface import plotXY, imshow, waitKey,destroyWindow, moveWindow, resize
import numpy as np      


class getPulseApp(object):
    """
    Python application that finds a face in a webcam stream, then isolates the
    forehead.
    
    Then the average green-light intensity in the forehead region is gathered 
    over time, and the detected person's pulse is estimated.
    """
    def __init__(self, ip, user, password):
        #Imaging device - must be a connected camera (not an ip camera or mjpeg
        #stream)
        
        self.camera = ipCamera(ip,
                       user=user, 
                       password=password)
        self.w,self.h = 0,0
        
        #Containerized analysis of recieved image frames (an openMDAO assembly)
        #is defined next.
        
        #This assembly is designed to handle all image & signal analysis,
        #such as face detection, forehead isolation, time series collection,
        #heart-beat detection, etc. 
        
        #Basically, everything that isn't communication
        #to the camera device or part of the GUI
        self.processor = findFaceGetPulse(bpm_limits = [50,160],
                                          data_spike_limit = 25.,
                                          face_detector_smoothness = 10.)  
        
        #Init parameters for the cardiac data plot
        self.bpm_plot = False
        self.plot_title = "Cardiac info - raw signal, filtered signal, and PSD"
        
        #Maps keystrokes to specified methods
        #(A GUI window must have focus for these to work)
        self.key_controls = {"s" : self.toggle_search,
                        "d" : self.toggle_display_plot}
        
    
    def toggle_search(self):
        """
        Toggles a motion lock on the processor's face detection component.
        
        Locking the forehead location in place significantly improves
        data quality, once a forehead has been sucessfully isolated. 
        """
        state = self.processor.find_faces.toggle()
        print "face detection lock =",not state
    
    def toggle_display_plot(self):
        """
        Toggles the data display.
        """
        if self.bpm_plot:
            print "bpm plot disabled"
            self.bpm_plot = False
            destroyWindow(self.plot_title)
        else:
            print "bpm plot enabled"
            self.bpm_plot = True
            self.make_bpm_plot()
            moveWindow(self.plot_title, self.w,0)
    
    def make_bpm_plot(self):
        """
        Creates and/or updates the data display
        """
        plotXY([[self.processor.fft.times, 
                 self.processor.fft.samples],
            [self.processor.fft.even_times[4:-4], 
             self.processor.measure_heart.filtered[4:-4]],
                [self.processor.measure_heart.freqs, 
                 self.processor.measure_heart.fft]], 
               labels = [False, False, True],
               showmax = [False,False, "bpm"], 
               label_ndigits = [0,0,0],
               showmax_digits = [0,0,1],
               skip = [3,3,4],
               name = self.plot_title, 
               bg = self.processor.grab_faces.slices[0])
    
    def key_handler(self):    
        """
        Handle keystrokes, as set at the bottom of __init__()
        
        A plotting or camera frame window must have focus for keypresses to be
        detected.
        """
        pressed = waitKey(10) & 255 #wait for keypress for 10 ms
        if pressed == 27: #exit program on 'esc'
            quit()
        for key in self.key_controls.keys():
            if chr(pressed) == key:
                self.key_controls[key]()
                
    def main_loop(self):
        """
        Single iteration of the application's main loop.
        """
        # Get current image frame from the camera
        frame = self.camera.get_frame()
        self.h,self.w,_c = frame.shape
        
        #display unaltered frame
        #imshow("Original",frame)
        
        #set current image frame to the processor's input
        self.processor.frame_in = frame
        #process the image frame to perform all needed analysis
        self.processor.run()
        #collect the output frame for display
        output_frame = self.processor.frame_out
        
        #show the processed/annotated output frame
        
        output_frame = resize(output_frame, (640,480))
        imshow("Processed",output_frame)
        
        #create and/or update the raw data display if needed
        if self.bpm_plot:
            self.make_bpm_plot()
        
        #handle any key presses
        self.key_handler()

if __name__ == "__main__":
    # example (replace these values)
    url = "http://1.1.1.1/frame.jpg"
    user = "admin"
    password = "12345"
    App = getPulseApp(url,
                      user, 
                      password)
    while True:
        App.main_loop()
        
        
