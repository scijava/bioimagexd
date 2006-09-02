class MayaViInterface:
    """
    This class defines the interface between MayaVi and the Animator.
    """

    def __init__(self,mayavi_gui):
        debug("In MayaViInterface::__init__()")

        self.mayavi_gui = mayavi_gui    # handles to mayavi and its GUI
        self.mayavi = mayavi_gui.mayavi

    def open_vtk_xml(self,filename,config=0):
        return self.mayavi.open_vtk_xml(filename, config)

    def get_render_window(self):
        return self.mayavi_gui.get_render_window()

    def update_label(self):
        self.mayavi_gui.update_label ()

    def get_current_dvm(self):
        return self.mayavi.get_current_dvm()

    def Render(self):
        self.mayavi_gui.Render()         

    def render(self):
        self.Render()         

    def open_vtk_xml_file (self, file_name, config=1, add_dvm=1): 
        """Open a VTK XML data file."""

        if not file_name:
            return
        try:
            rw = self.mayavi_gui.get_render_window()
            data = Sources.VtkXMLDataReader.VtkXMLDataReader (rw)
            if add_dvm:
                dvm = Base.DataVizManager.DataVizManager (data, rw)
                self.mayavi.add_dvm (dvm)
            Common.state.busy ()
            data.initialize (file_name)
            self.mayavi_gui.update_label ()
            Common.state.idle ()
            if config:
                data.configure (self.mayavi_gui.root)
            if add_dvm:
                dvm.add_module_mgr_gui ()
            return data
        except Exception, v:
            #exception ()
            Common.state.force_idle ()

    def __del__(self):
        debug("In MayViInterface::__del__()")

