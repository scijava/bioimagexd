import  wx

class SplashScreen(wx.Frame):
    def __init__(self, parent, ID=-1, title="Loading BioImageXD...",
                 style=wx.SIMPLE_BORDER|wx.STAY_ON_TOP,
                 duration=1500, bitmapfile="bitmaps/splashscreen.bmp",
                 bitmap = None,
                 callback = None):
        '''
        parent, ID, title, style -- see wx.Frame
        duration -- milliseconds to display the splash screen
        bitmapfile -- absolute or relative pathname to image file
        callback -- if specified, is called when timer completes, callback is
                    responsible for closing the splash screen
        '''
        ### Loading bitmap
        if bitmapfile:
            self.bitmap = bmp = wx.Image(bitmapfile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        else:
            self.bitmap = bitmap

        ### Determine size of bitmap to size window...
        self.offset = 30

        size = (bmp.GetWidth(), bmp.GetHeight()+self.offset)
    
        # size of screen
        width = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)
        height = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)
        pos = ((width-size[0])/2, (height-size[1])/2)

        # check for overflow...
        if pos[0] < 0:
            size = (wx.SystemSettings_GetSystemMetric(wx.SYS_SCREEN_X), size[1])
        if pos[1] < 0:
            size = (size[0], wx.SystemSettings_GetSystemMetric(wx.SYS_SCREEN_Y))

        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseClick)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBG)

        self.Show(True)
        self.message=""


        class SplashTimer(wx.Timer):
            def __init__(self, targetFunction):
                self.Notify = targetFunction
                wx.Timer.__init__(self)

        if callback is None:
            callback = self.OnSplashExitDefault

        self.timer = SplashTimer(callback)
        self.timer.Start(duration, 1) # one-shot only

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0,0, False)
        dc.SetBrush(wx.Brush(wx.Colour(200,200,200)))            
        h = self.bitmap.GetHeight()
        w= self.bitmap.GetWidth()
        dc.DrawRectangle(0, h,w,h+self.offset)
        if self.message:
            dc.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.NORMAL))
            dc.SetTextForeground(wx.Colour(0,0,0))
            dc.DrawText(self.message, 5,h+5)


    def OnEraseBG(self, event):
        pass

    def OnSplashExitDefault(self, event=None):
        self.Close(True)

    def OnCloseWindow(self, event=None):
        self.Show(False)
        self.timer.Stop()
        del self.timer
#        self.Destroy()

    def SetMessage(self, message):
        self.message = message
        self.Refresh()
        self.Update()

    def OnMouseClick(self, event):
        self.timer.Notify()
