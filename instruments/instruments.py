import yaml
import importlib

def make_instance(instr, module):
    if instr["intf"] == "gpib":  # handle gpib device
        if "device_number" in instr:
            # print(module.dev)
            return module.dev(
                instr["addr"], instr["port"], instr["slot"], instr["device_number"]
            )
        elif "slot" in instr:
            return module.dev(instr["addr"], instr["port"], instr["slot"])
        else:
            return module.dev(instr["addr"], instr["port"])
    if instr["intf"] == "mccusb":
        if "board_number" in instr:
            return module.dev(instr["board_number"])
        else:
            return module.dev()
    elif instr["intf"] == "visa":
        return module.dev(instr["port"])
    elif instr["intf"] == "serial":
        return module.dev(instr["port"])
    else:
        raise NotImplementedError("non-gpib devices need to be implemented")

def load_instr(yamlfile = "instruments_config.yaml"):
    #Load instrument dict from yaml file
    fp = open(yamlfile, "r")
    instr_gen = yaml.load_all(fp,Loader=yaml.Loader)
    instr = {}
    for g in instr_gen:
        print(g)
        instr[g["name"]] = g
    fp.close()

    #Import device modules
    devModules = {}
    for k in list(instr.keys()):
        instkey = instr[k]["inst"]
        print("Loading: %r"%(instkey))
        if instkey not in devModules:
            try:
                devModules[instkey] = importlib.import_module(instkey)
            except Exception as e:
                print("Error importing" + str(instkey) + ": " + str(e))
        instr[k]["dev"] = make_instance(instr[k], devModules[instkey])
    return instr

def load_detectors(yamlfile = "detectors_config.yaml"):
    fp = open(yamlfile, "r")
    detector_gen = yaml.load_all(fp,Loader=yaml.Loader)
    detectors = {}
    for g in detector_gen:
        print(g)
        g["biasV"] = (g["iBias"] * 10**-6) * (g["rSeries"] * 1000)
        print("Loaded detector #" + str(g["id"]))
        print("Bias voltage: " + str(g["biasV"]))
        detectors[g["id"]] = g
    return detectors
    
instr = load_instr()
detectors = load_detectors()
laser = instr['laser2']['dev']
#pc = instr['pc']['dev']
pm1 = instr['pm1']['dev']
pm2 = instr['pm2']['dev']
#pmcal = instr['pmcal']['dev']
switch = instr['switch']['dev']
sw12 = instr['sw12']['dev']
att1 = instr['att1']['dev']
att2 = instr['att2']['dev']
att3 = instr['att3']['dev']
dmm = instr['dmm']['dev']
oldvsrc = instr['oldvsrc']['dev']
vsrc = instr['vsrc']['dev']
compvsrc = instr['compvsrc']['dev']
#counter = instr['counter']['dev']

attlist = [att1,att2,att3]

def init_detector(detector):
    biasVoltage = detector["biasV"]
    biasChannel = detector["biasChannel"]
    #compChannel = detector["compChannel"]
    #threshVoltage = detector["compThreshold"]
    #hystVoltage = detector["compHyst"]

    #threshKey = "thresh" + str(compChannel)
    #hystKey = "hyst" + str(compChannel)

    #threshChannel = instr['compvsrc'][threshKey]
    #hystChannel = instr['compvsrc'][hystKey]

    #compvsrc.set_volt(threshChannel,threshVoltage)
    #compvsrc.set_volt(hystChannel,hystVoltage)

    vsrc.set_volt(biasChannel,biasVoltage)


def init_detectors():
    print(detectors)
    for detector in detectors:
        init_detector(detectors[detector])

def close_detector(detector):
    biasChannel = detector["biasChannel"]
    #compChannel = detector["compChannel"]
    #threshKey = "thresh" + str(compChannel)
    #hystKey = "hyst" + str(compChannel)
    #threshChannel = instr['compvsrc'][threshKey]
    #hystChannel = instr['compvsrc'][hystKey]
    #compvsrc.set_volt(threshChannel,0)
    #compvsrc.set_volt(hystChannel,0)
    vsrc.set_volt(biasChannel,0)

def close_detectors():
    for detector in detectors:
        close_detector(detectors[detector])
def att_enable():
    for att in attlist:
        att.enable()

def att_disable():
    for att in attlist:
        att.disable()

def att_set(value):
    for att in attlist:
        att.set_att(value)

def laseron():
    laser.enable()
    att_enable()
    switch.set_route(2)

def laseroff():
    laser.disable()
    att_disable()
    switch.set_route(1)