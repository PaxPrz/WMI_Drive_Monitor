import wmi
from typing import Union

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