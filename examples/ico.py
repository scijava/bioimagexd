from Tkinter import *;
import Image, ImageTk


class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()

myapp = App()

myapp.master.title("Sample Application")
myapp.master.iconbitmap("LeoApp.ico")

myapp.mainloop()

