from Tkinter import *;
import Image, ImageTk


class App:
    def __init__(self, master):
        
        self.frame = Frame(master)
        master.geometry("300x300")
        master.title("Toolbar with icons")
        self.frame.pack()

        #open and thumbnail GIFs for toolbar buttons
        self.image1 = Image.open("Therm0a.gif")
        self.image1.thumbnail((32, 32))
        self.img1 = ImageTk.PhotoImage(self.image1)
        
        self.image2 = Image.open("Rainbow.gif")
        self.image2.thumbnail((22, 22))
        self.img2 = ImageTk.PhotoImage(self.image2)
        
        self.image3 = Image.open("Lamp.gif")
        self.image3.thumbnail((20, 20))
        self.img3 = ImageTk.PhotoImage(self.image3)
        
        self.image4 = Image.open("Dots.gif")
        self.image4.thumbnail((18, 18))
        self.img4 = ImageTk.PhotoImage(self.image4)



        #create a toolbar
        self.toolbar = Frame(self.frame)
        
        #create a buttons
        b1 = Button(self.toolbar, text = "Visualize sparse intensitys", image = self.img1)
        b1.img1 = self.img1 # keep the reference
        b1.pack(side = LEFT)

        b2 = Button(self.toolbar, text = "Color merge", image = self.img2)
        b2.img2 = self.img2 # keep the reference
        b2.pack(side = LEFT)

        b3 = Button(self.toolbar, text = "Intensity interpolation", image = self.img3)
        b3.img3 = self.img3 # keep the reference
        b3.pack(side = LEFT)

        b4 = Button(self.toolbar, text = "Sparse intensity visualisation", image = self.img4)
        b4.img4 = self.img4 # keep the reference
        b4.pack(side = LEFT)

        self.toolbar.pack(side = TOP)


root = Tk()
app = App(root)
root.mainloop()
