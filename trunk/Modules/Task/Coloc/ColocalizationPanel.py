# -*- coding: iso-8859-1 -*-
"""
 Unit: ColocalizationPanel
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A window that is used to control the settings for the
 colocalization module. Expects to be handed a ColocalizationDataUnit()
 containing the datasets from which the colocalization map is generated.

 Copyright (C) 2005	 BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
__author__ = "BioImageXD Project <http://www.bioimagexd.org>"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

from GUI.UIElements import AcceptedValidator 
import codecs
import csv
from GUI.ColorTransferEditor import CTFButton
from lib import ImageOperations
import lib.Command
import lib.messenger
import Logging 
import GUI.Dialogs
import GUI.PreviewFrame
import os.path
from GUI.Scatterplot import Scatterplot
import string
from GUI.TaskPanel import TaskPanel
import time
import types
import vtk
import vtkbxd
import wx
import scripting
import GUI.ColocListView
import bxdevents
		
class ColocalizationPanel(TaskPanel):
	"""
	The GUI for colocalization task
	"""
	def __init__(self, parent, tb):
		self.scatterPlot = None
		self.createItemSelection = 0
		self.timePoint = 0		  
		TaskPanel.__init__(self, parent, tb, wantNotebook = 0)

		self.operationName = "Colocalization"
		self.voxelSize = None
			
		self.mainsizer.Layout()
		self.mainsizer.Fit(self)
		lib.messenger.connect(None, "timepoint_changed", self.updateTimepoint)
		lib.messenger.connect(None, "zslice_changed", self.updateZSlice)
		lib.messenger.connect(None, "threshold_changed", self.updateSettings)
		lib.messenger.connect(None, bxdevents.DATA_DIMENSIONS_CHANGED, self.onDataChanged)

	def deregister(self):
		"""
		Removes all listeners
		"""
		TaskPanel.deregister(self)
		try:
			lib.messenger.disconnect(None, "timepoint_changed", self.updateTimepoint)
			lib.messenger.disconnect(None, "zslice_changed", self.updateZSlice)
			lib.messenger.disconnect(None, "threshold_changed", self.updateSettings)
			lib.messenger.disconnect(None, "data_changed", self.onDataChanged)
		except:
			pass
			
	def autoThreshold(self):
		"""
		Use vtkAutoThresholdColocalization to determine thresholds
					 for colocalization and calculate statistics
		"""
		self.clearVariables()
		self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds", 1)
		self.eventDesc = "Calculating thresholds"
		
		self.doPreviewCallback(None)
		self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds", 0) 
		
		lib.messenger.send(None, "threshold_changed")	 
		
	def getAutoThreshold(self, event = None):
		"""
		Calculate the automatic threshold for colocalization
		"""
		do_cmd = """scripting.mainWindow.tasks['Colocalization'].autoThreshold()"""
		cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
									desc = "Calculate automatic threshold")
		cmd.run()
		
	def statistics(self):
		"""
		Calculate the statistics
		"""
		self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds", 2)
		self.eventDesc = "Calculating statistics"
		self.doPreviewCallback(None)
		self.dataUnit.getSourceDataUnits()[0].getSettings().set("CalculateThresholds", 0) 
				
		
		
	def getStatistics(self, event = None):
		"""
		Method: getStatistics
		Use vtkAutoThresholdColocalization to determine thresholds
					 for colocalization and calculate statistics
		"""
		do_cmd = """scripting.mainWindow.tasks['Colocalization'].statistics()"""
		cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
									desc = "Calculate colocalization statistics")
		cmd.run()
		pos = self.radiobox.GetSelection()
		if pos:
			map = [1, 0, 2]
			method = map[pos - 1]
			smethod = ""
			if method == 0:
				smethod = "Fay"
			if method == 1:
				smethod = "Costes"
			if method == 2:
				smethod = "van Steensel"
			
			try:
				n = int(self.iterations.GetValue())
				iterations = ", iterations = %d" % n
			except:
				pass
			if method != 1:
				iterations = ""
			do_cmd = "scripting.mainWindow.tasks['Colocalization'].getPValue('%s'%s)" % (smethod, iterations)
			cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
										desc = "Calculate P-Value of colocalization")
			cmd.run()
		
	def getPValue(self, method = 1, iterations = 100):
		"""
		Method: getPValue
		Get the P value for colocalization
		"""
		try:
			n = int(self.iterations.GetValue())
			if n != iterations:
				self.iterations.SetValue("%d" % iterations)
		except:
			pass
		
		coloctest = vtkbxd.vtkImageColocalizationTest()
		#coloctest.SetRandomizeZ(1)
		sources = self.dataUnit.getSourceDataUnits()
		self.eventDesc = "Calculating P-Value"
		methods = ["Fay", "Costes", "van Steensel"]
		if type(method) == types.StringType:
			method = methods.index(method)
		
		Logging.info("Using %s method (%d)" % (methods[method], method), kw = "processing")
		t = time.time()
		
		coloctest.SetMethod(method)
		
		try:
			n = float(self.fixedPSF.GetValue())
		except:
			lib.messenger.send(None, "show_error", "Bad PSF width", \
								"The given width for point spread function is invalid.")
			return
		print "Setting PSF width", int(n)
		coloctest.SetManualPSFSize(int(n))

		coloctest.SetNumIterations(iterations)
		
		for i in sources:
			data = i.getTimepoint(self.timePoint)
			coloctest.AddInput(data)
		coloctest.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(coloctest, "ProgressEvent", self.updateProgress)
		
		coloctest.Update()
		print "It took ", time.time() - t, "seconds to calculate p-value"
		set = sources[0].getSettings().set
		for i in ["PValue", "RObserved", "RRandMean", "RRandSD",
				  "NumIterations", "ColocCount", "Method"]:
			val = eval("coloctest.Get%s()" % i)
			set(i, val)
		lib.messenger.send(None, "update_progress", 100, "Done.")
		self.listctrl.updateListCtrl(self.getVariables())
		
		
	def updateProgress(self, obj, evt, *args):
		"""
		Method: updateProgress
		Sends a update_progress event and yields time for the GUI
		"""
		wx.GetApp().Yield(1)
		progress = obj.GetProgress()
		txt = obj.GetProgressText()
		if not txt:
			txt = self.eventDesc
		lib.messenger.send(None, "update_progress", progress, txt)
		
	def createButtonBox(self):
		"""
		Creates a button box containing the buttons Render, 
					 Preview and Close
		"""
		TaskPanel.createButtonBox(self)
		lib.messenger.connect(None, "process_dataset", self.doColocalizationCallback)		 

	def createOptionsFrame(self):
		"""
		Creates a frame that contains the various widgets
					 used to control the colocalization settings
		"""
		#TaskPanel.createOptionsFrame(self)
#		 self.colocalizationPanel=wx.Panel(self.settingsNotebook,-1)
		self.colocalizationPanel = wx.Panel(self, -1)
		self.colocalizationSizer = wx.GridBagSizer()
		n = 0

		self.lowerThresholdLbl1 = wx.StaticText(self.colocalizationPanel, -1, "Ch1 lower threshold:")
		self.upperThresholdLbl1 = wx.StaticText(self.colocalizationPanel, -1, "Ch1 upper threshold:")
		self.lowerThresholdLbl2 = wx.StaticText(self.colocalizationPanel, -1, "Ch2 lower threshold:")
		self.upperThresholdLbl2 = wx.StaticText(self.colocalizationPanel, -1, "Ch2 upper threshold:")
		
		self.lowerthreshold1 = wx.Slider(self.colocalizationPanel, value = 128, minValue = 1, \
											maxValue = 255, size = (300, -1),
		style = wx.SL_HORIZONTAL | wx.SL_LABELS)
		self.lowerthreshold1.Bind(wx.EVT_SCROLL, self.updateThreshold)
		self.upperthreshold1 = wx.Slider(self.colocalizationPanel, value = 128, minValue = 1, \
											maxValue = 255, size = (300, -1),
		style = wx.SL_HORIZONTAL | wx.SL_LABELS)
		self.upperthreshold1.Bind(wx.EVT_SCROLL, self.updateThreshold)

		self.lowerthreshold2 = wx.Slider(self.colocalizationPanel, value = 128, minValue = 1, \
											maxValue = 255, size = (300, -1),
		style = wx.SL_HORIZONTAL | wx.SL_LABELS)
		self.lowerthreshold2.Bind(wx.EVT_SCROLL, self.updateThreshold)
		self.upperthreshold2 = wx.Slider(self.colocalizationPanel, value = 128, minValue = 1, \
											maxValue = 255, size = (300, -1),
		style = wx.SL_HORIZONTAL | wx.SL_LABELS)
		self.upperthreshold2.Bind(wx.EVT_SCROLL, self.updateThreshold)
		
		self.colocalizationSizer.Add(self.lowerThresholdLbl1, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.lowerthreshold1, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.upperThresholdLbl1, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.upperthreshold1, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.lowerThresholdLbl2, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.lowerthreshold2, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.upperThresholdLbl2, (n, 0))
		n += 1
		self.colocalizationSizer.Add(self.upperthreshold2, (n, 0))
		n += 1
		sbox = wx.StaticBox(self.colocalizationPanel, -1, "2D histogram (right-click for more options)")
		box = wx.StaticBoxSizer(sbox, wx.VERTICAL)
		self.scatterPlot = Scatterplot(self.colocalizationPanel, drawLegend = 1)
		lib.messenger.connect(self.scatterPlot, "scatterplot_thresholds", self.onUpdateScatterplotThresholds)
		box.Add(self.scatterPlot)
		self.colocalizationSizer.Add(box, (n, 0))
		n += 1
		
		sbox = wx.StaticBox(self.colocalizationPanel, -1, "Colocalization quantification")
		box = wx.StaticBoxSizer(sbox, wx.VERTICAL)
		self.automaticThresholdStaticBox = sbox
		self.automaticThresholdSizer = box
		#self.pvaluebox = wx.StaticBox(self.colocalizationPanel, -1, "Calculate P-Value")
		self.radiobox = wx.RadioBox(self.colocalizationPanel, -1, "Calculate P-Value",
		choices = ["None", "Costes", "Fay", "van Steensel"], majorDimension = 2,
		style = wx.RA_SPECIFY_COLS
		)
		self.radiobox.Bind(wx.EVT_RADIOBOX, self.onSetTestMethod)
		#self.pvalueNone = wx.RadioButton(self.colocalizationPanel, -1, "None", name="pvalue")
		#self.pvalueNone.SetValue(True)
		#self.pvalueNone.Bind(wx.EVT_RADIOBUTTON, self.onSetNone)
		#self.pvalueCostes = wx.RadioButton(self.colocalizationPanel, -1, "Costes", name="pvalue")
		#self.pvalueCostes.SetValue(False)
		#self.pvalueCostes
		#self.pvalueFay = wx.RadioButton(self.colocalizationPanel, -1, "Fay", name="pvalue")
		#self.pvalueFay.SetValue(False)
		#self.pvaluevanSteensel = wx.RadioButton(self.colocalizationPanel, -1, "van Steensel", name="pvalue")
		#self.pvaluevanSteensel.SetValue(False)
		box.Add(self.radiobox)
		self.iterLbl = wx.StaticText(self.colocalizationPanel, -1, "Iterations:")
		self.iterations = wx.SpinCtrl(self.colocalizationPanel, -1, "100", min = 2, \
										max = 999, initial = 100)
		
		fixedPSFLbl = wx.StaticText(self.colocalizationPanel, -1, "PSF radius (px):")
		self.fixedPSF = wx.TextCtrl(self.colocalizationPanel, -1, "")
		
		costesgrid = wx.GridBagSizer()
		#sboxsizer.Add(costesgrid)
		costesgrid.Add(self.iterLbl, (0, 0))
		costesgrid.Add(self.iterations, (0, 1))

		costesgrid.Add(fixedPSFLbl, (1, 0))
		costesgrid.Add(self.fixedPSF, (1, 1))
		NALbl = wx.StaticText(self.colocalizationPanel, -1, "Numerical Aperture:")
		self.NA = wx.TextCtrl(self.colocalizationPanel, -1, "1.4")
		costesgrid.Add(NALbl, (2, 0))
		costesgrid.Add(self.NA, (2, 1))
		Ch2LambdaLbl = wx.StaticText(self.colocalizationPanel, -1, u"Ch2 \u03BB (nm):")
		self.Ch2Lambda = wx.TextCtrl(self.colocalizationPanel, -1, "520")
		costesgrid.Add(Ch2LambdaLbl, (3, 0))
		costesgrid.Add(self.Ch2Lambda, (3, 1))
		#pvaluebox.Add(costesgrid)
		
		self.NA.Bind(wx.EVT_TEXT, self.onUpdatePSF)
		self.Ch2Lambda.Bind(wx.EVT_TEXT, self.onUpdatePSF)

		self.iterations.Enable(0)
		self.NA.Enable(0)
		self.Ch2Lambda.Enable(0)
		self.fixedPSF.Enable(0)
 
		box.Add(costesgrid)
		
		box2 = wx.BoxSizer(wx.HORIZONTAL)
		self.statsButton = wx.Button(self.colocalizationPanel, -1, "Calculate statistics")
		self.statsButton.Bind(wx.EVT_BUTTON, self.getStatistics)
		box2.Add(self.statsButton)		  
		self.thresholdButton = wx.Button(self.colocalizationPanel, -1, "Calculate thresholds")
		self.thresholdButton.Bind(wx.EVT_BUTTON, self.getAutoThreshold)
		box2.Add(self.thresholdButton) 
		self.statsButtonSizer = box2
		box.Add(box2)
		self.colocalizationSizer.Add(box, (n, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		n += 1
		
		sbox = wx.StaticBox(self.colocalizationPanel, -1, "Coloc Volume Statistics")
		box = wx.StaticBoxSizer(sbox, wx.VERTICAL)
		self.colocStatsStaticBox = sbox
		self.colocStatsSizer = box
		
		self.listctrl = GUI.ColocListView.ColocListView(self.colocalizationPanel, -1, size = (350, 300))
		box.Add(self.listctrl)
		self.statsButton = wx.Button(self.colocalizationPanel, -1, "Export")
		self.statsButton.Bind(wx.EVT_BUTTON, self.onExportStatistics)
		box.Add(self.statsButton)

		self.listctrl.updateListCtrl(self.getVariables())
		self.colocalizationSizer.Add(box, (n, 0))
		n += 1
		sbox = wx.StaticBox(self.colocalizationPanel, -1, "Colocalization color")
		sboxsizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
		self.colocColorBox = sbox
		self.colocColorSizer = sboxsizer
		self.colorBtn = CTFButton(self.colocalizationPanel)
		sboxsizer.Add(self.colorBtn)

		val = AcceptedValidator
 
		self.constColocCheckbox = wx.CheckBox(self.colocalizationPanel, -1, \
												"Use single (1-bit) value for colocalization")
		self.constColocValue = wx.TextCtrl(self.colocalizationPanel, -1, "255",
									validator = val(string.digits, below = 255))
		self.constColocValue.Enable(0)

		self.constColocCheckbox.Bind(wx.EVT_CHECKBOX,
		lambda e, s = self, v = self.constColocValue:v.Enable(e.IsChecked()))
		
		sboxsizer.Add(self.constColocCheckbox)
		sboxsizer.Add(self.constColocValue)
		
		self.colocalizationSizer.Add(sboxsizer, (n, 0))
		n += 1
		self.colocalizationPanel.SetSizer(self.colocalizationSizer)
		self.colocalizationPanel.SetAutoLayout(1)
		
		self.settingsSizer.Add(self.colocalizationPanel, (1, 0), flag = wx.EXPAND | wx.ALL)
		
#		 self.settingsNotebook.AddPage(self.colocalizationPanel,"Colocalization")
	
	def onUpdateScatterplotThresholds(self, scatterplot, event, ch1thresholds, ch2thresholds):
		"""
		Updates the colocalization thresholds based on user's scatterplot drawing
		"""
		ch1lower, ch1upper = ch1thresholds
		ch2lower, ch2upper = ch2thresholds
		sources = self.dataUnit.getSourceDataUnits()
		print "Setting thresholds to",ch1lower, ch1upper, ch2lower, ch2upper
		sources[0].getSettings().set("ColocalizationLowerThreshold", ch1lower)
		sources[0].getSettings().set("ColocalizationUpperThreshold", ch1upper)
		sources[1].getSettings().set("ColocalizationLowerThreshold", ch2lower)
		sources[1].getSettings().set("ColocalizationUpperThreshold", ch2upper)
		lib.messenger.send(None, "threshold_changed", (ch1lower, ch1upper), (ch2lower, ch2upper))
		lib.messenger.send(None, "data_changed", True)
		
		
	def onUpdatePSF(self, event):
		"""
		Update the PSF based on the given NA and lambda
		"""
		if event:
			event.Skip()
		if not self.voxelSize:
			sources = self.dataUnit.getSourceDataUnits()
			if sources:
				self.voxelSize = sources[0].getVoxelSize()
			else:
				return
		vx, vy, vz = self.voxelSize
		try:
			l = float(self.Ch2Lambda.GetValue())
			na = float(self.NA.GetValue())
		except:
			
			return
		
		psf = (0.61 * l) / na
		
		# psf is now in nanometers
		psf /= (vx * 1000 * 1000000)
		self.fixedPSF.SetValue("%.4f" % float(psf))
		
		
	def onSetTestMethod(self, event):
		"""
		Set the method used for colocalisation test
		"""
		n = self.radiobox.GetSelection()
		flag = (n == 1)
		self.iterations.Enable(flag)
		self.NA.Enable(flag)
		self.Ch2Lambda.Enable(flag)
		self.fixedPSF.Enable(flag)
		

	def onExportStatistics(self, event):
		"""
		Export colocalization statistics to file
		"""
		
		name = self.dataUnit.getName()
		filename = GUI.Dialogs.askSaveAsFileName(self, "Save colocalization statistics as", \
													"%s.csv" % name, "CSV File (*.csv)|*.csv")
		if filename:
			filename = filename.replace("\\", "\\\\")
			do_cmd = "scripting.mainWindow.tasks['Colocalization'].exportStatistics('%s')" % filename
			cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
										desc = "Export colocalization statistics")
			cmd.run()
		
		
	def decode(self, d):
		"""
		Replace any unicode characeters with their ascii counterparts
		"""
		d = d.replace(u"\u00B1", "+-")
		return d
		
	def exportStatistics(self, filename):
		"""
		Export the colocalization stats
		"""	  
		name = self.dataUnit.getName()
		sources = self.dataUnit.getSourceDataUnits()
		names = []
		names2 = []
		names = [x.getName() for x in sources]
		names2 = [os.path.basename(x.getFileName()) for x in sources]
		
		names3 = names2[:]
				
		namestr = " and ".join(names)
		leadstr = "From file "
		if len(names3) > 1:
			leadstr = "From files "
		namestr2 = leadstr + " and ".join(names3)

		if not filename:
			Logging.info("Got no name for coloc statistics", kw = "processing")
			return
		f = codecs.open(filename, "wb", "latin-1")
		
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		get1 = sources[0].getSettings().get
		get2 = sources[1].getSettings().get

		w.writerow(["Statistics for colocalization of channels %s" % namestr])
		w.writerow([namestr2])
		w.writerow(["Timepoint", self.timePoint])
		w.writerow([time.ctime()])
		for item in self.listctrl.headervals:
			header, val1, val2, col = item
			header = self.decode(header)
			if type(val1) == types.UnicodeType:
				val1 = self.decode(val1)
				
			if val2:
				if type(val2) == types.UnicodeType:
					val2 = self.decode(val2)
				
				w.writerow([header, val1, val2])
			else:
				w.writerow([header, val1])
		f.close()
		del w
		del f
		
			
	def updateZSlice(self, obj, event, zslice):
		"""
		A callback function called when the zslice is changed
		"""
		if self.scatterPlot:
			self.scatterPlot.setZSlice(zslice)
			self.scatterPlot.updatePreview()
			self.listctrl.updateListCtrl(self.getVariables())

	def updateTimepoint(self, obj, event, timePoint):
		"""
		A callback function called when the timepoint is changed
		"""
		self.timePoint = timePoint
		if self.scatterPlot:
			self.scatterPlot.setTimepoint(self.timePoint)
			self.scatterPlot.updatePreview()

	def updateThreshold(self, event):
		"""
		A callback function called when the threshold is configured via the slider
		"""
		# We might get called before any channel has been selected.
		# In that case, do nothing
		if self.settings:
			self.clearVariables()
			oldlthreshold1 = self.settings.getCounted("ColocalizationLowerThreshold", 0)
			olduthreshold1 = self.settings.getCounted("ColocalizationUpperThreshold", 0)
			newlthreshold1 = int(self.lowerthreshold1.GetValue())
			newuthreshold1 = int(self.upperthreshold1.GetValue())
			self.settings.setCounted("ColocalizationLowerThreshold", 0, newlthreshold1)
			self.settings.setCounted("ColocalizationUpperThreshold", 0, newuthreshold1)
			
			oldlthreshold2 = self.settings.getCounted("ColocalizationLowerThreshold", 1)
			olduthreshold2 = self.settings.getCounted("ColocalizationUpperThreshold", 1)
			newlthreshold2 = int(self.lowerthreshold2.GetValue())
			newuthreshold2 = int(self.upperthreshold2.GetValue())
			self.settings.setCounted("ColocalizationLowerThreshold", 1, newlthreshold2)
			self.settings.setCounted("ColocalizationUpperThreshold", 1, newuthreshold2)
			if (oldlthreshold1 != newlthreshold1) or (olduthreshold1 != newuthreshold1) or (oldlthreshold2 != newlthreshold2) or (olduthreshold2 != newuthreshold2):
				lib.messenger.send(None, "threshold_changed")
				self.doPreviewCallback()
				

	def updateSettings(self, force = 0, *args):
		"""
		A method used to set the GUI widgets to their proper values
					 based on the selected channel, the settings of which are 
					 stored in the instance variable self.settings
		"""
		Logging.info("Updating coloc settings", kw="processing")
		if self.settings:
			format = self.settings.get("ColocalizationDepth")
			scalar = self.settings.get("OutputScalar")
			self.constColocCheckbox.SetValue(format == 1)
			self.constColocValue.SetValue("%d" % scalar)
			
			th = self.settings.getCounted("ColocalizationLowerThreshold", 0)
			if th != None:
				self.lowerthreshold1.SetValue(th)
			th = self.settings.getCounted("ColocalizationUpperThreshold", 0)
			if th != None:
				self.upperthreshold1.SetValue(th)
			th = self.settings.getCounted("ColocalizationLowerThreshold", 1)
			if th != None:
				self.lowerthreshold2.SetValue(th)
			th = self.settings.getCounted("ColocalizationUpperThreshold", 1)
			if th != None:
				self.upperthreshold2.SetValue(th)
		
		# If the scatterplot exists, update it's thresholds 
		if self.scatterPlot:
			sources = self.dataUnit.getSourceDataUnits()
			ch1 = sources[0].getSettings()
			ch2 = sources[1].getSettings()
			ch1lower, ch1upper = ch1.get("ColocalizationLowerThreshold"), ch1.get("ColocalizationUpperThreshold")
			ch2lower, ch2upper = ch2.get("ColocalizationLowerThreshold"), ch2.get("ColocalizationUpperThreshold")
			self.scatterPlot.setThresholds(ch1lower, ch1upper, ch2lower, ch2upper)
		
		if self.dataUnit and self.settings:
			ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
			if ctf and self.colorBtn:
				self.colorBtn.setColorTransferFunction(ctf)
				self.colorBtn.Refresh()

	def doColocalizationCallback(self, *args):
		"""
		A callback for the button "Do colocalization"
		"""
		self.updateBitDepth()
		TaskPanel.doOperation(self)

	def updateBitDepth(self, event = None):
		"""
		Updates the preview to be done at the selected depth
		"""
		if self.settings:
			#depth=self.depthMenu.GetSelection()
			#table=[1,8,32]
			#self.settings.set("ColocalizationDepth",table[depth])
			if self.constColocCheckbox.GetValue():
				self.settings.set("ColocalizationDepth", 1)
				colocval = self.constColocValue.GetValue()
				colocval = int(colocval)
				self.settings.set("OutputScalar", colocval)
			else:
				self.settings.set("ColocalizationDepth", 8)
			

	def doPreviewCallback(self, event = None, *args):
		"""
		A callback for the button "Preview" and other events
					 that wish to update the preview
		"""
		self.updateBitDepth()
		TaskPanel.doPreviewCallback(self, event)
		if self.scatterPlot:
			self.scatterPlot.setSlope(self.dataUnit.getSettings().get("Slope"))
			self.scatterPlot.setIntercept(self.dataUnit.getSettings().get("Intercept"))
			self.scatterPlot.setZSlice(0)
			self.scatterPlot.setTimepoint(self.timePoint)
			self.scatterPlot.setDataUnit(self.dataUnit)
		ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
		self.dataUnit.getSettings().set("ColocalizationColorTransferFunction", ctf)
		self.listctrl.updateListCtrl(self.getVariables())

	def getVariables(self):
		"""
		Return the colocalization variables in a dictionary
		"""
		variables = {}
		if not self.dataUnit: return {}
		sources = self.dataUnit.getSourceDataUnits()
		variables["LowerThresholdCh1"] = sources[0].getSettings().get("ColocalizationLowerThreshold")
		variables["LowerThresholdCh2"] = sources[1].getSettings().get("ColocalizationLowerThreshold")
		variables["UpperThresholdCh1"] = sources[0].getSettings().get("ColocalizationUpperThreshold")
		variables["UpperThresholdCh2"] = sources[1].getSettings().get("ColocalizationUpperThreshold")
		for var in ["Ch1ThresholdMax", "Ch2ThresholdMax", "PearsonImageAbove",
						  "PearsonImageBelow", "PearsonWholeImage", "M1", "M2",
						  "K1", "K2", "DiffStainIntCh1", "DiffStainIntCh2",
						  "DiffStainVoxelsCh1", "DiffStainVoxelsCh2",
						  "ThresholdM1", "ThresholdM2",
						  "ColocAmount", "ColocPercent", "PercentageVolumeCh1",
						  "PercentageTotalCh1", "PercentageTotalCh2",
						  "PercentageVolumeCh2", "PercentageMaterialCh1", "PercentageMaterialCh2",
						  "SumOverThresholdCh1", "SumOverThresholdCh2", "SumCh1", "SumCh2",
						  "NonZeroCh1", "NonZeroCh2", "OverThresholdCh2", "OverThresholdCh1"]:
			variables[var] = sources[0].getSettings().get(var)
		return variables

	def clearVariables(self):
		"""
		Clear colocalization statistics
		"""
		sources = self.dataUnit.getSourceDataUnits()
		settings = sources[0].getSettings()
		for var in ["Ch1ThresholdMax", "Ch2ThresholdMax", "PearsonImageAbove",
						  "PearsonImageBelow", "PearsonWholeImage", "M1", "M2",
						  "K1", "K2", "DiffStainIntCh1", "DiffStainIntCh2",
						  "DiffStainVoxelsCh1", "DiffStainVoxelsCh2",
						  "ThresholdM1", "ThresholdM2",
						  "ColocAmount", "ColocPercent", "PercentageVolumeCh1",
						  "PercentageTotalCh1", "PercentageTotalCh2",
						  "PercentageVolumeCh2", "PercentageMaterialCh1", "PercentageMaterialCh2",
						  "SumOverThresholdCh1", "SumOverThresholdCh2", "SumCh1", "SumCh2",
						  "NonZeroCh1", "NonZeroCh2", "OverThresholdCh2", "OverThresholdCh1"]:
			settings.set(var,0)
		
	def setCombinedDataUnit(self, dataUnit):
		"""
		Set the dataunit used for the colocalization 
		"""
		TaskPanel.setCombinedDataUnit(self, dataUnit)
		# See if the dataunit has a stored colocalizationctf
		# then use that.
		sources = self.dataUnit.getSourceDataUnits()
		self.updateNames()
		
		minval, maxval = sources[0].getScalarRange()
		minval2, maxval2 = sources[1].getScalarRange()
		minval = min(minval, minval2)
		bitmax1 = (2**sources[0].getSingleComponentBitDepth())-1
		bitmax2 = (2**sources[0].getSingleComponentBitDepth())-1
		maxval = max(maxval, maxval2, bitmax1, bitmax2)
		self.lowerthreshold1.SetRange(minval, maxval)
		self.lowerthreshold1.SetValue((maxval - minval) / 2)
		self.upperthreshold1.SetRange(minval, maxval)
		self.upperthreshold1.SetValue(maxval)
		self.lowerthreshold2.SetRange(minval, maxval)
		self.lowerthreshold2.SetValue((maxval - minval) / 2)
		self.upperthreshold2.SetRange(minval, maxval)
		self.upperthreshold2.SetValue(maxval)
		self.updateThreshold(None)

		na = sources[1].getNumericalAperture()
		emission = sources[1].getEmissionWavelength()

		if na:
			self.NA.SetValue("%.4f" % na)
		if emission:
			self.Ch2Lambda.SetValue("%d" % emission)
			
		self.onUpdatePSF(None)

		ctf = self.dataUnit.getSettings().get("ColocalizationColorTransferFunction")
		if not ctf:
			ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
		else:
			Logging.info("Using ColocalizationColorTransferFunction", kw = "task")
		if self.colorBtn:
			self.colorBtn.setColorTransferFunction(ctf)
		self.scatterPlot.setDataUnit(dataUnit)
		if self.scatterPlot:
			#self.scatterPlot.setZSlice(self.preview.z)
			self.scatterPlot.setZSlice(0)
			self.scatterPlot.setTimepoint(self.timePoint)
			self.scatterPlot.updatePreview()		
		
		self.colocalizationPanel.Layout()
		
	def createItemToolbar(self):
		"""
		Method to create a toolbar for the window that allows use to select processed channel
		"""		 
		n = TaskPanel.createItemToolbar(self)		 
		
		coloc = vtkbxd.vtkImageColocalizationFilter()
		coloc.SetOutputDepth(8)
		i = 0
		for data in self.itemMips:
			coloc.AddInput(data)
			coloc.SetColocalizationLowerThreshold(i, 100)
			coloc.SetColocalizationUpperThreshold(i, 255)
			i = i + 1
		coloc.Update()
		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(0, 0, 0, 0)
		ctf.AddRGBPoint(255, 1, 1, 1)
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInput(coloc.GetOutput())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		maptocolor.Update()
		imagedata = maptocolor.GetOutput()
		bmp = ImageOperations.vtkImageDataToWxImage(imagedata).ConvertToBitmap()
		
		bmp = self.getChannelItemBitmap(bmp, (255, 255, 0))
		toolid = wx.NewId()
		name = "Colocalization"
		self.toolMgr.addChannelItem(name, bmp, toolid, lambda e, x = n, s = self:s.setPreviewedData(e, x))		  
		
		for i, tid in enumerate(self.toolIds):
			self.dataUnit.setOutputChannel(i, 0)
			self.toolMgr.toggleTool(tid, 0)
		
		self.dataUnit.setOutputChannel(len(self.toolIds), 1)
		self.toolIds.append(toolid)
		self.toolMgr.toggleTool(toolid, 1)
		self.restoreFromCache()

	def updateNames(self):
		"""
		Updates names of channels
		"""
		sources = self.dataUnit.getSourceDataUnits()
		n1 = sources[0].getName()
		n2 = sources[1].getName()
		self.listctrl.setChannelNames(n1,n2)
		self.lowerThresholdLbl1.SetLabel("%s lower threshold:"%(n1))
		self.lowerThresholdLbl2.SetLabel("%s lower threshold:"%(n2))
		self.upperThresholdLbl1.SetLabel("%s upper threshold:"%(n1))
		self.upperThresholdLbl2.SetLabel("%s upper threshold:"%(n2))

	def onDataChanged(self, obj, event):
		"""
		Handler of data changed event
		"""
		if self.scatterPlot:
			self.scatterPlot.setSlope(self.dataUnit.getSettings().get("Slope"))
			self.scatterPlot.setIntercept(self.dataUnit.getSettings().get("Intercept"))
			self.scatterPlot.setZSlice(0)
			self.scatterPlot.setTimepoint(self.timePoint)
			self.scatterPlot.setDataUnit(self.dataUnit)
			del self.scatterPlot.verticalLegend
			self.scatterPlot.verticalLegend = None
			del self.scatterPlot.horizontalLegend
			self.scatterPlot.horizontalLegend = None
		ctf = self.dataUnit.getSettings().get("ColorTransferFunction")
		self.dataUnit.getSettings().set("ColocalizationColorTransferFunction", ctf)
		self.clearVariables()
		self.listctrl.ClearAll()
		self.listctrl.populateListCtrl()
		self.updateNames()
		
