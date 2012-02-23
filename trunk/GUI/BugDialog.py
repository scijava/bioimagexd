#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: BugDialog
 Project: BioImageXD
 Description:

 A dialog for reporting a bug to the BioImageXD developers
 
 Copyright (C) 2005  BioImageXD Project
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"



import GUI.Dialogs
from lib.email.mime.multipart import MIMEMultipart
from lib.email.mime.text import MIMEText
from lib.email.mime.base import MIMEBase
import scripting
import smtplib
import wx	# This module uses the new wx namespace
import Configuration
import platform
import bxdversion

def createSystemReport():
	"""
	create a report of the system
	"""
	ret = "System report for machine %s (%s)\n"%(platform.node(),platform.system())
	ret += "BioImageXD version: %s\n"%bxdversion.VERSION
	ret += "Version: %s\n"%platform.version()
	ret += "Platform: %s\n"%platform.platform()
	ret += "Machine type (processor): %s (%s)\n"%(platform.machine(), platform.processor())
	ret += "Python version: %s\n"%platform.python_version()
	try:
		release, versioninfo, machine = platform.mac_ver()
		ret+="MacOS Version: %s\n"%release
	except:
		pass
	dist, ver, did = platform.dist()
	if dist:
		ret+="Unix distribution: %s %s %s\n"%(dist,ver,did)
	try:
		ver, csd, ptype = platform.win32_ver()
		ret+="Win32 version: %s %s %s\n"%(ver,csd,ptype)
	except:
		pass
		
	return ret
def mail(to = '', senderName = '', logText = '', text = ''):
	"""
	send an email message
	"""
	sender = 'bioimagexd.bugs@gmail.com'
	message = MIMEMultipart('related')
	message["To"]      = to
	message["From"]    = sender
	message["Subject"] = "BioImageXD Bug report from %s" % senderName
	message.preamble = 'This is a multi-part message in MIME format.'
    
	msgAlternative = MIMEMultipart('alternative')
	message.attach(msgAlternative)    
	msgText = MIMEText('The message has been sent in HTML format, which your mail reader seems not to support.')
	msgAlternative.attach(msgText)    
	msgText = MIMEText(text, 'html')
	msgAlternative.attach(msgText)

	conf = Configuration.getConfiguration()
	fp = open(conf.getConfigurationFile(),"r")
	configText = fp.read()
	fp.close()
	
	part = MIMEBase('text','plain')
	part.set_payload(configText)
	part.add_header('Content-Disposition','attachment; filename="BioImageXD.ini"')
	message.attach(part)
	part = MIMEBase('text','plain')
	part.set_payload(createSystemReport())
	part.add_header('Content-Disposition','attachment; filename="system.txt"')
	message.attach(part)
    
	part = MIMEBase('text','plain')
	part.set_payload(logText)
	part.add_header('Content-Disposition','attachment; filename="logfile.txt"')
	message.attach(part)
    
	try:
		mailServer = smtplib.SMTP("smtp.gmail.com", 587)
		mailServer.ehlo()
		mailServer.starttls()
		mailServer.ehlo()
		mailServer.login("bioimagexd.bugs@gmail.com", "bxd123")
		mailServer.sendmail(sender, to, message.as_string())    
	except:
		return 1    
	try:
		mailServer.quit()
	except:
		pass
	return 0
    
