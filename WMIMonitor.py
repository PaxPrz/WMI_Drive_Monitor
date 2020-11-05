try:
    from logicaldisk import LogicalDiskCreation, LogicalDiskModification, LogicalDiskEjection, LogicalDiskOperation
    from pnpentity import WPDCreation, WPDModification, WPDEjection, WPDOperation
except ImportError:
    from .logicaldisk import LogicalDiskCreation, LogicalDiskModification, LogicalDiskEjection, LogicalDiskOperation
    from .pnpentity import WPDCreation, WPDModification, WPDEjection, WPDOperation

if __name__ == "__main__":
    import logging
    import argparse
    import sys
    from threading import Thread
    
    CHOICES = ['create','modify','delete','operation']
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description="Tracks USB Storage activity: Thread based implementation")
    parser.add_argument('-l', '--logical-drive', action="store_true", help="Keep track of Logical Removable Device")
    parser.add_argument('-p', '--portable-device', action="store_true", help="Keep track of Windows Portable Devices")
    parser.add_argument('-o', '--options', nargs='+', choices=CHOICES, help="Choose multiple notification to listen on. Defaults to all")
    args = parser.parse_args()
    
    LOGICAL = {
        'create': LogicalDiskCreation,
        'modify': LogicalDiskModification,
        'delete': LogicalDiskEjection,
        'operation': LogicalDiskOperation
    }
    
    PNP = {
        'create': WPDCreation,
        'modify': WPDModification,
        'delete': WPDEjection,
        'operation': WPDOperation
    }
    
    headers = []
    workers = []
    if args.logical_drive:
        headers.append(LOGICAL)
        logging.debug("Listening for Logical Drives")
    if args.portable_device:
        headers.append(PNP)
        logging.debug("Listening for Portable Devices")
    if not headers:
        logging.error("Must listen to atleast one of '--logical-drive' or '--portable-device'")
        sys.exit(0)
    for h in headers:
        if args.options:
            logging.debug(f"Listening to {args.options}")
            for o in args.options:
                workers.append(h[o]())
        else:
            logging.debug(f"Listening to all options: {CHOICES}")
            for o in CHOICES:
                workers.append(h[o]())
    logging.debug("Starting Watcher\n")
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
    logging.debug("Closing Watcher")
    

