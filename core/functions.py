import wmi
from typing import Union, List
from contextlib import suppress

def get_WMI_consumer()-> wmi._wmi_namespace:
    return wmi.WMI()

def get_logical_disks(c: wmi._wmi_namespace)-> List[wmi._wmi_object]:
    try:
        return c.Win32_LogicalDisk()
    except:
        logging.error("Cannot fetch Logical Disks")
        return []

def get_removable_disks(d: Union[wmi._wmi_namespace, List[wmi._wmi_object]])-> List[wmi._wmi_object]:
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