from CTC100 import CTC
import time

primingTime = 20 #time (24hr value) to enter priming. MST
coolingTime = 8 #time(24hr value) to enter cooling

def currentHour():
    currentHour_utc = time.localtime().tm_hour
    currentHour_mst = currentHour_utc - 7
    if currentHour_mst < 1:
        currentHour_mst = currentHour_mst + 24
    return currentHour_mst

if __name__ == "__main__":
    print("TEMPERATURE SERVER STARTING")
    ctc = CTC()
    while True:
        h = currentHour()
        m = ctc.getMode()
        if h >= coolingTime and h < primingTime and m != "cooling":
            print("TEMPERATURE SERVER SETTING TO COOLING MODE")
            currentTime = time.localtime()
            formattedTime = time.strftime("%Y-%m-%d %H:%M:%S", currentTime)
            print(formattedTime)
            ctc.coolingMode()
        elif h >= primingTime and m != "priming":
            print("TEMPERATURE SERVER SETTTING TO PRIMING MODE")
            currentTime = time.localtime()
            formattedTime = time.strftime("%Y-%m-%d %H:%M:%S", currentTime)
            print(formattedTime)
            ctc.primingMode()
        else:
            print("TEMPERATURE SERVER REMAINING IN CURRENT STATE: " + m)
            currentTime = time.localtime()
            formattedTime = time.strftime("%Y-%m-%d %H:%M:%S", currentTime)
            print(formattedTime)
        time.sleep(300)
