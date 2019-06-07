import ctypes
from ctypes import *
import os
from pathlib import Path
import datetime

import ErrorCodes
from jc_storage_examples import uFR
import globals
#################################################################
def testCardIsStorageType():
    selection_response = (c_ubyte*16)()
    Ne = c_uint32(0)
    sw = (c_ubyte*2)()
    cls = c_ubyte(0x00)
    ins = c_ubyte(0xA4)
    p1 = c_ubyte(0x04)
    p2 = c_ubyte(0x00)
    data_out = StringToCByteArray(globals.DL_STORAGE_AID)
    Nc = c_uint32(globals.DL_SIGNER_AID_SIZE.value)
    send_le = c_ubyte(1)
    
    uFR.s_block_deselect(100)
    
    status = uFR.SetISO14443_4_DLStorage()
    if status != 0:
        print(" Error while switching into ISO 14443-4 mode, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
        uFR.s_block_deselect(100)
    print(" Sending Select APDU...")
    Ne = c_uint32(16)
    sendApduFunc = uFR.APDUTransceive
    sendApduFunc.argtypes = [c_ubyte, c_ubyte, c_ubyte, c_ubyte, (c_ubyte*globals.DL_STORAGE_AID_SIZE.value), c_uint32, (c_ubyte*16), POINTER(c_uint32), c_ubyte, (c_ubyte*2)]
    # cls         ins     p1      p1                                        data_out                           Nc         #data_in    # *Ne          #send_le, #apdu_status
    status = sendApduFunc(cls, ins, p1, p2, data_out, Nc, selection_response, byref(Ne), send_le, sw)
    if status != 0:
        print(" Error while selecting card application, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
        uFR.s_block_deselect(100)
        return
    if sw[0] == 0x90:
        print(" OK!                Card is DL JC Storage Type                      ")
    else:
        print("           You can't use this card to read and write files          ");
    uFR.s_block_deselect(100)
def read():
    card_selected = False
    file_path_name = str()
    file_size = c_uint32(0)
    temp = c_ushort(65535) #\xFFFF
    selection_response = (c_ubyte * 16)()
    count = 0
    uFR.s_block_deselect(100)

    print(" Please enter file index on the card: ")
    temp_input = input()
    if temp_input == "":
        print(" Invalid input. Returning to main...")
        return
    temp = c_ushort(int(temp_input))
    if temp.value >= 16:
        print(" Input error. Maximum file index is 15.")
        return
    card_file_index = c_ubyte(temp.value)
    print(" Please enter new file path and name: ")
    file_path_name = input()
    if file_path_name == "":
        print("Invalid input. Returning to main...")
        return
    aid = StringToCByteArray(globals.DL_STORAGE_AID)
    while card_selected == False:
        status = uFR.SetISO14443_4_DLStorage()
        if status != 0:
            print(" Error while switching into ISO 14443-4 mode, status is:  " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break
        card_selected == True
        print(count)
        count+=1
        # Select:
        print(" Sending Select APDU")
        SelectFunc = uFR.JCAppSelectByAid
        SelectFunc.argtypes = [(c_ubyte * globals.DL_STORAGE_AID_SIZE.value), c_ubyte, (c_ubyte*16)]        
        status = SelectFunc(aid, globals.DL_STORAGE_AID_SIZE.value, selection_response)
        if status != 0:
            print(" Error while selecting card application, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break
        print("Reading file from the card. Please wait.")
        getJCFileSizeFunc = uFR.JCStorageGetFileSize
        getJCFileSizeFunc.argtypes = [c_ubyte, POINTER(c_uint32)]
        status = getJCFileSizeFunc(card_file_index, byref(file_size))
        if status != 0:
            print(" Reading error, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break
        buff = (c_ubyte*file_size.value)()
       
        readJCFileFunc = uFR.JCStorageReadFile
        readJCFileFunc.argtypes = [c_ubyte, (c_ubyte*file_size.value), c_uint32]
        start = datetime.datetime.now()
        status = readJCFileFunc(card_file_index, buff, file_size)
        end = datetime.datetime.now()
        res = end - start
        res = res.total_seconds() * 1000
        if status != 0:
            print(" Reading error, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            
        f = open(file_path_name, "wb")
        result = f.write(buff)
        if result != file_size.value:
            print(" Host file system error while reading file.")
            break
        if card_selected == True:
            uFR.s_block_deselect(100)
        if status == 0:
            print(" File has been successfully read from the card and written to the local file.")
            print("File size is %u bytes" % file_size.value)
            print(" Reading duration: %.3f [ms]" % res)
            print(" Measured time for reading duration only (excluding file system and card selection processes)")
        return status
def write():
    temp = c_ushort(65535)
    card_file_index = c_ubyte(0)
    selection_response = (c_ubyte*16000)() # maximum size of selection response is always 16 bytes
    write_successful = False

    uFR.s_block_deselect(100)

    print(" Please enter file index on the card: ")
    temp_input = input()
    if temp_input == "":
        print("Invalid input. Returning to main...")
        return
    temp = c_ushort(int(temp_input))
    if temp.value >= 16:
        print(" Input error. Maximum file index is 15.")
        return
    card_file_index = c_ubyte(temp.value)
    print(" Please enter file path and name: ")
    file_path_name = input()
    if file_path_name == "":
        print("Invalid input. Returning to main...")
        return
    config = Path(file_path_name)
    if config.is_file():
        f = open(file_path_name, "rb")
    else:
        print("That file does not exist. Returning to main...")
        return
    file_size = c_uint32(os.path.getsize(file_path_name))
    if file_size.value > globals.JC_DL_STORAGE_MAX_FILE_SIZE:
        print(" Error: maximum card file size exceeded.")
        return
    buffer = f.read()
    if file_size.value == 0:
        print(" Host file system error while reading file.")
        return
    while write_successful == False:
        status = uFR.SetISO14443_4_DLStorage()
        if status != 0:
            print(" Error while switching into ISO 144443-4 mode, status: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            write_successful = False
            #break
        card_selected = True
        write_data = (c_ubyte*file_size.value)()
        for x in range(file_size.value):
            write_data[x] = buffer[x]
        # Select
        print(" Sending Select APDU")
        aid = StringToCByteArray(globals.DL_STORAGE_AID)
        SelectFunc = uFR.JCAppSelectByAid
        SelectFunc.argtypes = [(c_ubyte * globals.DL_STORAGE_AID_SIZE.value), c_ubyte, (c_ubyte*16000)]        
        status = SelectFunc(aid, globals.DL_STORAGE_AID_SIZE.value, selection_response)
        if status != 0:
            print(" Error while selecting card application, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            write_successful = False
            #break
        print(" Writing file to the card. This may take a few seconds. Please wait.")
        WriteFunc = uFR.JCStorageWriteFile
        WriteFunc.argtypes = [c_ubyte, (c_ubyte * file_size.value), c_uint32]
        start = datetime.datetime.now()
        status = WriteFunc(card_file_index, write_data, file_size.value)
        end = datetime.datetime.now()
        res = end - start
        res = res.total_seconds() * 1000
        if status != 0:
            if status == 0x000A6A89:
                print("Error during write file to card, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
                print("Select another file index on your next function call.")
                uFR.s_block_deselect(100)
                break
            print("Error during write file to card, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            write_successful = False
            #break
        if status == 0:
            print(" File has been successfully written to the card.")
            print(" Writing duration: %.3f [ms]" % res)
            print(" Measured time for reading duration only (excluding file system and card selection processes)")
            write_successful = True
    if write_successful == True:
        uFR.s_block_deselect(100)
    f.close()
    
def delete():
    temp = c_ushort(65535)
    selection_response = (c_ubyte * 16)()
    uFR.s_block_deselect(100)

    print(" Please enter file index on the card: ")
    temp_input = input()
    if temp_input == "":
        print("Invalid input. Returning to main...")
        return
    temp = c_ushort(int(temp_input))
    if temp.value >= 16:
        print(" Input error. Maximum file index is 15.")
        return
    card_file_index = c_ubyte(temp.value)

    status = uFR.SetISO14443_4_DLStorage()
    if status != 0:
        print(" Error while selecting card application, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
        return
    # Select
    aid = StringToCByteArray(globals.DL_STORAGE_AID)
    SelectFunc = uFR.JCAppSelectByAid
    SelectFunc.argtypes = [(c_ubyte * globals.DL_STORAGE_AID_SIZE.value), c_ubyte, (c_ubyte*16)]        
    status = SelectFunc(aid, globals.DL_STORAGE_AID_SIZE.value, selection_response)
    if status != 0:
        print(" Error while selecting card application, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
        uFR.s_block_deselect(100)
        return

    DeleteFunc = uFR.JCStorageDeleteFile
    DeleteFunc.argtypes = [c_ubyte]
    status = DeleteFunc(card_file_index)
    if status != 0:
        print(" Error while deleting file, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
        uFR.s_block_deselect(100)
        return
    print(" File on card has been deleted successfully.")
    uFR.s_block_deselect(100)
def list_files():
    selection_response = (c_ubyte*16)()
    success = False
    list_size = c_uint32(0)
    
    uFR.s_block_deselect(100)

    while success == False:
        status = uFR.SetISO14443_4_DLStorage()
        if status != 0:
            print(" Error while switching into ISO 14443-4 mode, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break
        # Select:
        aid = StringToCByteArray(globals.DL_STORAGE_AID)
        SelectFunc = uFR.JCAppSelectByAid
        SelectFunc.argtypes = [(c_ubyte * globals.DL_STORAGE_AID_SIZE.value), c_ubyte, (c_ubyte*16)]        
        status = SelectFunc(aid, globals.DL_STORAGE_AID_SIZE.value, selection_response)
        if status != 0:
            print(" Error while selecting card application, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break
        GetListSizeFunc = uFR.JCStorageGetFilesListSize
        GetListSizeFunc.argtypes = [POINTER(c_uint32)]
        status = GetListSizeFunc(byref(list_size))
        if status != 0: 
            print(" Could not get list size, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break 
        file_list = (c_ubyte*list_size.value)()
        files_sizes = (c_uint32 * list_size.value)()
        ListFilesFunc = uFR.JCStorageListFiles
        ListFilesFunc.argtypes = [(c_ubyte * list_size.value), c_uint32]
        status = ListFilesFunc(file_list, list_size)
        if status != 0:
            print("Could not get file list, status is: " + ErrorCodes.UFCODER_ERROR_CODES[status])
            break
        for i in range(list_size.value):
            GetFileSizeFunc = uFR.JCStorageGetFileSize
            GetFileSizeFunc.argtypes = [c_ubyte, POINTER(c_uint32)]
            file_index = c_ubyte(file_list[i])
            file_size = c_uint32(files_sizes[i])
            status = GetFileSizeFunc(file_index, byref(file_size))
            files_sizes[i] = file_size
            if status != 0:
                print(" Can't get size for a file with an index %d, status is: %s " % (i, ErrorCodes.UFCODER_ERROR_CODES[status]))
                break
        success = True
    uFR.s_block_deselect(100)
    if success == True:
        print(" List of the files on the card:")
        print(" +---------+--------------+")
        print(" |  index  | size [bytes] |")
        print(" +---------+--------------+")
        for i in range(list_size.value):
            print(" |    %2d   | %11u  |" % (file_list[i], files_sizes[i]))
            print(" +---------+--------------+")
    
def StringToCByteArray(input):
    # converts string to c_ubyte() array
    str_len = len(input)
    byte_aid = (c_ubyte*str_len)()
    for x in range(str_len):
        byte_aid[x] = ord(input[x])
    return byte_aid