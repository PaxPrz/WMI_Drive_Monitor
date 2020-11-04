import wmi
from typing import List, Any, Union
import logging
from contextlib import suppress
from threading import Thread
import sys
import time
import pythoncom

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        
def convert_bytes(size):
    if isinstance(size, str):
        size = float(size)
    for x in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
    return str(size)

DRIVE_TYPE = {
    '2' : "Removable Disk",
    '3' : "Fixed Local Disk",
    '4' : "Network Disk",
    '5' : "Compact Disk",
}

def get_WMI_consumer()-> wmi._wmi_namespace:
    return wmi.WMI()

wmi_consumer = get_WMI_consumer()

def get_logical_disks(c: wmi._wmi_namespace)-> List[wmi._wmi_object]:
    try:
        return c.Win32_LogicalDisk()
    except:
        return []

def get_removable_disks(d: Union[wmi._wmi_namespace, List[wmi._wmi_object]])-> List[wmi._wmi_object]:
    removable_disks = []
    if not isinstance(d, (list, tuple, set)):
        try:
            d = d.Win32_LogicalDisk()
        except:
            d = []
    for drive in d:
        try:
            if drive.DriveType == 2:
                removable_disks.append(drive)
        except AttributeError:
            logging.error(f"DriveType cannot be fetched for {self.drive_letter}")
    return removable_disks

class Drive:
    def __init__(self, drive: wmi._wmi_object)-> "Drive":
        self.drive = drive
        self.drive_letter = Drive.get_drive_letter(drive)

    def __str__(self):
        return f"{self.drive_letter} Drive"
    
    @staticmethod
    def get_drive_letter(drive: wmi._wmi_object)-> str:
        drive_letter = "-"
        with suppress(AttributeError):
            drive_letter = drive.Caption
        return drive_letter

    def get_drive_size(self)-> Union[int, None]:
        try:
            size = self.drive.Size
            size = int(size)
        except AttributeError:
            logging.error(f"Size cannot be fetched for {self.drive_letter}")
            return None
        except ValueError:
            pass
        return size
            
    def get_free_space(self)-> Union[int, None]:
        try:
            free_size = self.drive.FreeSpace
            free_size = int(free_size)
        except AttributeError:
            logging.error(f"Free space cannot be fetched for {self.drive_letter}")
            return None
        except ValueError:
            pass
        return free_size
                
    def get_drive_description(self)-> Union[str, None]:
        try:
            description = self.drive.Description
        except AttributeError:
            logging.error(f"Description cannot be fetched for {self.drive_letter}")
            return None
        return description
    
    def get_volume_serial_number(self)-> Union[str, None]:
        try:
            volume_serial_number = self.drive.VolumeSerialNumber
        except AttributeError:
            logging.error(f"Volume Serial Number cannot be fetched for {self.drive_letter}")
            return None
        return VolumeSerialNumber
    
    def get_volume_name(self)-> Union[str, None]:
        try:
            volume_name = self.drive.VolumeName
        except AttributeError:
            logging.error(f"Volume Name cannot be fetched for {self.drive_letter}")
            return None
        return volume_name
    
    def get_file_system(self)-> Union[str, None]:
        try:
            file_system = self.drive.FileSystem
        except AttributeError:
            logging.error(f"File System cannot be fetched for {self.drive_letter}")
            return None
        return FileSystem
    
class LogicalDiskWatcher(Thread):
    def __init__(self, mode: str, timeout_in_ms=1000)-> "LogicalDiskWatcher":
        Thread.__init__(self)
        self._my_c = wmi.WMI()
        self._mode = mode
        self._destruct = False
        self._timeout = timeout_in_ms
        self._all_disks = []
        self._only_removable = True
        logging.info(f"Created {self._mode}")
        
    def _create_watcher(self):
        self.disk_watcher = self._my_c.Win32_LogicalDisk.watch_for(self._mode)
        
    def start_watching(self):
        while True:
            try:
                response = self.disk_watcher(timeout_ms=self._timeout)
            except KeyboardInterrupt:
                self._destruct = True
                break
            except wmi.x_wmi_timed_out:
                if self._destruct:
                    break
                #print('sleep')
                #time.sleep(10) #to be removed
                #print('wakeup')
                continue
            except Exception as e:
                logging.error(f"Exception coming from here\n {e}")
                sys.exit(-1)
                continue
            else:
                drive_type = -1
                with suppress(AttributeError):
                    drive_type = int(response.DriveType)
                if self._only_removable and not drive_type == 2:
                    continue
                self._show_notification(response)
    
    def destroy(self):
        self._destruct = True
    
    def _show_notification(self, response: wmi._wmi_event):
        pass
    
    def run(self):
        logging.info(f'''Starting {self.__class__.__name__}''')
        #pythoncom.CoInitialize()
        self._create_watcher()
        self.start_watching()
        #pythoncom.CoUninitialize()
        
    
class LogicalDiskCreation(LogicalDiskWatcher):
    def __init__(self, only_removable=True):
        super().__init__(mode="creation")
        self._only_removable = only_removable
        #self._create_watcher()
    
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
        super().__init__(mode="modification")
        self._only_removable = only_removable
        self._create_watcher()
        
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''Drive Modified
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
        
        ''')
        
class LogicalDiskEjection(LogicalDiskWatcher):
    def __init__(self, only_removable=True):
        super().__init__(mode="deletion")
        self._only_removable = only_removable
        self._create_watcher()
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''Drive Ejected
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
        ''')
        
class LogicalDiskOperation(LogicalDiskWatcher):
    def __init__(self, only_removable=True):
        super().__init__(mode="operation")
        self._only_removable = True
        self._create_watcher()
        
    def _show_notification(self, response: wmi._wmi_event):
        logging.info(f'''Drive Operation
            Drive Letter: {response.Caption}
            Volume Name: {response.VolumeName}
        ''')

if __name__=="__main__":
    logging.debug('''Starting up watcher
        Press 'q' to Quit!
    ''')
    #e = LogicalDiskEjection()
    #e.start_watching()
    #sys.exit()
    workers = (LogicalDiskCreation(),)# LogicalDiskEjection()#, LogicalDiskModification()#, LogicalDiskOperation()
    for w in workers:
    #    t = Thread(target=w.start_watching)
        w.start()
    #    threads.append(t)
    while True:
        q = input("")
        if q in ('q','Q'):
            for w in workers:
                w.destroy()
            break
    for t in workers:
        t.join()
    logging.debug('''Closing Watcher''')
    