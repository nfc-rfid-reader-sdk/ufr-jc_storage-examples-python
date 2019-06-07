import ctypes
from ctypes import c_ubyte
def initialize():
    #JCDL_AIDs
    global DL_AID_RID_PLUS
    DL_AID_RID_PLUS = "\xF0" + "DLogic"
    global DL_SIGNER_PIX 
    DL_SIGNER_PIX = "\x00\x01"
    global DL_STORAGE_PIX
    DL_STORAGE_PIX  = "\x01\x01"
    global DL_SIGNER_AID
    DL_SIGNER_AID = DL_AID_RID_PLUS + DL_SIGNER_PIX 
    global DL_STORAGE_AID
    DL_STORAGE_AID = "\xF0" + "DLogic" + "\x01\x01"
    global DL_SIGNER_AID_SIZE
    DL_SIGNER_AID_SIZE = c_ubyte(9)
    global DL_STORAGE_AID_SIZE 
    DL_STORAGE_AID_SIZE = c_ubyte(9)

    #JCDLStorage constants:
    global JC_DL_STORAGE_MAX_FILES
    JC_DL_STORAGE_MAX_FILES = 16
    global JC_DL_STORAGE_MAX_FILE_SIZE
    JC_DL_STORAGE_MAX_FILE_SIZE = (32*1024 - 2) # 32KB - 2 bytes are system reserved


    