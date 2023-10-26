from instruments import *

def setComp(channel, threshold = -1, hysteresis = -1):
    if channel == 1:
        global threshold1
        global hysteresis1
        if threshold == -1:
            threshold = threshold1
        else:
            threshold1 = threshold
        if hysteresis == -1:
            hysteresis = hysteresis1
        else:
            hysteresis1 = hysteresis
        print("Dan is setting threshold to " + str(threshold))
        compvsrc.set_volt(3,threshold)
        compvsrc.set_volt(2,hysteresis)
    elif channel == 2:
        global threshold2
        global hysteresis2
        if threshold == -1:
            threshold = threshold2
        else:
            threshold2 = threshold
        if hysteresis == -1:
            hysteresis = hysteresis2
        else:
            hysteresis2 = hysteresis
        compvsrc.set_volt(4,threshold)
        compvsrc.set_volt(6,hysteresis)

def initComps(customThreshold = -1):
    #Default values, change if necessary
    thresholdA = 1.2
    hysteresisA = 4
    thresholdB = 0.7
    hysteresisB = 4

    if customThreshold != -1:
        thresholdA = customThreshold
        thresholdB = customThreshold

    setComp(1,thresholdA,hysteresisA)
    setComp(2, thresholdB, hysteresisB)

def initDetectors():
    initComps()
    #Voltage Channel 0 Bias - Currently hooped up to port 1, which has 200k resistor
    bias0 = 1.1
    #Voltage channel 1 Bias - Currently hooked up to port 3, which has 100k resistor
    bias1 = 0.4
    vsrc.set_volt(0,bias0)
    vsrc.set_volt(1,bias1)

def closeDetectors():
    vsrc.set_volt(0,0)
    vsrc.set_volt(1,0)

threshold1 = 0
threshold2 = 0
hysteresis1 = 0
hysteresis2 = 0
setComp(1,0,0)
setComp(2,0,0)