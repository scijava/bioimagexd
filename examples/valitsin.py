from Tkinter import *

root=Tk()


window=Frame(root)
nrow=0
ncol=0
window.pack()

def markButton(widget):
    if not widget.__dict__.has_key("selected"):
        widget.oldcol=widget.cget("bg")
        widget.config(bg="#333333")
        widget.selected=1
    else:
        widget.config(bg=widget.oldcol)
        widget.selected=0


for i in range(200+1):
    if ncol==30:
        nrow=nrow+1
        ncol=0
    btn=Button(window,text="%d"%i,font="Arial 6")
    btn.config(command=lambda x=btn: markButton(x))
    btn.grid(row=nrow,column=ncol,sticky=W+E)
    ncol=ncol+1
mainloop()
