
import os

if "CCP4" not in os.environ.keys(): 
    msg = "Cannot find CCP4 root directory"
    raise RuntimeError(msg)

__all__ = ["AMPLE_DIR", "SHARE_DIR"]

# AMPLE source code directory
AMPLE_DIR = os.path.join(os.environ["CCP4"], "lib", "py2", "ample")
# AMPLE share data directory
SHARE_DIR = os.path.join(os.environ["CCP4"], "share", "ample")