class DataHandler:
    """
    This class handles data manipulation in the Animator
    """

    def __init__(self,animator,mayavi_interface):
        debug("In DataHandler::__init__()")

        self.animator = animator
        self.mayavi_interface = mayavi_interface

        self.file_names = []
        self.next_file_name_index = 0
        
        self.data_src_map = {}
        self.data_map = {}

        self.dvm = None  # data visualization manager used by mayavi
        self.mm = None   # module manager

        self.time_dimension = 0

        self.input_dir = ""
        self.input_pattern = ""
        self.output_dir = ""
        self.output_pattern = ""
        self.output_type = ""


    def clear_data(self):
        self.data_src_map.clear()
        self.data_map.clear()
        self.remove_all_file_names()

    def show_message(self,msg):
        self.animator.show_message(msg)

    def open_vtk_xml(self,filename,config=0,add_dvm=1):
        if  self.file_exists(filename):
            self.append_data(filename, self.mayavi_interface.open_vtk_xml_file(filename, config, add_dvm))
        else:
            self.remove_file_name(filename)
            self.show_message("Can not open file %s"%filename)
            
    def open_many_vtk_xml(self):
        """
        This method reads data from the disk. File names which will
        be opened are being held in the self.file_names list.
        """
        self.clear_data()
        if len(self.file_names) == 0:
            self.process_file_names()
        for i in range(0,len(self.file_names)):
            self.show_message("Opening file %s"%(self.file_names[i]))
            if i == 0:
                self.open_vtk_xml(self.file_names[i],0,1) # add dvm to mayavi, only for the first file
            else:
                self.open_vtk_xml(self.file_names[i],0,0) # do not add dvm               
        self.set_time_dimension(len(self.file_names))

    def process_file_names(self):
        """
        This method forms the list which contains all the input file
        names. 
        """
        for i in range(0,self.time_dimension):
            filename = self.get_absolut_input_file_name(i)
            self.show_message("Processing file %s"%filename)
            try:
                self.add_file_name(filename)
            except Exception, v:
                self.show_message("Can not append data file %s"%filename)

    def append_data(self,key,data_src):
        self.data_src_map[key] = data_src
        self.data_map[key] = data_src.GetOutput()
        
    def file_exists(self,filename):
        """
        Just checking that given file really exists.
        """
        if os.path.isfile(filename):
            return 1
        return 0
        
    def add_file_name(self,filename):
        self.file_names.append(filename)

    def remove_all_file_names(self):
        """
        This could be done more sophisticated way?
        """
        if self.file_names:
            del self.file_names
        self.file_names = []

    def remove_file_name(self,filename):
        try:
            self.file_names.remove(filename)
        except:
            self.show_message("Failed removing file name %s"%filename)

    def set_time_dimension(self,dim):
        self.time_dimension = dim
        self.animator.set_time_dimension(dim)

    def get_time_dimension(self):
        return self.time_dimension

    def get_next_input_file_name(self):
        if self.next_file_name_index >= self.time_dimension:
            self.next_file_name_index = 0
        name = self.get_absolut_input_file_name(self.next_file_name_index)
        self.next_file_name_index = self.next_file_name_index + 1
        return name

    def get_absolut_input_file_name(self,i):
        """
        Form input file name that has an absolut directory path. This
        is done using Pythons platform independent methods.
        """
        dir = self.input_dir
        if not dir:
            dir = ""
        return os.path.normpath(os.path.join(dir,self.get_input_file_name(i)))

    def get_input_file_name(self,i):
        """
        Form input file name from user specified pattern. If pattern
        consists % then it will be replaced by number i. So, file name
        pattern might be of form file_name%d.vti and in this case %d
        is replaced by parameter i.
        """
        file = self.input_pattern
        if file.find("%") > 0:
            file = eval("file%i")
        return file

    def get_absolut_out_file_name(self,i):
        """
        Form output file name that has an absolut directory path. This
        is done using Pythons platform independent methods.
        """
        path = ""
        dir = self.output_dir
        file = self.get_output_file_name(i)
        if len(file) > 0:
            # if directory is empty the default dir will be .
            path = os.path.normpath(os.path.join(dir,file))
        return path
        
    def get_output_file_name(self,i):
        """
        Form output file name from user specified pattern. If pattern
        consists % then it will be replaced by number i. So, file name
        pattern might be of form file_name%d.vti and in this case %d
        is replaced by parameter i.
        """
        file = self.output_pattern
        if not file or len(file) == 0:
            return ""
        file_type = self.output_type
        file = file+"."+file_type
        if file.find("%") > 0:
            file = eval("file%i")        
        return file

    def get_current_module_manager(self):
        return self.mm

    def get_data_src(self,key):
        if not key and type(key) == type("string"):
            self.show_message("key is null")
            return None
        if type(key) == type("string"):
            if not self.data_src_map.has_key(key):
                return None
            return self.data_src_map[key]
        elif type(key) == type(1):
            if (key < 0 or key > len(self.file_names)-1):
                return None
            k = self.file_names[key]
            if not self.data_src_map.has_key(k) :
                return None
            self.next_file_name_index = key + 1
            return self.data_src_map[k]
        #return None

    def get_data(self,key):
        if not key or not self.data_map.has_key(key):
            return None
        return self.data_map[key]

    def set_next_data_set(self):
        self.change_data(self.get_next_input_file_name())

    def change_data(self,key):
        """
        Change the data set mayavi is rendering.
        """
        self.show_message("Changing data: %s"%key)
        try:
            data_src = self.get_data_src(key)
            if not data_src:
                return 
            self.set_mayavi_gui_data(data_src)
            self.mayavi_interface.update_label ()
            #self.set_mayavi_gui_data(data_src)
            self.show_message("Data has been changed to %s"%key)
            return data_src
        except Exception, v:
            #exception ()
            Common.state.force_idle ()

    def set_mayavi_gui_data(self,data_src):
        """
        Change the data set mayavi is rendering.
        """
        self.dvm = dvm = self.mayavi_interface.get_current_dvm()        
        dvm.data_src = data_src
        self.mm = mm = dvm.get_current_module_mgr()
        mm.data_src = data_src
        mm.Update(render=0)

    def get_mayavi_gui_data(self,key):
        self.dvm = dvm = self.mayavi_interface.get_current_dvm()
        if dvm:
            self.append_data(key,dvm.get_data_source())
            self.mm = dvm.get_current_module_mgr()

    def get_center(self):
        if len(self.file_names) < 1:
            return [0,0,0]
        return self.data_map[self.file_names[self.animator.get_curr_time_point()-1]].GetCenter()
        
    def data_width(self):
        return self.data_dimension(0)

    def data_height(self):
        return self.data_dimension(1)

    def data_depth(self):
        return self.data_dimension(2)
        
    def data_dimension(self,dim):
        if len(self.file_names) < 1 or (dim < 0 or dim > 2):
            return 0
        return (self.data_map[self.file_names[self.animator.get_curr_time_point()-1]].GetDimensions())[dim]

    def time_dimension(self):
        return len(self.data_src_map)


    def __del__(self):
        debug("In DataHandler::__del__()")

