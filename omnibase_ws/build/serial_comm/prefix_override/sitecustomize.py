import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/roger/Github/home-electronics/omnibase_ws/install/serial_comm'
