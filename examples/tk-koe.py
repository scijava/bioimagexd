# -*- coding: cp1252 -*-
from Tkinter import *
import Tree
import os.path
import tkMessageBox
import tkFileDialog

class MyNode(Tree.Node):
    def __init__(self, *args, **kw_args):
        # call superclass
        apply(Tree.Node.__init__, (self,)+args, kw_args)
        # bind right-click
        self.widget.tag_bind(self.symbol, '<1>', self.setActive)
        self.widget.tag_bind(self.label, '<1>', self.setActive)
        
    def setActive(self, event):
        global mainwin

        self.widget.delete("highlight")

        path=apply(os.path.join,self.full_id())
        print path
        type="N/A"
        if path[-3:]=="chl":
            type="CHANNEL"
        elif path[-3:]=="tpt":
            type="TIMEPOINT"
            if mainwin.isSelected(path):
                self.widget.itemconfig(self.label,fill="#000000")
                self.unselectItem(path)
                mainwin.unSelect(path)
#                self.highlightItem()
            else:
                mainwin.select(path)
                self.widget.itemconfig(self.label,fill="#ffffff")
#                self.widget.itemconfig(self.label,fill="#0000ff",font="Arial 12")
                self.selectItem(path)
#                self.highlightItem()
            # If we are looking at a timepoint, we
            # find out the channel the timepoint belongs to and first
            # set that channel
            # full_id()[:-1] is the id for the channel this timepoint belongs to
            fid=self.full_id()[:-1]
            # self.widget == the tree we belong to
            # we find the channel node and get it's label
            lbl=self.widget.find_full_id(fid).get_label()
            mainwin.selectTreeItem("CHANNEL",lbl)
        mainwin.selectTreeItem(type,self.get_label())

    def selectItem(self,path):
        bbox = self.widget.bbox(self.label)
        if bbox:
            i = self.widget.create_rectangle(
                bbox, fill="navyblue",
                tag=path,outline=""
                )
            self.widget.lower(i, self.label)
            
    def unselectItem(self,path):
        print "Unselect ",path
        bbox=self.widget.bbox(self.label)
        if bbox:
            i = self.widget.create_rectangle(
                bbox, fill=self.widget.cget("bg"),
                tag=path,outline=""
                )
            self.widget.lower(i, self.label)
        self.widget.delete(path)
        
    
    def highlightItem(self):
        bbox = self.widget.bbox(self.label)
        if bbox:
            i = self.widget.create_rectangle(
                bbox, fill="lightblue",
                tag="highlight",outline=""
                )
            self.widget.lower(i, self.label)

