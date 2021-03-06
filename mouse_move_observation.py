# -*- coding:utf-8 -*-
import ctypes
import time
import socket
import errno
import subprocess

"""
対応してるエラー：
1.サーバーダウン時の再接続
サーバーダウン時、サーバーが動き始めるまでコネクトし続ける。
サーバーが落ちた時、出席していれば送りなおす
2.衝突したとき
15秒待つ。15秒はサーバーのタイムアウトが10秒なので
3.始めに繋がらなかったとき
接続できるまでがんばる
"""

host = "0.0.0.0"#server's ip address
port = 8000     #your fabortite port
wait_num = 1    #int, when wait_connection, need to repeat

# define mouse pointer class
class _pointer(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_long),
        ('y', ctypes.c_long),
    ]

class client(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #these follow a main reason to error occuring
        #error 10053: timeout
        #error 10054: server_down
        #error 10056: disconnect
        self.error = dict({ "ERROR_10053":"exc.errno == errno.WSAECONNABORTED",
                            "ERROR_10054":"exc.errno == errno.WSAECONNRESET",
                            "ERROR_10056":"exc.errno == errno.WSAEISCONN",
                            "ERROR_10057":"exc.errno == errno.WSAENOTCONN" })
        self.try_connection()

    def try_connection(self):
        while(1):
            try:
                self.client.connect((self.host, self.port))
                break
            except socket.error as exc:
                #print("Caught exception socket.error : %s" % exc)
                #for reconnection error not to continue connecting
                if self.error["ERROR_10053"] or self.error["ERROR_10054"] \
                    or self.error["ERROR_10056"] or self.error["ERROR_10057"]:
                    break
                continue

    #うまくいかないとこです。
    def wait_connection(self):
        #occur a wait connection to wait and repeat to send information
        #Um... x does not increase, so i use while method
        x = 0
        while(x <= wait_num):
            time.sleep(15)
            x += 1
            try:
                self.client.send(str(self.state_on).encode("utf-8"))
            except socket.error:
                continue
            return 1
        return 0

    def observe(self):
        # initialize pointer
        before_point = _pointer()
        after_point = _pointer()

        #to wait time and sleep
        weight = -1
        time_weight = [15, 60, 180, 120, 180]

        #when server_down and presence, we send presence information
        try:
            self.client.send(str(self.state_on).encode("utf-8"))
        except (AttributeError, socket.error):
            self.state_on = 0

        while (1):
            before_point.x = after_point.x
            before_point.y = after_point.y
            #get mouse position
            ctypes.windll.user32.GetCursorPos(ctypes.byref(after_point))

            #move or stop
            if before_point.x == after_point.x and before_point.y == after_point.y:
                #weight is almost over 0 and it is rarely -1
                #(when over 1 is presence, when -1, absence)
                weight = weight - 1 if weight >= 0 and self.state_on else 0
            else:#time_weight does not correspond over 3
                if weight != (len(time_weight) - 2):
                    weight += 1
                #send presence
                self.state_on = 1
                try:
                    self.client.send(str(self.state_on).encode("utf-8"))
                except socket.error as exc:
                    #print("Caught exception socket.error : %s" % exc)
                    if self.error["ERROR_10053"]:#repeat connection
                        time.sleep(15)
                        break
                    elif self.error["ERROR_10054"]:#give up connection
                        break
            #send absence
            if weight == -1:
                self.state_on = 0
                try:
                    self.client.send(str(self.state_on).encode("utf-8"))
                except socket.error as exc:
                    #print("Caught exception socket.error : %s" % exc)
                    if self.error["ERROR_10053"]:#repeat connection
                        time.sleep(15)
                        break
                    elif self.error["ERROR_10054"]:#give up connection
                        break

            time.sleep(time_weight[weight + 1])

    def repeat(self):
        # remedy to error and server_down
        while(1):
            self.__init__(self.host, self.port)
            self.observe()

if __name__ == "__main__":
    client(host, port).repeat()
