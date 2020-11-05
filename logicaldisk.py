import logging
import wmi
from threading import Thread, current_thread, main_thread
import pythoncom
from contextlib import suppress
try:
    from utils.helpers import convert_bytes
    from core.functions import get_WMI_consumer
    from utils.constants import TIMEOUT_CYCLE, DRIVE_TYPE
except ImportError:
    from .utils.helpers import convert_bytes
    from .core.functions import get_WMI_consumer
    from .utils.constants import TIMEOUT_CYCLE, DRIVE_TYPE

class LogicalDiskWatcher:
    '''
        An abstract watcher class that watches for changes in Logical Disk using windows WMI
    '''
    def __init__(self, mode: str, only_removable:bool=True, timeout_in_ms:int=TIMEOUT_CYCLE)-> "LogicalDiskWatcher":
        self._mode = mode
        self._destruct = False
        self._timeout = timeout_in_ms
        self._all_disks = []
        self._only_removable = only_removable
        self._kword={}
        if self._only_removable:
            self._kword.update({"DriveType":"2"})
        #logging.info(f"Created {self._mode}")
        
    def _create_watcher(self):
        '''
            Creates a watcher object and stores it as instance property
        '''
        self._my_c = get_WMI_consumer()
        self.disk_watcher = self._my_c.Win32_LogicalDisk.watch_for(self._mode, **self._kword)
        
    def start_watching(self):
        '''
            A method to run in thread, that watch for event until timeout and loops back again
            If KeyboardInterrupt or other exception occurs, the module gets destroyed
            Notification is only printed if drive_type is removable for only_removable=True            
        '''
        if not current_thread() is main_thread():
            pythoncom.CoInitialize()
        try:
            self._create_watcher()
            while not self._destruct:
                try:
                    response = self.disk_watcher(timeout_ms=self._timeout)
                except KeyboardInterrupt:
                    self.destroy()
                except wmi.x_wmi_timed_out:
                    continue
                except Exception as e:
                    logging.error(f"Exception coming from here\n {e}")
                    self.destroy()
                else:
                    drive_type = -1
                    with suppress(AttributeError):
                        drive_type = int(response.DriveType)
                    if self._only_removable and not drive_type == 2:
                        continue
                    self._show_notification(response)
        finally:
            if not current_thread() is main_thread():
                pythoncom.CoUninitialize()
                
    def destroy(self):
        '''
            Destroys the loop and stops watching for the specific element
        '''
        self._destruct = True
    
    def _show_notification(self, response: wmi._wmi_event):
        '''
            Notification method to be defined by the inherited classes
            
            Args:
                response (_wmi_event): A WMI event object
        '''
        pass
        
    
class LogicalDiskCreation(LogicalDiskWatcher):
    '''
        The instance of this class tracks for USB drive Insertion
    '''
    def __init__(self, only_removable=True):
        super().__init__(mode="creation", only_removable=only_removable)
    
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''New Disk Inserted
            Drive Letter: {response.Caption}
            Description: {response.Description}
            Volume Name: {response.VolumeName}
            Drive Type: {DRIVE_TYPE.get(str(response.DriveType), "Unknown")}
            Size: {convert_bytes(response.Size)}
            Free Space: {convert_bytes(response.FreeSpace)}
            Volume Serial Number: {response.VolumeSerialNumber}
        ''')
    
class LogicalDiskModification(LogicalDiskWatcher):
    '''
        The instance of this class tracks file being copied to drive or deleted from it
    '''
    def __init__(self, only_removable=True):
        super().__init__(mode="modification", only_removable=only_removable)
        
    def _show_notification(self, response: wmi._wmi_event):
        volume_changed = int(response.previous.FreeSpace) - int(response.FreeSpace)
        text = "File Size Added"
        if volume_changed < 0:
            text = "File Size Freed"
            volume_changed = -volume_changed
        logging.info(f'''Drive Modified
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
            {text}: {convert_bytes(volume_changed)}
        ''')
        
class LogicalDiskEjection(LogicalDiskWatcher):
    '''
        The instance of this class tracks drive being ejected
    '''
    def __init__(self, only_removable=True):
        super().__init__(mode="deletion", only_removable=only_removable)
        
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''Drive Ejected
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
        ''')
        
class LogicalDiskOperation(LogicalDiskWatcher):
    '''
        The instance of this class track any operation performed on the drive
    '''
    def __init__(self, only_removable=True):
        super().__init__(mode="operation", only_removable=only_removable)
        
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''Drive Operation
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
        ''')

if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug('''Starting up watcher
        Press 'q' to Quit!
    ''')
    workers = LogicalDiskCreation(), LogicalDiskEjection(), LogicalDiskModification()#, LogicalDiskOperation()
    threads = []
    for w in workers:
        t = Thread(target=w.start_watching)
        t.start()
        threads.append(t)
    while True:
        try:
            q = input("")
        except KeyboardInterrupt:
            q = 'q'
        if q in ('q','Q'):
            for w in workers:
                w.destroy()
            break
    for t in threads:
        t.join()
    logging.debug('''Closing Watcher''')
    