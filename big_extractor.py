"""
BIG5 = CLASH.big
BIG4 = VIDEO.big
BIGF = other

BIG4 and BIGF are the same afaik

// all values ive seen have been big endian except for the file count at the start of the file (0x4)
0x0: char sig[3];    // b'BIG'
0x3: char type;      // 5, 4 or F (ive seen so far)
0x4: u32 file_size;  // size of the .big file (little endian)
0x8: u32 num_files;  // number of files in archive
"""

import struct
import sys
import os
from pathlib import Path

# if we should make a directory to put all the exported files
# the name of the directory will be the name of the file without the extension
EXPORT_TO_DIR = True

# read 32 bit unsigned integer for both little endian and big endian
def be_uint32(b):
    return struct.unpack('>I', b)[0]
def le_uint32(b):
    return struct.unpack('<I', b)[0]

# simple class used to store the file meta data in both versions
class FEntry:
    def __init__(self, offs, size, path):
        self.offs = offs
        self.size = size
        self.path = path

    # for debugging
    def __str__(self):
        return f'path: {self.path}, offs: {self.offs}, size: {self.size}'


# get null terminated string from file
def get_string(fd):
    # TODO: prevent/handle reading past file if no null terminator is found
    name = ""
    char = fd.read(1)
    while char != b'\0':
        name += char.decode('ascii')
        char = fd.read(1)
    return name

# display file names as we are extracting
def outlog(data):
    print(f'\r{data}'.ljust(64, ' '), end='')

# get meta data
def get_file_entry(fd):
    return FEntry(be_uint32(fd.read(4)), be_uint32(fd.read(4)), get_string(fd))


def write_file(path, data):
    dirs, filename = path.rsplit('/', 1)
    
    # make directories if they dont already exist
    try:
        os.makedirs(dirs)
    except IOError:
        pass

    # create file and write the data
    with open(path, 'wb') as outfile:
        outfile.write(data)

    # return the filename so we can display it as output
    return filename

# extract and return array of metadata to process later
def extract_BIG5(file, file_count):
    file.seek(3, os.SEEK_CUR)

    entries = []
    # read meta data of each file and append to list
    for i in range(file_count):
        # skip unknown byte
        file.seek(1, os.SEEK_CUR) 
        entries.append(get_file_entry(file))

    return entries

# extract and return array of metadata to process later
def extract_BIGF(file, file_count):
    file.seek(4, os.SEEK_CUR)

    entries = []
    # read meta data of each file and append to list
    for i in range(file_count):
        entries.append(get_file_entry(file))

    return entries


if __name__ == '__main__':

    # program expects filepath given as a command line argument
    if len(sys.argv) != 2:
        print('invalid number of arguments')
        exit(1)

    # get filepath argument entered by user
    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print('File does not exist...')
        exit(1)

    bdir = Path(filepath).stem if EXPORT_TO_DIR else ""

    with open(filepath, 'rb') as file:
        # read file header b'BIG'*
        header = file.read(4)

        # get .big size (little endian)
        file_size = le_uint32(file.read(4))

        # get number of files inside
        file_count = be_uint32(file.read(4))

        entries = None

        if header == b'BIG5':
            entries = extract_BIG5(file)
        elif header == b'BIGF' or header == b'BIG4':
            entries = extract_BIGF(file)
        else:
            print('Not a \'BIG\' file!')
            exit(1)
        
        # iterate over the entries we have gathered and process the files
        for entry in entries:
            file.seek(entry.offs)
            thefile = write_file(bdir + entry.path, file.read(entry.size))
            outlog(f'extracting {thefile}...')
        outlog('complete!')