#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasPersist
 Project: BioImageXD
 Created: 11.04.2005, KP
 Description:

 URPO - The URMAS Persistent Objects
 
 This is a module for writing out / reading in an URMAS timeline
 that uses the python ConfigParser. Urpo utilizes the __getstate__ / 
 __setstate__ methods for pickling. A __getstate__ is required, but
 if no __setstate__ is present, Urpo will update target dictionary
 with the depersisted items.
 
 
 Modified: 11.04.2005 KP - Created the module
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

from ConfigParser import *

class UrmasPersist:
    """
    Class: UrmasPersist
    Created: 11.04.2005, KP
    Description: A class that persists / depersists an Urmas timeline
    """    
    def __init__(self,control):
        """
        Method: __init__
        Created: 11.04.2005, KP
        Description: Initialize
        """           
        self.control = control
    
    def persist(self,filename):
        """
        Method: persist(filename)
        Created: 11.04.2005, KP
        Description: Write the given control object out to the given file
        """               
        self.parser = SafeConfigParser()
        self.parser.optionxform=str
        to_persist=[("control",self.control)]
        self.control.persist_lbl="control"
        while len(to_persist):
            name,obj=to_persist[0]
            print "Persisting ",name,"=",obj
            d=obj.__getstate__()
            for item,value in d.items():
                if type(value) in [type([])]:
                    n=0
                    print "adding items of ",value
                    for additem in value:
                        lbl="%s.%s(%d)"%(name,item,n)
                        print "additem=",additem
                        to_persist.append((lbl,additem))
                        n=n+1
                elif "__getstate__" in dir(value):
                    persist_lbl="%s.%s"%(name,item)
                    to_persist.append((persist_lbl,value))
                else:
                    self.persist_object(item,value,name)
            to_persist=to_persist[1:]
            
        fp=open(filename,"w")
        self.parser.write(fp)
        fp.close()
        
    def persist_object(self,name,value,label):
        """
        Method: persist_object(name,value,label)
        Created: 11.04.2005, KP
        Description: Write out info specific to one item
        """      
        if not self.parser.has_section(label):
            self.parser.add_section(label)
        if type(value)==type(""):
            value='"%s"'%value
        self.parser.set(label,name,str(value))
        
    def depersist(self,filename):
        """
        Method: depersist(filename)
        Created: 11.04.2005, KP
        Description: Read the given control object from a given file
        """               
        self.parser = SafeConfigParser()
        self.parser.optionxform=str
        self.parser.read([filename])
        sections = self.parser.sections()
        print "sections=",sections
        sections.sort()
        for section in sections:
            self.depersist_section(section)
            
    def depersist_section(self,section):
        """
        Method: depersist_section(section)
        Created: 11.04.2005, KP
        Description: Read a given section from a given persisted file
        """               
        print "Depersisting section",section
        s=section.replace("(","[")
        s=s.replace(")","]")
        for option in self.parser.options(section):
            value=self.parser.get(section,option)
            #value=eval(value)
            code="self.%s.%s=%s"%(s,option,value)
            
            print code
            codeobj=compile(code,"Depersist","single")
            print "code=",code
            eval(codeobj,globals(),locals())
            #eval(code,globals(),locals())
        obj=eval("self.%s"%s)
        if "refresh" in dir(obj):
            print "Refreshing self.%s"%(s)
            obj.refresh()
            
