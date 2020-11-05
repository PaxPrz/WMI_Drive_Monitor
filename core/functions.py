import wmi
from typing import Union, List
from contextlib import suppress

def get_WMI_consumer()-> wmi._wmi_namespace:
    '''
        Returns WMI Namespace
        
        Returns:
            Returns WMI Namespace object
    '''
    return wmi.WMI()

def get_logical_disks(c: wmi._wmi_namespace)-> List[wmi._wmi_object]:
    '''
        Gets LogicalDisk of the system

        Args:
            c (wmi._wmi_namespace): Namespace Object
            
        Returns:
            List[wmi._wmi_object]: List of _wmi_object (represents Logical Disk)
    '''
    try:
        return c.Win32_LogicalDisk()
    except:
        logging.error("Cannot fetch Logical Disks")
        return []

def get_removable_disks(d: Union[wmi._wmi_namespace, List[wmi._wmi_object]])-> List[wmi._wmi_object]:
    '''
        Gets Removable Disks of the system
        
        Args:
            d (_wmi_namespace or List[_wmi_object]): If List is provided, removable objects are sorted out
            
        Returns:
            List[wmi._wmi_object]: List of removable drive WMI Object 
    '''
    removable_disks = []
    if not isinstance(d, (list, tuple, set)):
        try:
            removable_disks = d.Win32_LogicalDisk(DriveType="2")
        except:
            logging.error(f"Cannot Fetch Removable Disks")
    else:
        for drive in d:
            with suppress(AttributeError):
                drive_type = drive.DriveType
                if drive_type == "2":
                    removable_disks.append(drive)
    return removable_disks