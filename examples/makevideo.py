#! /bin/env python
import sys, os, time
import pymedia.video.vcodec as vcodec
import pygame

def makeVideo( inPattern, outFile, outCodec ):
  # Get video stream dimensions from the image size
  pygame.init()
  i= 1
  # Opening mpeg file for output
  e= None
  i= 1
  fw= open( outFile, 'wb' )
  while i:
    if os.path.isfile( inPattern % i ):
      s= pygame.image.load( inPattern % i )
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
          'height': s.get_height(),
          'width': s.get_width(),
          'frame_rate': 2997,
          'deinterlace': 0,
          'bitrate': bitrate,
          'id': vcodec.getCodecID( outCodec )
        }
        print 'Setting codec to ', params
        e= vcodec.Encoder( params )
        t= time.time()
      
      # Create VFrame
      ss= pygame.image.tostring(s, "RGB")
      bmpFrame= vcodec.VFrame( vcodec.formats.PIX_FMT_RGB24, s.get_size(), (ss,None,None))
      yuvFrame= bmpFrame.convert( vcodec.formats.PIX_FMT_YUV420P )
      d= e.encode( yuvFrame )
      fw.write( d )
      i+= 1
    else:
      print '%d frames written in %.2f secs( %.2f fps )' % ( i, time.time()- t, float( i )/ ( time.time()- t ) )
      i= 0
  
  fw.close()
  pygame.quit()


if __name__== '__main__':
  if len( sys.argv )!= 4:
    print "Usage: make_video <in_file_pattern> <out_file> <format>\n\tformat= { mpeg1video | mpeg2video }"
  else:
    makeVideo( sys.argv[ 1 ], sys.argv[ 2 ], sys.argv[ 3 ] )

 
