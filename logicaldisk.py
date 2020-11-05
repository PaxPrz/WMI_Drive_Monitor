import logging
import wmi
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
        self._my_c = get_WMI_consumer()
        self.disk_watcher = self._my_c.Win32_LogicalDisk.watch_for(self._mode, **self._kword)
        
    def start_watching(self):
        self._create_watcher()
        while not self._destruct:
            try:
                response = self.disk_watcher(timeout_ms=self._timeout)
            except KeyboardInterrupt:
                self.destroy()
            except wmi.x_wmi_timed_out:
                yield
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
                #yield
                
    def destroy(self):
        self._destruct = True
    
    def _show_notification(self, response: wmi._wmi_event):
        pass
        
    
class LogicalDiskCreation(LogicalDiskWatcher):
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
    def __init__(self, only_removable=True):
        super().__init__(mode="deletion", only_removable=only_removable)
        
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''Drive Ejected
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
        ''')
        
class LogicalDiskOperation(LogicalDiskWatcher):
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
    gens = [x.start_watching() for x in workers]
    while True:
        try:
            for w in gens:
                next(w)
        except (KeyboardInterrupt, StopIteration):
            break
    logging.debug('''Closing Watcher''')
    