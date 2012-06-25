import sys
import csv
#import codecs
import struct
import vtk

def prepare_data(x,y,z):
    return [0]*(x*y*z)
    
# Plot a given track file
def set_pos(data,x,y,z,w,h,d,value):
    
    x=int(x)
    y=int(y)
    z=int(z)
    i = z*(w*h)+y*w+x
    #print "Setting position",i,"to",value
    data[i] = value
    
def interpolate(pt1,pt2):
    ret=[]
    dx, dy, dz = pt2[0]-pt1[0],pt2[1]-pt1[1],pt2[2]-pt1[2]
    dx=int(dx)
    dy=int(dy)
    dz=int(dz)
    gx,gy,gz = pt2
    sx,sy,sz = pt1
    signx=signy=signz=0
    if dx:
        signx = dx/abs(dx)
    if dy:
        signy = dy/abs(dy)
    if dz:
        signz = dz / abs(dz)
    m = max(abs(dx),abs(dy),abs(dz))
    ret.append(pt1)
    for i in range(m):
        xd = signx*i
        yd = signy*i
        zd = signz*i
        if abs(xd)>abs(dx):xd=dx
        if abs(yd)>abs(dy):yd=dy
        if abs(zd)>abs(dz):zd=dz
        
        x = sx+xd
        y = sy+yd
        z = sz+zd
        if x<0:print "x=",x,"<0, dx=",dx,"sx=",sx,"signx=",signx,"i=",i
        if y<0:print "y=",y,"<0, dy=",dy,"sy=",sy,"signy=",signy,"i=",i
        if z<0:print "z=",z,"<0, dz=",dz,"sz=",sz,"signz=",signz,"i=",i
            
        
        #if x>gx:x=gx
        #if y>gy:y=gy
        #if z>gz:z=gz
        ret.append((x,y,z))
    ret.append(pt2)
    return ret

def points_to_data(data, pttracks,w,h,d):
    for i,points in enumerate(pttracks):
        #print "Processing ",len(points),"points in track",i
        for x,y,z in points:
            #set_pos(data, x,y,z,w,h,d, 255)
            set_pos(data, x,y,z,w,h,d, i+2)
    

def main(filename,width,height,depth):
    print "Reading file",filename,"and creating data of size",width,height,depth
    rdr = csv.reader(open(filename), dialect="excel",delimiter=";")
    tracks=[]
    ctrack=[]
    
    currtrack=-1
    for track, timepoint, x,y,z in rdr:
        try:
            tracknum=int(track)
        except:
            continue
        timepoint = int(timepoint)
        x = float(x)
        y = float(y)
        z = float(z)
        if tracknum != currtrack:
            if ctrack:
                #print "Adding track",ctrack
                tracks.append(ctrack)
                ctrack=[]            
            currtrack = tracknum
        ctrack.append((x,y,z))
    
    write_as_imagedata(tracks,width,height,depth)

def write_as_imagedata(tracks,width,height,depth):
    pttracks=[]
    data=prepare_data(width,height,depth)
    print "got data size=",len(data)
    
    for track in tracks:
        #print "track=",track
        pts = []
        for i,pt in enumerate(track[:-1]):
            pt2 = track[i+1]
            pts.extend(interpolate(pt,pt2))
        pttracks.append(pts)
    print "number of point tracks=",len(pttracks)
    points_to_data(data, pttracks,width,height,depth)        
    write_data(data,width,height,depth)
    
def write_data(data,x,y,z):
    siz = x*y*z
    fs="%dH"%siz
    print "min(data)=",min(data),"max(data)=",max(data)
    print "size=",siz,"len of data=",len(data)
    ss = struct.pack(fs,*data)
    print "min(ss)=",min(ss),"max(ss)=",max(ss),"len(ss)=",len(ss)
    
    
    importer=vtk.vtkImageImport()
    importer.CopyImportVoidPointer(ss,len(ss))
    importer.SetDataScalarTypeToUnsignedShort()
    #importer.SetDataScalarTypeToUnsignedChar()
    #importer.SetDataScalarType(5)
    importer.SetNumberOfScalarComponents(1)
    importer.SetDataExtent(0,x-1,0,y-1,0,z-1)
    importer.SetWholeExtent(0,x-1,0,y-1,0,z-1)
    importer.Update()
    image = importer.GetOutput()
    #print image
    print "Image scalar range=",image.GetScalarRange()
    print "Image scalar type=",image.GetScalarTypeAsString()
    #print image
    
    writer = vtk.vtkXMLImageDataWriter()
    writer.SetInput(image)
    writer.SetFileName("output.vti")
    print "Writing..."
    writer.Write()
    print "done"

if __name__=='__main__':
    if len(sys.argv)<4:
        print "Usage: plot_track <file> <x> <y> <z>"
        sys.exit(1)
    import psyco
    psyco.full()
    main(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]))
