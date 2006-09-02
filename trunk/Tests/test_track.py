import csv
import sys
import math
import psyco
import time
import os.path
import codecs



class ParticleReader:
    def __init__(self,filename, timepoint = 0, filterObjectSize = 2, spacing=(1,1,1)):
        self.rdr = csv.reader(open(filename), dialect="excel",delimiter=";")
        self.filterObjectSize = filterObjectSize
        self.timepoint = timepoint
        self.spacing = spacing
    def read(self):
        ret=[]
        for obj, sizemicro,size,cog in self.rdr:
            try:
                size = int(size)
            except:
                continue
            
            obj = int(obj)
            if obj==0:continue
            if size >= self.filterObjectSize:
                x,y,z = eval(cog)
                intpos=x,y,z
                x*=self.spacing[0]
                y*=self.spacing[1]
                z*=self.spacing[2]
                cog = (x,y,z)
                p = Particle(cog, intpos, self.timepoint, size, obj)
                ret.append(p)
        return ret

class Particle:
    def __init__(self, pos = (0,0,0),intpos=(0,0,0), tp = 0, size=1, obj=-1):
        self.pos = pos
        self.intval = obj
        self.tp = tp
        self.size = size
        self.inTrack = 0
        self.flag = 0
        self.trackNum = -1
        self.posInPixels=intpos
        
    def distance(self, p):       
        x,y,z=p.pos
        x2,y2,z2=self.pos
        dx=x-x2
        dy=y-y2
        dz=z-z2
        dsize = p.size-self.size
        return math.sqrt(dx*dx+dy*dy+dz*dz+dsize*dsize)
        
    def copy(self, p):
        self.size = p.size
        self.pos = p.pos
        self.posInPixels = p.posInPixels
        self.inTrack = p.inTrack
        self.flag = p.flag
        self.tp = p.tp
        self.intval = p.intval
        
    def __str__(self):
        try:
            x,y,z = self.pos
            return "#%d at (%.2f, %.2r, %.2f) at time %d, in track: %s"%(self.intval, x,y,z,self.tp, not not self.inTrack)
        except:
            raise "Bad pos",self.pos
    def __repr__(self):
        return self.__str__()

def get_tracks(particles, maxVelocity = 5):
    tracks=[]
    trackCount=0
    totalTimepoints = len(particles)
    searchOn = False
    foundOne = False
    
    for tp in range(totalTimepoints):
        
        for i,particle in enumerate(particles[tp]):
            if particle.inTrack:
                print "\nParticle %d / %d in timepoint %d is already in track %d"%(i,len(particles[tp]),tp,particle.trackNum)
            else:
                print "\nTracking particle %d / %d in timepoint %d"%(i,len(particles[tp]),tp)

                track=[]
                trackCount+=1
                particle.inTrack = True
                particle.trackNum = trackCount
                track.append(particle)
                
                oldParticle = Particle()
                tmpParticle = Particle()
                oldParticle.copy(particle)
                searchOn = True
                # Search the next timepoints for more particles
                for search_tp in range(tp+1,totalTimepoints):
                    foundOne = False
                    newParticle = Particle()
                    for testParticle in particles[search_tp]:
                        dist = testParticle.distance(oldParticle)
                        # If a particle is within search radius and doesn't belong in a
                        # track yet
                        if dist < maxVelocity and (not testParticle.inTrack):
                            # if there's no other particle that fits the criteria
                            if not foundOne:
                                tmpParticle = testParticle
                                testParticle.inTrack = True
                                testParticle.trackNum = trackCount
                                newParticle.copy(testParticle)
                                foundOne = True
                            else:
                                # if we've already found one, then use this instead if
                                # this one is closer. In any case, flag the particle
                                testParticle.flag = True
                                if dist < newParticle.distance(oldParticle):
                                    testParticle.inTrack = True
                                    testParticle.trackNum = trackCount
                                    newParticle.copy(testParticle)
                                    tmpParticle.inTrack = False
                                    tmpParticle.trackNum = -1
                                    tmpParticle = testParticle
                                else:
                                    newParticle.flag = True
                        elif dist < maxVelocity:
                            # If the particle is already in a track but could also be in this
                            # track, we have a few options
                            # 1. Sort out to which track this particle really belongs (but how?)
                            # 2. Stop this track
                            # 3. Stop this track, and also delete the remainder of the other one
                            # 4. Stop this track and flag this particle:
                            testParticle.flag = True
                    if foundOne:
                        sys.stdout.write(".")
#                        print "Particle added to track %d"%trackCount
                        track.append(newParticle)
                    else:
                        sys.stdout.write("^")
                        #print "Found no particles that belong to track %d"%trackCount
                        searchOn = False
                    oldParticle.copy(newParticle)
                tracks.append(track)
    return tracks

def main(fileprefix,n, maxvel = 15, vx=1.0,vy=1.0,vz=1.0):
    particles=[]
    for i in range(0,n+1):
        file="%s_%d.csv"%(fileprefix,i)
        if os.path.exists(file):
            rdr = ParticleReader(file, i-1, filterObjectSize = 10, spacing = (vx,vy,vz))
            particles.append(rdr.read())
    for i,list in enumerate(particles):
        print "In timepoint %d, there are %d particles"%(i,len(list))
    t = time.time()
    tracks = get_tracks(particles, maxVelocity = maxvel)
    print "Found", len(tracks),"tracks in ",time.time()-t,"seconds"
    for i,track in enumerate(tracks):
        print "There are %d particles in track %d"%(len(track),i)
        
    f=codecs.open("tracks.csv","wb","latin1")
        
    w=csv.writer(f,dialect="excel",delimiter=";")
    w.writerow(["Track #","Object #","Timepoint","X","Y","Z"])
    for i,track in enumerate(tracks):
        if len(track)<3:continue
        for particle in track:
            x,y,z=particle.posInPixels
            w.writerow([str(i),str(particle.intval),str(particle.tp), str(x),str(y),str(z)])        
    f.close()
    

if __name__ == '__main__':
    if len(sys.argv) <3:
        print "Usage: track <file prefix> <number of timepoints> [max velocity = 15] [voxel size x] [voxel size y] [voxel size z]"
        print "Track files are assumed to be named <file prefix>_<timepoint>.csv"
        sys.exit(1)
        
    if len(sys.argv)>3:
        maxvel = int(sys.argv[3])
    else:
        maxvel = 15
    if len(sys.argv)>5:
        vx, vy, vz = map(float,sys.argv[4:7])
    n=int(sys.argv[2])
    psyco.full()
    main(sys.argv[1], n, maxvel, vx,vy,vz)
