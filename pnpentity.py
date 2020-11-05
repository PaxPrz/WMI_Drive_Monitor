import wmi
import logging
from threading import Thread, current_thread, main_thread
import pythoncom
try:
    from core.functions import get_WMI_consumer
    from utils.constants import TIMEOUT_CYCLE
except ImportError:
    from .core.functions import get_WMI_consumer
    from .utils.constants import TIMEOUT_CYCLE

class WPD:
    '''
        An abstract watcher class that watches for changes in Portable Device using windows WMI
    '''
    def __init__(self, mode:str, timeout_ms:int =TIMEOUT_CYCLE):
        self._mode = mode
        self._destruct = False
        self._timeout_in_ms = timeout_ms
        self._kword = {"PNPClass": "WPD"}
        
    def _create_watcher(self):
        '''
            Creates a watcher object and stores it as instance property
        '''
        self._my_c = get_WMI_consumer()
        self.pnp_watcher = self._my_c.Win32_PnPEntity.watch_for(self._mode, **self._kword)
    
    def start_watching(self):
        '''
            A method to run in thread, that watch for event until timeout and loops again
            If KeyboardInterrupt or other exception occurs, the module gets destroyed            
        '''        
        if not current_thread() is main_thread():
            pythoncom.CoInitialize()
        try:
            self._create_watcher()
            while not self._destruct:
                try:
                    response = self.pnp_watcher(timeout_ms=self._timeout_in_ms)
                except KeyboardInterrupt:
                    self.destroy()
                except wmi.x_wmi_timed_out:
                    continue
                except Exception as e:
                    logging.error(f"Exception coming from here\n {e}")
                    self.destroy()
                else:
                    self._show_notification(response)
        finally:
            if not current_thread() is main_thread():
                pythoncom.CoUninitialize()
    
    def destroy(self):
        '''
            Destroys the loop and stops watching for the specific element
        '''
        self._destruct = True
        
    def _show_notification(self, response:wmi._wmi_event):
        '''
            Notification method to be defined by the inherited classes
            
            Args:
                response (_wmi_event): A WMI event object
        '''
        pass
    
class WPDCreation(WPD):
    '''
        The instance of this class tracks for Portable Device Insertion
    '''
    def __init__(self):
        super().__init__(mode="creation")
        
    def _show_notification(self, response:wmi._wmi_event):
        logging.info(f'''Portable Device Connected
            Manufacturer: {response.Manufacturer}
            Name: {response.Name}
            Description: {response.Description}
            PnP Device ID: {response.PnPDeviceID}
        ''')
        
class WPDModification(WPD):
    '''
        The instance of this class tracks for modification. Doesn't track file transfer or delete.
    '''
    def __init__(self):
        super().__init__(mode="modification")
    
    def _show_notification(self, response:wmi._wmi_event):
        logging.info(f'''Portable Device Modification
            Name: {response.Name}
            PnP Device ID: {response.PnPDeviceID}
        ''')
        
class WPDEjection(WPD):
    '''
        The instance of this class tracks for Portable Device Ejection
    '''
    def __init__(self):
        super().__init__(mode="deletion")
    
    def _show_notification(self, response:wmi._wmi_event):
        logging.info(f'''Portable Device Ejected
            Manufacturer: {response.Manufacturer}
            Name: {response.Name}
            PnP Device ID: {response.PnPDeviceID}
        ''')
        
class WPDOperation(WPD):
    '''
        The instance of this class tracks for Portable Device operation
    '''
    def __init__(self):
        super().__init__(mode="operation")
    
    def _show_notification(self, response:wmi._wmi_event):
        logging.info(f'''Portable Device Operation
            Name: {response.Name}
            PnP Device ID: {response.PnPDeviceID}
        ''')

    
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug('''Starting up WPD watcher
        Press 'q' to Quit
    ''')
    workers = WPDCreation(), WPDModification(), WPDEjection() #, WPDOperation()
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
    logging.debug('''Stopping WPD watcher''')
    