# File: FunkLootaDemo.py
#
# Jukka Varsaluoma

from Tkinter import *

class FunkLoota:

    def __init__(self, master):

        # Values 0-255
        self.x0 = 20
        self.y0 = 20
        self.x1 = 180
        self.y1 = 80

        # Movable size
        self.bz = 4

        frame = Frame(master)

        self.canvas = Canvas(frame, width=300, height=300, background='white')
        self.canvas.width = 300
        self.canvas.height = 300

        self.canvas.bind("<Button-1>", self.clickLeft)
        self.canvas.bind("<Button-3>", self.clickRight)

        self.setup()

        self.canvas.pack()
        frame.pack()

    def setup(self):

        w = self.canvas.width/256.0
        h = self.canvas.height/256.0

        self.oval0 = self.canvas.create_oval ( self.x0*h-self.bz, self.y0*w-self.bz, self.x0*h+self.bz, self.y0*w+self.bz, fill='white')
        self.oval1 = self.canvas.create_oval ( self.x1*h-self.bz, self.y1*w-self.bz, self.x1*h+self.bz, self.y1*w+self.bz, fill='white')

        self.line = self.canvas.create_line ( 0, self.y0*h, self.x0*w, self.y0*h, self.x1*w, self.y1*h, self.canvas.width,self.y1*h)

    def draw(self):

        w = self.canvas.width/256.0
        h = self.canvas.height/256.0

        self.canvas.coords(self.line, 0, self.y0*h, self.x0*w, self.y0*h, self.x1*w, self.y1*h, self.canvas.width,self.y1*h)
        self.canvas.coords(self.oval0, self.x0*h-self.bz, self.y0*w-self.bz, self.x0*h+self.bz, self.y0*w+self.bz)
        self.canvas.coords(self.oval1, self.x1*h-self.bz, self.y1*w-self.bz, self.x1*h+self.bz, self.y1*w+self.bz)

    def coordsTo256(self, x,y):

        w = 256.0/self.canvas.width
        h = 256.0/self.canvas.height

        x = x * w
        y = y * h

        x = max(0,x)
        y = max(0,y)
        x = min(256,x)
        y = min(256,y)

        return(x,y)

    def clickLeft(self, event):
        # Get the click location:
        x, y = event.x, event.y

        x,y = self.coordsTo256(x,y)

        self.x0 = min(x,self.x1)
        self.y0 = y

        self.draw()

    def clickRight(self, event):
        # Get the click location:
        x, y = event.x, event.y

        x,y = self.coordsTo256(x,y)

        self.x1 = max(x,self.x0)
        self.y1 = y

        self.draw()

root = Tk()

app = FunkLoota(root)

root.mainloop()
