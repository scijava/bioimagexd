#! /bin/env python
import sys, os, time
import pymedia.video.vcodec as vcodec
import os.path
import struct
import glob
sys.path.insert(0,os.path.normpath("../Modules/VTK/bin"))
sys.path.insert(0,os.path.normpath("../Modules/VTK/Wrapping/Python"))

import vtk




def makeVideo( inPattern, outFile, outCodec ):
  reader=vtk.vtkPNGReader()
  # Get video stream dimensions from the image size
  i= 1
  # Opening mpeg file for output
  e= None
  i= 1
  fw= open( outFile, 'wb' )
  exporter=vtk.vtkImageExport()
  t=time.time()
  files=glob.glob("*.png")
  i=0
  for file in files:
    if os.path.isfile( file ):
      print "Read %s"%file
      reader.SetFileName(file)
      reader.Update()
      img=reader.GetOutput()
      exporter.SetInput(img)
      x,y,z=img.GetDimensions()
      if not e:
        if outCodec== 'mpeg1video':
          bitrate= 2700000
        else:
          bitrate= 9800000
        
        params= { \
          'type': 0,
          'gop_size': 12,
          'frame_rate_base': 125,
          'max_b_frames': 0,
          'height': y,
          'width': x,
          'frame_rate': 2997,
          'deinterlace': 0,
          'bitrate': bitrate,
          'id': vcodec.getCodecID( outCodec )
        }
        print 'Setting codec to ', params
        e= vcodec.Encoder( params )
        t= time.time()
      
      # Create VFrame
      reqsize=exporter.GetDataMemorySize()
      fs="%ds"%reqsize
      print fs
      print "Data requires %d bytes"%reqsize
      ss=struct.pack(fs,"")
      exporter.SetExportVoidPointer(ss)
      print "Exporting..."
      exporter.Export()
      print "Converting..."
      bmpFrame= vcodec.VFrame( vcodec.formats.PIX_FMT_RGB24, (x,y), (ss,None,None))
      yuvFrame= bmpFrame.convert( vcodec.formats.PIX_FMT_YUV420P )
      print "done!"
      print "encoding..."
      d= e.encode( yuvFrame )
      print "Writing..."
      fw.write( d )
      i+= 1
    else:
      print '%d frames written in %.2f secs( %.2f fps )' % ( i, time.time()- t, float( i )/ ( time.time()- t ) )
      i= 0
  
  fw.close()


if __name__== '__main__':
  if len( sys.argv )!= 4:
    print "Usage: make_video <in_file_pattern> <out_file> <format>\n\tformat= { mpeg1video | mpeg2video }"
  else:
    makeVideo( sys.argv[ 1 ], sys.argv[ 2 ], sys.argv[ 3 ] )

 
