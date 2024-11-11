import zmq
import threading
import instruments
import time
import json

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
                instruments.init_detectors()
                returnMessage = "Detectors initialized."
            elif message[0] == "closedetectors":
                instruments.close_detectors()
                returnMessage = "Detectors closed."
            elif message[0] == "iddetectors":
                detDict = instruments.detectors
                returnMessage = json.dumps(detDict)
            elif message[0] == "bias":
                if len(message) < 3:
                    returnMessage = "2 Arguments Required."
                else:
                    instruments.vsrc.set_volt(int(message[1]),float(message[2]))
                    returnMessage = "Bias voltage set."
            elif message[0] == "reset":
              instruments.close_detectors()
              time.sleep(15)
              instruments.init_detectors()
            elif message[0] == "comp":
                v = float(message[2])
                #This is absolutely disgusting but I love it
                channel = instruments.instr['compvsrc'][message[1]]
                instruments.compvsrc.set_volt(channel,v)
                returnMessage = "Comparator set"

            else:
                returnMessage = "Command not recognized."
        except Exception as e:
            returnMessage = "Error: " + str(e)
        return returnMessage.encode()

if __name__ == '__main__':
    zmqs = Server('80', n_workers=4)
