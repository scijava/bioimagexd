# -*- coding: iso-8859-1 -*-
"""
 Unit: WatershedTotalsList
 Project: BioImageXD
 Created: 22.11.2007, KP
 Description: A module containg a list control element for showing the average totals of analyzing segmented objects

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import wx.lib.mixins.listctrl as listmix
import lib.messenger

class WatershedTotalsList(wx.ListCtrl):
	"""
	Created: KP
	Description: a listctrl that shows the averages of the segmented object
	"""
	def __init__(self, parent, log):
		"""
		initialize the list ctrl
		"""
		wx.ListCtrl.__init__(
			self, parent, -1, 
			size = (400, 250),
			style = wx.LC_REPORT | wx.LC_VIRTUAL | wx.BORDER_RAISED | wx.LC_VRULES
			)

		self.quantities = []
		self.stats = []
		self.setupList()

	def setupList(self):
		"""
		Setup list ctrl
		"""
		self.quantities = []
		self.quantities.append("# of objects")
		self.quantities.append(u"Avg. volume (px)")
		self.quantities.append(u"Avg. volume (\u03BCm)")
		self.quantities.append(u"Sum of volumes (\u03BCm)")
		self.quantities.append(u"Avg. area (\u03BCm)")
		self.quantities.append(u"Sum of areas (\u03BCm)")
		self.quantities.append("Avg. intensity (obj)")
		self.quantities.append("Avg. intensity (voxels in objs)")
		self.quantities.append("Avg. intensity (outside objs)")
		self.quantities.append("Avg. intensity (outside objs, non zero)")
		self.quantities.append(u"Avg. distance to other objs (\u03BCm)")
		self.quantities.append("Non zero voxels")
		self.quantities.append("Avg. roundness (0.0-1.0)")

		self.stats = []
		for i in range(22):
			self.stats.append(0.0)
	
		self.SetItemCount(13)
		self.InsertColumn(0, "Quantity")
		self.InsertColumn(1, "Value")
		self.SetColumnWidth(0, 250)
		self.SetColumnWidth(1, 150)

		self.attr = wx.ListItemAttr()
		self.color = wx.Colour(180,255,180)
		self.attr.SetBackgroundColour(self.color)

	def setStats(self, stats):
		"""
		set the averages to be shown in the listctrl
		"""
		self.stats = stats
		self.Refresh()
		
	def getColumnText(self, index, col):
		"""
		Descrition: return the text for the given row and column
		"""
		item = self.GetItem(index, col)
		return item.GetText()

	def OnGetItemText(self, item, col):
		if col == 0:
			return self.quantities[item]
		
		if not self.stats:
			return ""
		
		if item > len(self.stats):
			return ""
		
		if col == 1:
			if item == 0:
				return "%d" % self.stats[0]
			elif item == 2:
				return u"%.3f\u00B1%.3f \u03BCm"%(self.stats[1],self.stats[2])
			elif item == 1:
				return u"%.3f\u00B1%.3f px"%(self.stats[3],self.stats[4])
			elif item == 3:
				return u"%.3f \u03BCm"%(self.stats[13])
			elif item == 4:
				return u"%.3f\u00B1%.3f \u03BCm"%(self.stats[5],self.stats[6])
			elif item == 5:
				return u"%.3f \u03BCm"%(self.stats[14])
			elif item == 6:
				return u"%.3f\u00B1%.3f"%(self.stats[7],self.stats[8])
			elif item == 7:
				return u"%.3f\u00B1%.3f"%(self.stats[17],self.stats[18])
			elif item == 8:
				return u"%.3f\u00B1%.3f"%(self.stats[9],self.stats[10])
			elif item == 9:
				return u"%.3f\u00B1%.3f"%(self.stats[15],self.stats[16])
			elif item == 10:
				return u"%.2f\u00B1%.2f \u03BCm"%(self.stats[11],self.stats[12])
			elif item == 11:
				return "%d"%self.stats[19]
			elif item == 12:
				return u"%.2f\u00B1%.2f"%(self.stats[20],self.stats[21])
				
 
	def OnGetItemImage(self, item):
		return -1

	def OnGetItemAttr(self, item):
		return self.attr


class WatershedObjectList(wx.ListCtrl, listmix.ListCtrlSelectionManagerMix):
	"""
	A list control object that is used to display a list of the results of
				 a watershed segmentation or a connected components analysis
	"""
	def __init__(self, parent, wid, gsize = (400, 250)):
		wx.ListCtrl.__init__(
			self, parent, wid, 
			size = gsize,
			style = wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES,
			)
		listmix.ListCtrlSelectionManagerMix.__init__(self)
		self.InsertColumn(0, "Object #")
		self.InsertColumn(1, u"Volume (px)")
		self.InsertColumn(2, u"Volume (\u03BCm)")
		self.InsertColumn(3, u"Area (\u03BCm)")
		self.InsertColumn(4, "Center Of Mass")
		self.InsertColumn(5, "Avg. intensity")
		self.InsertColumn(6, u"Avg. dist to other objs (\u03BCm)")
		self.InsertColumn(7, "Roundness")
		self.SetColumnWidth(0, 50)
		self.SetColumnWidth(1, 70)
		self.SetColumnWidth(2, 70)
		self.SetColumnWidth(3, 70)
		self.SetColumnWidth(4, 70)
		self.SetColumnWidth(5, 70)
		self.SetColumnWidth(6, 70)
		self.SetColumnWidth(7, 70)

		self.highlightSelected = 1
		#self.SetItemCount(1000)

		self.attr1 = wx.ListItemAttr()
		self.attr1.SetBackgroundColour("white")
		
		self.counter = 0
		self.attr2 = wx.ListItemAttr()
		self.attr2.SetBackgroundColour("light blue")
		self.volumeList = []
		self.centersOfMassList = []
		self.avgIntList = []
		self.areaUmList = []
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
		self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.OnItemFocused)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

	def setSelectionHighlighting(self, flag):
		"""
		Set the flag indicating whether the selection of the objects will be highlighted
		"""
		self.highlightSelected = flag
	
	def setCentersOfMass(self, centersofmassList):
		"""
		"""
		self.centersOfMassList = centersofmassList
		self.Freeze()
		for i, cog in enumerate(centersofmassList):
			if self.GetItemCount() < i:
				self.InsertStringItem(i, "")
			self.SetStringItem(i, 4, "(%d,%d,%d)" % (cog))
		self.Thaw()
		self.Refresh()
		
	def setVolumes(self, volumeList):
		"""
		"""
		self.volumeList = volumeList
		self.Freeze()
		for i, (vol, volum) in enumerate(volumeList):
			if self.GetItemCount() <= i:
				self.InsertStringItem(i, "")
			self.SetStringItem(i, 0, "#%d" % (i+1))
			self.SetStringItem(i, 1, "%d px" % (vol))	
			self.SetStringItem(i, 2, u"%.3f \u03BCm" % (volum))	  
		self.Thaw()
		self.Refresh()

	def setAreasUm(self, areaList):
		self.areaUmList = areaList
		self.Freeze()
		for i, area in enumerate(areaList):
			if self.GetItemCount() <= i:
				self.InsertStringItem(i, "")
			self.SetStringItem(i, 3, u"%.3f \u03BCm" % (area))	  
		self.Thaw()
		self.Refresh()
		
	def setAverageDistances(self, avgDistList, avgDistStdErrs):
		"""
		Set the list of average distances to be shown
		"""
		self.avgDistList = avgDistList
		for i, avgDist in enumerate(avgDistList):
			if self.GetItemCount() < i:
				self.InsertStringItem(i, "")
			self.SetStringItem(i, 6, u"%.3f\u00B1%.3f \u03BCm"%(avgDist,avgDistStdErrs[i]))
		self.Refresh()
		
	def setAverageIntensities(self, avgIntList, avgIntStdErrs):
		"""
		Set the list of average intensities that is displayed
		"""
		self.avgIntList = avgIntList
		for i, avgint in enumerate(avgIntList):
			if self.GetItemCount() < i:
				self.InsertStringItem(i, "")		
			self.SetStringItem(i, 5, u"%.3f\u00B1%.3f" %(avgint,avgIntStdErrs[i]))
		self.Refresh()

	def setRoundness(self, roundness):
		"""
		Set the list of roundness of the objects
		"""
		self.objRoundness = roundness
		for i, oRound in enumerate(roundness):
			if self.GetItemCount() < i:
				self.InsertStringItem(i, "")
			self.SetStringItem(i, 7, "%.3f"%(oRound))
		self.Refresh()
		
	def OnItemFocused(self, event):
		event.Skip()
		
	def OnItemSelected(self, event):
		self.currentItem = event.m_itemIndex
		item = -1
		
		if self.highlightSelected:
			self.counter += 1
			wx.FutureCall(200, self.sendHighlight)
		event.Skip()
		
	def sendHighlight(self):
		"""
		Send an event that will highlight the selected objects
		"""
		self.counter -= 1
		if self.counter <= 0:
			lib.messenger.send(None, "selected_objects", self.getSelection())
			self.counter = 0
			
	def OnItemActivated(self, event):
		self.currentItem = event.m_itemIndex
		
		if len(self.centersOfMassList) >= self.currentItem: 
			centerofmass = self.centersOfMassList[self.currentItem]
			x, y, z = centerofmass
			
			lib.messenger.send(None, "show_centerofmass", self.currentItem, centerofmass)
			lib.messenger.send(None, "zslice_changed", int(z))
			lib.messenger.send(None, "update_helpers", 1)

	def OnItemDeselected(self, evt):
		print ("OnItemDeselected: %s" % evt.m_itemIndex)

	def OnGetItemImage(self, item):
		return - 1

	def OnGetItemAttr(self, item):
		if item % 2 == 1:
			return self.attr1
		elif item % 2 == 0:
			return self.attr2
		else:
			return None
