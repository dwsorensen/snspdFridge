import TimeTagger
import time

port = 5000
tagger = TimeTagger.createTimeTagger()
print(f"Starting timetagger server on port {port}...")
tagger.startServer(access_mode = TimeTagger.AccessMode.Control, port = port,channels=[1,2,3,4,5,6,7,8])
print("Timetagger running")

while True:
    time.sleep(500)
    print("Server running")