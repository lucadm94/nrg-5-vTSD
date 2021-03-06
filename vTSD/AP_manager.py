import socket
import threading
import datetime
import sys, os
import json, struct

sys.path.append(os.path.abspath(os.path.join("..")))
from common.Def import MSG_HDR_LEN, MSGTYPE, INTFTYPE, NRG5_SSID_PREFIX

from optparse import OptionParser

class Listener(object):

    def __init__(self, host, port):
        self.ssid = 0
        self.host = host
        self.port = port
        self.auth = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.createlog("Listener is started on port " + str(port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            self.createlog("Receive connection from " + str(address))
            client.settimeout(60)
            print threading.Thread(target = self.listenToClient, args = (client, address)).start()
            self.createlog("Opening a threaded socket for client " + str(address))

    def __generate_device_reg_reply(self, reg):
        msg = {"device_id": reg[u"device_id"]}
        msg_type = MSGTYPE.DEV_REG_SUCCESS if self.auth else MSGTYPE.DEV_REG_FAILED
        self.auth = not self.auth
        if msg_type == MSGTYPE.DEV_REG_SUCCESS:
            msg["intfs"] = []
            for intf in reg[u"intfs"]:
                msg["intfs"].append({"type":intf[u"type"], "typename":intf[u"typename"], "name":intf[u"name"], "ssid": "{}{:0>6}".format(NRG5_SSID_PREFIX, self.ssid), "channel": 11})
        else:
            msg["error_type"] = 11
            msg["error_msg"] = "unable to pass the authentication of vAAA" 
        msg = json.dumps(msg)
        msg = struct.pack("!BH{}s".format(len(msg)), msg_type.value, len(msg), msg)
        self.ssid += 1
        return msg
                 
    def __receive_msg_hdr(self, sock):
        msg_hdr = sock.recv(MSG_HDR_LEN)
        if msg_hdr:
            tp, length = struct.unpack("!BH", msg_hdr)
            return (MSGTYPE(tp), length)
        return None
                     
    def __process_dev_reg(self, sock, tp, length):
        assert tp == MSGTYPE.DEV_REG
        data = sock.recv(length)
        reg = json.loads(data)
        msg = self.__generate_device_reg_reply(reg)
        return msg

    def __process_svs_reg(self, sock, tp, length):
        data = sock.recv(length)
        reg = json.loads(data)
        del reg["credential"]
        msg = json.dumps(reg)
        msg = struct.pack("!BH{}s".format(len(msg)), MSGTYPE.SVS_REG_SUCCESS.value, len(msg), msg)
        return msg

    def listenToClient(self, client, address):
        size = 1024
        while True:
            try:
                data = self.__receive_msg_hdr(client)
                if data:
                    tp, length = data
                    if tp == MSGTYPE.DEV_REG:
                        response = self.__process_dev_reg(client, tp, length)
                    elif tp == MSGTYPE.SVS_REG:
                        response = self.__process_svs_reg(client, tp, length)
                    else:
                        logging.error("unknown message")
                    client.send(response)
                    self.createlog("Replying to " + str(address) + " with " + str(response))
                else:
                    raise error('Client Disconnected')
            except msg:
                print "AP_manager: error "
                client.close()
                return False

    def createlog(self, message):
        with open('listener.log', 'a') as logfile:
            logfile.write("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "] " + str(message) + '\n')


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port_num", help="select on wich port to open the listener, default = 2311", metavar="<port>")
    (options, args) = parser.parse_args()

    port_num = options.port_num

    if not port_num:
        port_num = 2311

    while True:
        try:
            port_num = int(port_num)
            break
        except ValueError:
            print "AP_manager:main: Invalid port number. Abort..."
            exit(1)

    Listener('',port_num).listen()

