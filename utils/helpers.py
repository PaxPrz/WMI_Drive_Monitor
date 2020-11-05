from typing import Union

def convert_bytes(size: Union[str,int,float]):
    '''
        Convert a byte representation to Human Readable format
        
        Args:
            size (str/int/float): Size in bytes e.g. 1024
         
        Returns:
            str: Human Readable size e.g. "1KB"
    '''
    if isinstance(size, str):
        size = float(size)
    for x in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.2f %s" % (size, x)
        size /= 1024.0
    return str(size)