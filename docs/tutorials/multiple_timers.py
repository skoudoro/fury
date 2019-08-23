import vtk


class vtkTimerCallback:

    ReallyFastTimerId = None
    ReallyFastTimerCount = None
    FastTimerId = None
    FastTimerCount = None
    RenderTimerId = None
    RenderTimerCount = None
    OneShotTimerId = None
    QuitOnOneShotTimer = None

    def __init__(self):
        self.ReallyFastTimerId = 0
        self.ReallyFastTimerCount = 0
        self.FastTimerId = 0
        self.FastTimerCount = 0
        self.RenderTimerId = 0
        self.RenderTimerCount = 0
        self.OneShotTimerId = 0
        self.QuitOnOneShotTimer = 1

    @vtk.calldata_type(vtk.VTK_INT)
    def Execute(self, caller, eventId, calldata):
        if "TimerEvent" == eventId:
            print(calldata)
            tid = calldata

            if tid == self.ReallyFastTimerId:
                self.ReallyFastTimerCount += 1
            elif tid == self.FastTimerId:
                self.FastTimerCount += 1
            elif tid == self.RenderTimerId:
                self.RenderTimerCount += 1

                iren = vtk.vtkRenderWindowInteractor.SafeDownCast(caller)
                if iren and iren.GetRenderWindow() and iren.GetRenderWindow().GetRenderers():
                    n = self.RenderTimerCount % 20
                    if n > 10:
                        n = 20 - n

                    f = n / 10.0

                    renderer = iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
                    if renderer:
                        renderer.SetBackground(f, f, f)
                    iren.Render()

            elif tid == self.OneShotTimerId:
                self.Report()
                if self.QuitOnOneShotTimer:
                    print("QuitOnOneShotTimer is true.")
                    iren = vtk.vtkRenderWindowInteractor.SafeDownCast(caller)
                    if iren:
                        print("Calling iren.ExitCallback()...")
                        iren.ExitCallback()
                else:
                    print("QuitOnOneShotTimer is false.")
                    print("Remaining interactive...")

    def SetReallyFastTimerId(self, tid):
        self.ReallyFastTimerId = tid
        self.ReallyFastTimerCount = 0

    def SetFastTimerId(self, tid):
        self.FastTimerId = tid
        self.FastTimerCount = 0

    def SetRenderTimerId(self, tid):
        self.RenderTimerId = tid
        self.RenderTimerCount = 0

    def SetOneShotTimerId(self, tid):
        self.OneShotTimerId = tid

    def SetQuitOnOneShotTimer(self, quit_v):
        self.QuitOnOneShotTimer = quit_v

    def Report(self):
        print("vtkTimerCallback::Report")
        print("  ReallyFastTimerId: ", self.ReallyFastTimerId)
        print("  ReallyFastTimerCount: ", self.ReallyFastTimerCount)
        print("  FastTimerId: ", self.FastTimerId)
        print("  FastTimerCount: ", self.FastTimerCount)
        print("  RenderTimerId: ", self.RenderTimerId)
        print("  RenderTimerCount: ", self.RenderTimerCount)
        print("  OneShotTimerId: ", self.OneShotTimerId)
        print("  QuitOnOneShotTimer: ", self.QuitOnOneShotTimer)


if __name__ == "__main__":

    renderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # Initialize must be called prior to creating timer events.
    #
    print("Calling iren.Initialize()...")
    iren.Initialize()

    # Sign up to receive TimerEvent:
    #
    cb = vtkTimerCallback()
    iren.AddObserver("TimerEvent", cb.Execute)

    # Create two relatively fast repeating timers:
    #
    tid = iren.CreateRepeatingTimer(3)
    cb.SetReallyFastTimerId(tid)

    tid = iren.CreateRepeatingTimer(25)
    cb.SetFastTimerId(tid)

    # Create a slower repeating timer to trigger Render calls.
    # (This fires at the rate of approximately 10 frames per second.)
    #
    tid = iren.CreateRepeatingTimer(100)
    cb.SetRenderTimerId(tid)

    # And create a one shot timer to quit after 4 seconds.
    #
    tid = iren.CreateOneShotTimer(4000)
    cb.SetOneShotTimerId(tid)
    cb.SetQuitOnOneShotTimer(5000)

    # Run event loop until the one shot timer fires:
    #
    print("Calling iren.Start()...")
    iren.Start()

    # Clean up:
    #
    del cb
    del renderer
    del renWin
    del iren
