#! /bin/env python
import sys
import pymedia.video.muxer as muxer
import pymedia.video.vcodec as vcodec

def recodeVideo( inFile, outFile, outCodec ):
        dm= muxer.Demuxer( inFile.split( '.' )[ -1 ] )
        f= open( inFile, 'rb' )
        fw= open( outFile, 'wb' )
        s= f.read( 400000 )
        r= dm.parse( s )
        v= filter( lambda x: x[ 'type' ]== muxer.CODEC_TYPE_VIDEO, dm.streams )
        if len( v )== 0:
                raise 'There is no video stream in a file %s' % inFile
        
        v_id= v[ 0 ][ 'index' ]
        print 'Assume video stream at %d index: ' % v_id
        c= vcodec.Decoder( dm.streams[ v_id ] )
        e= None
        while len( s )> 0:
                for fr in r:
                        if fr[ 0 ]== v_id:
                                d= c.decode( fr[ 1 ] )
                                if e== None and d:
                                        params= c.getParams()
                                        params[ 'id' ]= vcodec.getCodecID( outCodec )
                                        # Just try to achive max quality( 2.7 MB/sec mpeg1 and 9.8 for mpeg2 )
                                        if outCodec== 'mpeg1video':
                                                params[ 'bitrate' ]= 2700000
                                        else:
                                                params[ 'bitrate' ]= 9800000
                                        # It should be some logic to work with frame rates and such.
                                        # I'm not aware of what it would be...
                                        print 'Setting codec to ', params
                                        e= vcodec.Encoder( params )
                                if e and d:
                                        dw= e.encode( d )
                                        #print 'Frame size ', len( dw )
                                        fw.write( dw )
                
                s= f.read( 400000 )
                r= dm.parse( s )

if __name__== '__main__':
  if len( sys.argv )!= 4:
    print "Usage: recode_video <in_file> <out_file> <format>\n\tformat= { mpeg1video | mpeg2video }"
  else:
    recodeVideo( sys.argv[ 1 ], sys.argv[ 2 ], sys.argv[ 3 ] )
