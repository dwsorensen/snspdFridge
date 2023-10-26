import zmq
import threading
import instruments
import daniel_utilities as dan

class Server():
    def __init__(self, port, n_workers=4):
        self.port = str(port)
        url_worker = "inproc://workers"
        url_client = 'tcp://*:'+self.port
        self.context = zmq.Context.instance()
        # Socket to talk to clients
        clients = self.context.socket(zmq.ROUTER)
        clients.bind(url_client)

        workers = self.context.socket(zmq.DEALER)
        workers.bind(url_worker)

        self.workers = []
        for k in range(0, n_workers):
            self.workers.append(threading.Thread(target=self.start_worker, daemon=True, args=(url_worker,k,)))
            self.workers[-1].start()

        zmq.proxy(clients, workers)
        # We never get here but clean up anyhow
        clients.close()
        workers.close()
        context.term()


    def start_worker(self, url_worker, k=0):
        """Worker routine"""
        context = self.context or zmq.Context.instance()
        # Socket to talk to dispatcher
        socket = context.socket(zmq.REP)
        socket.connect(url_worker)

        while True:
            message = socket.recv()
            message = message.decode()
            response = self.handle(message)
            # print('worker '+str(k)+' reporting for duty, '+response.decode())
            socket.send(response)


    def handle(self, message):
        print("Recieved: " + message)
        try:
            message = message.lower()
            message = message.split(" ")
            if message[0] == "initdetectors":
                dan.initDetectors()
                returnMessage = "Detectors initialized."
            elif message[0] == "closedetectors":
                dan.closeDetectors()
                returnMessage = "Detectors closed."
            elif message[0] == "bias":
                if len(message) < 3:
                    returnMessage = "2 Arguments Required."
                else:
                    instruments.vsrc.set_volt(int(message[1]),float(message[2]))
                    returnMessage = "Bias voltage set."
            elif message[0] == "hyst":
                if len(message) < 3:
                    returnMessage = "2 Arguments Required."
                else:
                    channel = int(message[1])
                    value = float(message[2])
                    dan.setComp(channel,hysteresis=value)
                    returnMessage = "Set comp " + str(channel) + " to " + str(value)
            elif message[0] == "thresh":
                if len(message) < 3:
                    returnMessage = "2 Arguments Required."
                else:
                    channel = int(message[1])
                    value = float(message[2])
                    dan.setComp(channel,threshold = value)
                    returnMessage = "Set comp " + str(channel) + " to " + str(value)
                    
            elif message[0] == "laseron":
                instruments.laseron()
                returnMessage = "Laser turned on."
            elif message[0] == "laseroff":
                instruments.laseroff()
                returnMessage = "Laser turned off."
            elif message[0] == "att":
                if len(message) < 2:
                    returnMessage = "1 Argument Required."
                else:
                    value = float(message[1])
                    instruments.att_set(value)
                    returnMessage = "Set attenuators to " + str(value)
            else:
                returnMessage = "Command not recognized."
        except Exception as e:
            returnMessage = "Error: " + str(e)
        return returnMessage.encode()

if __name__ == '__main__':
    zmqs = Server('80', n_workers=4)
