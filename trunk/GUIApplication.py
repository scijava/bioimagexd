import wx
import scripting
import GUI.MainWindow
import GUI.SplashScreen
import os

class BXDGUIApplication(wx.App):
	"""
	Created: 03.11.2004, KP
	Description: Encapsulates the wxPython initialization and mainwindow creation
	"""
	def OnInit(self):
		"""
		Created: 10.1.2005, KP
		Description: Create the application's main window
		"""
		self.SetAppName("BioImageXD")
		iconpath = scripting.get_icon_dir()

		splashimage = os.path.join(iconpath, "splash2.jpg")
		self.splash = GUI.SplashScreen.SplashScreen(None, duration = 99000, bitmapfile = splashimage)
		self.splash.Show()
		self.splash.SetMessage("Loading BioImageXD...")
		provider = wx.SimpleHelpProvider()
		wx.HelpProvider_Set(provider)

		self.mainwin = GUI.MainWindow.MainWindow(None, -1, self, self.splash)
		self.mainwin.config = wx.Config("BioImageXD", style = wx.CONFIG_USE_LOCAL_FILE)
		scripting.app = self
		scripting.mainWindow = self.mainwin

		self.mainwin.Show(True)
		self.SetTopWindow(self.mainwin)

		return True

	def macOpenFile(self, filename):
		"""
		Created: 14.03.2007, KP
		Description: open a file that was dragged on the app
		"""
		self.mainwin.loadFiles([filename])

	def run(self, files, scriptfile, **kws):
		"""
		Created: 03.11.2004, KP
		Description: Run the wxPython main loop
		"""
		if files:
			self.mainwin.loadFiles(files)

		if scriptfile:
			self.splash.SetMessage("Loading script file %s..."%scriptfile)
			self.mainwin.loadScript(scriptfile)
		self.MainLoop()