class BugDialog(wx.Dialog):
	def __init__(self, parent, crashMode = 0):
		if not crashMode:
			title = 'Report a bug'
		else:
			title = 'Report an abnormal shutdown'
		wx.Dialog.__init__(self, parent, -1, title, size = (520, 400))
		self.sizer = wx.GridBagSizer(5, 5)
		x, y = (600, 400)
        
		self.crashMode = crashMode
		self.logFile = ""

		nameLbl = wx.StaticText(self, -1, "Name:")
		emailLbl = wx.StaticText(self, -1, "Email:")
        
		self.nameEdit = wx.TextCtrl(self, -1, "BioImageXD User", size = (300, -1))
		self.emailEdit = wx.TextCtrl(self, -1, "", size = (300, -1))
        
		infoSizer = wx.GridBagSizer(5, 5)
		infoSizer.Add(nameLbl, (0, 0))
		infoSizer.Add(self.nameEdit, (0, 1), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)
		infoSizer.Add(emailLbl, (1, 0))
		infoSizer.Add(self.emailEdit, (1, 1), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)
        
		self.sizer.Add(infoSizer, (0, 1), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)

		if not self.crashMode:
			text = wx.StaticText(self, -1, """Please enter a description of the problem 
you have encountered while using BioImageXD. Carefully describe the steps you took and 
try to be as specific as possible. This helps the BioImageXD development team solve 
the problems as quickly as possible.  A log of your last usage of the software will be 
attached to the report to aid the developers in solving the error. If you wish to be 
contacted regarding the error, you can fill in your name and email address. 
It is not required, however, and you can leave them empty if you wish.
""")
		else:
			text = wx.StaticText(self, -1, """The last execution of BioImageXD ended with 
an abnormal shutdown. Data from the last execution has been gathered that will help the 
BioimageXD developers to solve this problem. Please describe the steps you took that caused 
the abnormal shutdown. Try to be as specific as possible. A log of your last usage of the 
software will be attached to the report to aid the developers in solving the error.
""")
		self.sizer.Add(text, (1, 1), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)
        
		self.reportMessage = wx.TextCtrl(self, -1, size = (500, 200), style = wx.TE_MULTILINE)
        
		self.sizer.Add(self.reportMessage, (2, 1), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)
        
		self.staticLine = wx.StaticLine(self)
		self.sizer.Add(self.staticLine, (3, 1), flag = wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.cancelButton = wx.Button(self, -1, "Cancel")
		self.okButton = wx.Button(self, -1, "Send report")
		self.okButton.Bind(wx.EVT_BUTTON, self.sendReport)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.closeWindow)
		self.okButton.SetDefault()
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer.Add(self.okButton, wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT, border = 10)
		btnSizer.AddSpacer((10,10))
		btnSizer.Add(self.cancelButton, wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT, border = 10)
		self.sizer.Add(btnSizer, (4, 1), flag = wx.ALIGN_RIGHT)

		self.actions, self.logmessages = None, None

		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.SetSizeHints(self)
		#self.sizer.Fit(self)
        
		self.CentreOnParent(wx.BOTH)
        
	def crashModeOn(self, logfile):
		"""
		enable the crash mode, where the log will be coming fromthe given filename
		"""
		self.crashMode = 1
		self.logFile = logfile
	def setContent(self, actions, logmessages):
		"""
		set the contents to be sent, for example in case we're reporting a crash 
						instead of an error in current execution
		"""
		self.actions, self.logmessages = actions, logmessages
       
	def closeWindow(self, evt):
		"""
		close the window without sending a bug report
		"""
		self.EndModal(wx.ID_CANCEL)

	def sendReport(self, evt):
		"""
		close the window without sending a bug report
		"""
		if not self.logmessages:
			loglines = scripting.logFile.getvalue().split("\n")
			self.logmessages = scripting.logFile.getvalue()
		else:
			#print "Log messages =", self.logmessages
			loglines = self.logmessages.split("\n")
        
		frommsg = ["<html>", "<strong>From:</strong> " + self.nameEdit.GetValue()] + \
					["<strong>E-mail:</strong>" + self.emailEdit.GetValue(), ""]
					
		
		usermsg = ["<strong>Description of the problem:</strong>"] + \
					self.reportMessage.GetValue().split("\n") + [""]

		if not self.actions:
			actions = scripting.recorder.getText()
		else:
			actions = [self.actions]
            
		if not self.crashMode:
			logprefix = "<strong>Attached is the log file related to the crash</strong>"
		else:
			logprefix = "<strong>Attached is a log from file %s</strong>" % (self.logFile)
            
        
		lines = frommsg + usermsg + ["<strong>The actions of the user:</strong>"] + \
				actions + ["<br><br>", logprefix] 
		#+ loglines
        
		if mail("bioimagexd-bugs@lists.sourceforge.net", self.nameEdit.GetValue(), self.logmessages, "<br/>\n".join(lines)):
			GUI.Dialogs.showerror(self, \
							"Failed to send error report. Please contact info@bioimagexd.org directly", \
							"Failed to send error report")
		else:
			GUI.Dialogs.showmessage(self, \
							"The report was sent succesfully!. Thank you for helping to improve BioImageXD!", \
							"Reporting succesful")
        
		self.EndModal(wx.ID_OK)

