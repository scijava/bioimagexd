#! /usr/bin/env python
import struct
import sys,os

if __name__=='__main__':
    if len(sys.argv)<2:
        print "Usage: is_nih <lut file>"
        sys.exit(1)

if not os.path.exists(sys.argv[1]):
    print "File",sys.argv[1],"does not exist"
    sys.exit(1)
data = open(sys.argv[1]).read()
d=len(data)-32
s="4s2s2s2s2s8s8si%ds"%d
header,version,ncolors,start,end,fill1,fill2,filler,lut = struct.unpack(s,data)

if header!="ICOL":
    print "NOT NIH LUT"
    sys.exit(1)
else:
    print "IS NIH LUT"
