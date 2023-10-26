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

instr = load_instr()
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