class MayaViAnimatorGUI:
    """ Creates the user interface for making animations."""

    def __init__(self, master, gui):
        debug ("In Animator::__init__ ()")

        self.mayavi_gui = gui
        self.mayavi_interface = MayaViInterface(gui)        

        self.x = Tkinter.IntVar()
        self.y = Tkinter.IntVar()
        self.z = Tkinter.IntVar()
        self.time = Tkinter.IntVar()

        self.control_points = Tkinter.IntVar()
        self.control_points.set(5)
        self.frames_per_timepoint = Tkinter.IntVar()
        self.frames_per_timepoint.set(1)
        self.out_dir = Tkinter.StringVar()
        self.out_file_pattern = Tkinter.StringVar()
        self.out_file_type = Tkinter.StringVar()

        self.rendering_status = Tkinter.StringVar()

        self.input_filename_pattern = ""
        self.curr_input_filename = ""
        self.input_dir = ""
        self.used_input_files = 0
        
        self.master = master
        self.root = Tkinter.Toplevel(master)
        self.root.title("MayaVi Animator")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.minsize (600, 400)

        # next two lines must be in this order.
        self.make_gui()
        self.animator = MayaViAnimator(self.root,self.mayavi_interface,self,self.spline_f)


    def make_animation(self):
        self.animator.set_output_dir(self.out_dir.get())
        self.animator.set_output_pattern(self.out_file_pattern.get())
        self.animator.set_output_file_type(self.out_file_type.get())
        self.animator.make_animation()

    def make_new_rand_spline(self):
        self.animator.init_spline(self.control_points.get())


    def set_rendering_status(self,status):
        """
        Just showing some strings in the main window. May not be
        working properly, maybe some update-method needed..
        """
        #print status
        self.rendering_status.set(status)


    def get_timepoints_num(self):
        return self.time.get()


    def get_frames(self):
        ret = 0
        try:
            ret = self.get_frames_per_timepoint() * self.get_timepoints_num()
        except:
            pass
        return ret

    def get_frames_per_timepoint(self):
        ret = 0
        try:
            ret = self.frames_per_timepoint.get()
        except:
            pass
        return ret
    

    def open_many_vtk_xml(self):
        t = MyDialog(self.root,"Open many VTK XML files");
        self.set_input_dir(t.dir)
        self.set_input_filename_pattern(t.filename)
        self.set_timepoints(int(t.dimension))
        self.animator.open_many_vtk_xml()
        
    def change_data(self,event=None):
        self.animator.change_data(self.data_set_scale.get()-1)
        self.mayavi_interface.render()

    def set_timepoints(self,points):
        self.time.set(points)
        self.data_set_scale.configure(to=self.get_timepoints_num())

    def set_input_dir(self,d):
        if not d:
            d = ""
        self.input_dir = d

    def set_input_filename_pattern(self,p):
        if not p:
            p = ""
        self.input_filename_pattern = p

    def make_menus(self):
        self.menu = Tkinter.Menu (self.root, tearoff=0)
	self.root.config (menu=self.menu)

	self.file_menu = Tkinter.Menu (self.menu, name='file', tearoff=0)
	self.help_menu = Tkinter.Menu (self.menu, name='help', tearoff=0)
	self.menu.add_cascade (label="File", menu=self.file_menu, 
			       underline=0)
	self.menu.add_cascade (label="Help", menu=self.help_menu, 
			       underline=0)
        self.open_menu = Tkinter.Menu (self.file_menu, tearoff=0)
        self.file_menu.add_cascade (label="Open", underline=0,
                                    menu=self.open_menu)
	#self.open_menu.add_command (label="VTK file", underline=0,
		#		    command=self.open_vtk)
	#self.open_menu.add_command (label="VTK XML file", underline=4,
	#			    command=self.open_vtk_xml)
	self.open_menu.add_command (label="Many VTK XML files", underline=1,
				    command=self.open_many_vtk_xml)
        self.file_menu.add_command (label="Exit", underline=1, 
                                    command=self.quit)

        self.help_menu.add_command (label="About", underline=1, 
                                    command=self.show_about_msg)

    def make_gui(self):
        self.make_menus()

        self.master_info_f = Tkinter.Frame(self.root, relief='sunken', bd=2)
        self.master_info_f.grid(row=0,column=0,sticky="N");

        self.data_info_f = Tkinter.Frame(self.master_info_f, relief='sunken', bd=2)
        self.data_info_f.grid(row=0,column=0,sticky="W"+"E");

        self.spline_f = Tkinter.Frame(self.root, relief='sunken', bd=2)#,width="400",height="300",bg="green")
        self.spline_f.grid(row=0,column=1,sticky="W"+"E"+"S"+"N");

        self.bottom_f = Tkinter.Frame(self.root,height="30",bg="red")
        self.bottom_f.grid(row=1,column=0);

        self.message_f = Tkinter.Frame(self.root,height="100")
        self.message_f.grid(row=2,column=0,columnspan="2",sticky="W");

        # data set chooser

        rows = 0
        w = Tkinter.Label(self.data_info_f, text="Choose data set:")
        w.grid(row=rows,column=0,sticky="W")

        rows = rows + 1
        self.data_set_scale = Tkinter.Scale(self.data_info_f, orient=Tkinter.HORIZONTAL, \
                      from_=1, to=1, length="300",tickinterval=2)
        self.data_set_scale.set(1)
        
        self.data_set_scale.grid (row=rows,column=0,columnspan="2",sticky="W"+"E")
        self.data_set_scale.bind ("<ButtonRelease>",self.change_data)

        # information about the data

        rows = rows+1
        w = Tkinter.Label(self.data_info_f, text="Information about the data:")
        w.grid(row=rows,column=0,columnspan="2",sticky="W")

        txtvar = [("X-dimension:",self.x),("Y-dimension:",self.y),("Z-dimension:",self.z),("Time points:",self.time)]
        for txt,var in txtvar:
            rows = rows+1
            w = Tkinter.Label(self.data_info_f, text=txt).grid(row=rows,column="0",sticky="W")
            w = Tkinter.Label(self.data_info_f, textvariable=var,bd="0",width="10",relief="sunken",anchor="w").grid(row=rows,column="1",sticky="W")
        

        # spline parameters

        rows = rows+1
        self.animation_spline_f = Tkinter.Frame(self.master_info_f, relief='sunken', bd=2)
        self.animation_spline_f.grid(row=rows,column=0,sticky="W"+"E");

        rw = 0
        w = Tkinter.Label(self.animation_spline_f, text="Parameters for spline:")
        w.grid(row=rw,column=0,columnspan="2",sticky="W")

        rw = rw+1
        w = Tkinter.Label(self.animation_spline_f, text="Number of control points:",anchor="w").grid(row=rw,column="0",sticky="W")
        w = Tkinter.Entry(self.animation_spline_f, textvariable=self.control_points,bd="2",width="10",relief="sunken").grid(row=rw,column="1",sticky="W")

        rw = rw+1
        self.make_new_rand_spline = Tkinter.Button(self.animation_spline_f, text="New random spline", command=self.make_new_rand_spline,state=Tkinter.DISABLED)
        self.make_new_rand_spline.grid(row=rw,columnspan="2",sticky="W");

        # animation parameters
        
        rows = rows+1
        self.animation_info_f = Tkinter.Frame(self.master_info_f, relief='sunken', bd=2)
        self.animation_info_f.grid(row=rows,column=0,sticky="W"+"E");

        rw = 0
        w = Tkinter.Label(self.animation_info_f, text="Parameters for animation:")
        w.grid(row=rw,column=0,columnspan="2",sticky="W")

        txtvars = {"Frames per time point:":self.frames_per_timepoint,"Output directory:":self.out_dir,"Output file name pattern:":self.out_file_pattern}
        for txt,var in txtvars.iteritems():
            rw = rw+1
            w = Tkinter.Label(self.animation_info_f, text=txt).grid(row=rw,column="0",sticky="W")
            w = Tkinter.Entry(self.animation_info_f, textvariable=var,bd="2",width="20",relief="sunken").grid(row=rw,column="1",sticky="W")


        TYPES = [
            ("BMP", "bmp"),
            ("PNG", "png"),
            ("TIFF", "tiff"),
            #("JPEG", "jpg"),
            ]
        
        self.out_file_type.set("tiff") # initialize
    
        rw = rw+1
        w = Tkinter.Label(self.animation_info_f, text="Save files as:").grid(row=rw,column="0",sticky="W",rowspan="3")
        for text, type in TYPES:
            b = Tkinter.Radiobutton(self.animation_info_f, text=text,
                            variable=self.out_file_type, value=type)
            b.grid(row=rw,column="1",sticky="W")
            rw = rw+1


        # progress frame
        rows = rows+1
        self.animation_progress_f = Tkinter.Frame(self.master_info_f, relief='sunken', bd=0)
        self.animation_progress_f.grid(row=rows,column=0,sticky="W");
        self.set_rendering_status("Not started")
        rw = 0
        w = Tkinter.Label(self.animation_progress_f, text="Rendering status:").grid(row=rw,column="0",sticky="E")
        w = Tkinter.Label(self.animation_progress_f, textvariable=self.rendering_status).grid(row=rw,column="1",sticky="W")

        # THE button
        self.make_animation = Tkinter.Button(self.bottom_f, text="Make animation", command=self.make_animation,state=Tkinter.DISABLED)
        self.make_animation.grid(row=0,columnspan="2",sticky="W");

        # messages
        self.show_messages_var = Tkinter.IntVar()
        c = Tkinter.Checkbutton(self.message_f, text="Show messages",
                        variable=self.show_messages_var, command=self.show_messages)
        c.grid(row=0,column=0,sticky="W")

        self.message = Tkinter.StringVar()

        self.messages = Tkinter.Text(self.message_f,relief="sunken",width="100",height="10")#,yscrollcommand=self.messages_scrollbar.set)
        self.messages.insert(Tkinter.END,' ')
        
        self.messages_scrollbar = Tkinter.Scrollbar(self.messages)
        self.messages_scrollbar.config(command=self.messages.yview)

    def show_messages(self,event=None):
        if self.show_messages_var.get() > 0:
            self.messages.grid(row=1,column=0,sticky="W"+"E")
        else:
            self.messages.grid_forget()

    def show_message(self,msg):
        self.messages.insert(1.0,msg+'\n')

    def show_about_msg (self):
        msg = "The MayaVi Data Visualizer's Animation tool\n\n"\
              "A free, powerful, scientific data visualizer written "\
              "in Python.\n\n"\
              "Version: 0.1\n\n"\
              "License: BSD\n\n"\
              "Home page: http://mayavi.sourceforge.net\n\n"\
              "(c) Heikki Uuksulainen 2004\n"
        return tkMessageBox.showinfo ("About MayaViAnimator", msg)


    def __del__(self):
        debug ("In AnimatorGUI::__del__ ()")
        print "In AnimatorGUI::__del__ ()"
        #del self.splineEditor
        #self.root.destroy ()
        self.quit()
        
    def quit (self, event=None):
        print "AnimatorGUI.quit()"
        debug ("In AnimatorGUI::quit ()")
        #self.animator.quit()
        del self.animator
        self.root.destroy ()
        self.mayavi_gui.animator = False
        