class MainWindow:
    def __init__(self,root):
        self.root=root
        self.root.config(width=640,height=480)

        self.selected={}

        self.statusbar=StatusBar(self.root)
        self.statusbar.set("Initializing.")
        self.statusbar.grid(row=5,column=0,sticky=W+E)


        self.createMenu()
        self.createToolBar()
        self.createTree()
        self.createInfoBox()

        self.colorMap={"red":"#ff0000","green":"#00ff00","blue":"#0000ff","yellow":"#ffff00"}
        
        self.statusbar.set("Done.")

    def selectTreeItem(self,type,item):
        if type=="CHANNEL":
            self.channelName.config(text=item)
            name=item.split(" ")[0]
            self.channelColor.config(bg=self.colorMap[name.lower()])            
            self.channelTimePoint.config(text="")
        elif type=="TIMEPOINT":
            self.channelTimePoint.config(text=item)

        else:
            self.channelName.config(text="")
            self.channelTimePoint.config(text="")


    def isSelected(self,path):
        if not self.selected.has_key(path):
            self.selected[path]=None
        return self.selected[path]
    def unSelect(self,path):
        self.selected[path]=None
    def select(self,path):
        self.selected[path]=1
        
    def selectItem(self,x):
        txt=self.listbox.get(ACTIVE)
        self.channelName.config(text=txt)
        self.channelColor.config(bg=self.colorMap[txt.lower()])


    def createInfoBox(self):
        self.infoframe=Frame(self.root,relief=RAISED,borderwidth=1,width=200,height=100)
        self.channelNameLbl=Label(self.infoframe,text="Channel:",width=20,anchor=W)
        self.channelTimePointLbl=Label(self.infoframe,text="Time point:",width=20,anchor=W)
        self.channelTimePoint=Label(self.infoframe,text="<n/a>",width=10)
        self.channelColorLbl=Label(self.infoframe,text="Color: ",width=20,anchor=W)
        self.channelName=Label(self.infoframe,text="<n/a>",width=10)
        self.channelColor=Label(self.infoframe,bg="#ffffff",width=10,anchor=W)

        self.channelNameLbl.grid(row=0,column=0,sticky=W+E)
        self.channelName.grid(row=0,column=1)
        self.channelTimePointLbl.grid(row=1,column=0)
        self.channelTimePoint.grid(row=1,column=1)
        self.channelColorLbl.grid(row=2,column=0,sticky=W+E)
        self.channelColor.grid(row=2,column=1)
        self.infoframe.grid(row=2,column=0,sticky=W)

    def createTree(self):
        self.tree=Tree.Tree(master=self.root,root_id="\\lsm",root_label="LSM File",get_contents_callback=self.createTreeContents,width=300,node_class=MyNode)
        self.tree.grid(row=1,column=0)
        
    def createTreeContents(self,node):
        path=apply(os.path.join,node.full_id())
        print path
        if path=="\\lsm":
            self.tree.add_node(name="Red Channel",id="\\lsm\\red_chl",flag=1)
            self.tree.add_node(name="Green Channel",id="\\lsm\\green_chl",flag=1)
            self.tree.add_node(name="Blue Channel",id="\\lsm\\blue_chl",flag=1)
            self.tree.add_node(name="Colocalization Maps",id="\\lsm\\colocalization_col",flag=1)
            self.tree.add_node(name="Merged Channels",id="\\lsm\\colormerge_mrg",flag=1)
        else:
            print path[-3:]
            if path[-3:]=="chl":
                for i in range(0,5):
                    self.tree.add_node(name="Time point %d"%i,id="%s\\time%d_tpt"%(path,i))
            elif path[-3:]=="col":
                self.tree.add_node(name="Colocalization (Red, Green)",id="%s\\col_red_green"%(path))
            elif path[-3:]=="mrg":
                self.tree.add_node(name="Merged Channels (Red, Green)",id="%s\\mrg_red_green"%(path))
    def createToolBar(self):
        self.toolbar=ToolBar(self.root)
        self.toolbar.insertButton("Color Merging",self.menuMergeChannels)#,"Z:\\Sovellusprojekti\\CVS\\kuvat\\merge.gif")
        self.toolbar.insertButton("Colocalization",self.menuColocalization)#,"Z:\\Sovellusprojekti\\CVS\\kuvat\\colo.gif")
        self.toolbar.grid(row=0,column=0,sticky=W+E)

    def createListBox(self):
        self.listbox=Listbox(self.root,selectmode=MULTIPLE)
        for i in ["Punainen","Vihreä","Sininen"]:
            self.listbox.insert(END,i)

        self.listbox.grid(row=1,column=0)
        self.listbox.bind('<Button-1>',self.selectItem)

    def createMenu(self):
        self.menu=Menu(self.root)
        self.root.config(menu=self.menu)
        self.fileMenu=Menu(self.menu,tearoff=0)
        self.taskMenu=Menu(self.menu,tearoff=0)
        self.helpMenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="File",menu=self.fileMenu)
        self.menu.add_cascade(label="Tasks",menu=self.taskMenu)
        self.menu.add_cascade(label="Help",menu=self.helpMenu)

        self.fileMenu.add_command(label="Open LSM File...",command=self.menuOpenLSM)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Quit",command=self.quitApp)

        self.taskMenu.add_command(label="Colocalization Map...",command=self.menuColocalization)
        self.taskMenu.add_command(label="Merge Channels...",command=self.menuMergeChannels)
        self.taskMenu.add_command(label="Adjust Intensity and Contrast...",command=self.menuAdjustIntensity)

        self.helpMenu.add_command(label="Online Help",command=self.menuHelp)
        self.helpMenu.add_command(label="About LSM Module",command=self.menuAbout)

        
    def menuOpenLSM(self):
        askfile=tkFileDialog.askopenfilename(title="Open LSM File",filetypes=[("LSM File",".lsm")])

    def menuColocalization(self):
        tkMessageBox.showinfo("Colocalization","This feature has not been implemented yet")
        
    def menuMergeChannels(self):
        tkMessageBox.showinfo("Merge Channels","This feature has not been implemented yet")
        
    def menuAdjustIntensity(self):
        tkMessageBox.showinfo("Adjust Intensity","This feature has not been implemented yet")
        
    def menuHelp(self):
        tkMessageBox.showinfo("Help","This feature has not been implemented yet")
        
    def menuAbout(self):
        tkMessageBox.showinfo("About LSM Module","LSM Module Demo v0.001\nCopyright (c) 2004 Juha Hyytiäinen, Jaakko Mäntymaa, Kalle Pahajoki, Jukka Varsaluoma")
        
    def quitApp(self):
        if tkMessageBox.askokcancel("Quit","Do you really wish to quit?"):
           self.root.destroy()


class ToolBar(Frame):
    def __init__(self,master):
        Frame.__init__(self,master,relief=RAISED)
        self.master=master
        self.btns=[]
        self.imgs=[]
        
    def insertButton(self,text,cmd,img=None):
        if not img:
            btn=Button(self,text=text,command=cmd)
        else:
            photoimg=PhotoImage(file=img)
            btn=Button(self,text=text,image=photoimg,command=cmd)
            self.imgs.append(photoimg)
        self.btns.append(btn)
        btn.pack(side=LEFT,padx=2,pady=2)

class StatusBar(Frame):
    def __init__(self,master):
        Frame.__init__(self,master)
        self.label=Label(self,bd=1,relief=SUNKEN,anchor=W)
        self.label.pack(fill=X)
    def set(self,format,*args):
        self.label.config(text=format%args)
        self.label.update_idletasks()
    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


root=Tk()
mainwin=MainWindow(root)

mainloop()


