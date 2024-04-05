
import socket
import sha3
import logging

import cv2, imutils, socket
import numpy as np
import time
import base64
import threading, wave, pyaudio,pickle,struct
import sys
import queue
import os
# For details visit pyshine.com
q = queue.Queue(maxsize=10)

filename =  'count.mp4'
command = "ffmpeg -i {} -ab 160k -ac 2 -ar 44100 -vn {}".format(filename,'temp.wav')
os.system(command)

BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
host_name = socket.gethostname()
host_ip = '192.168.1.21'#  socket.gethostbyname(host_name)
print(host_ip)
port = 9688
socket_address = (host_ip,port)
server_socket.bind(socket_address)
print('Listening at:',socket_address)

vid = cv2.VideoCapture(filename)
FPS = vid.get(cv2.CAP_PROP_FPS)
global TS
TS = (0.5/FPS)
BREAK=False
print('FPS:',FPS,TS)
totalNoFrames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
durationInSeconds = float(totalNoFrames) / float(FPS)
d=vid.get(cv2.CAP_PROP_POS_MSEC)
print(durationInSeconds,d)


def video_stream_gen():
   
    WIDTH=400
    while(vid.isOpened()):
        try:
            _,frame = vid.read()
            frame = imutils.resize(frame,width=WIDTH)
            q.put(frame)
        except:
            os._exit(1)
    print('Player closed')
    BREAK=True
    vid.release()
	

def video_stream():
    global TS
    fps,st,frames_to_count,cnt = (0,0,1,0)
    cv2.namedWindow('TRANSMITTING VIDEO')        
    cv2.moveWindow('TRANSMITTING VIDEO', 10,30) 
    while True:
        msg,client_addr = server_socket.recvfrom(BUFF_SIZE)
        print('GOT connection from ',client_addr)
        WIDTH=400
        
        while(True):
            frame = q.get()
            encoded,buffer = cv2.imencode('.jpeg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])
            message = base64.b64encode(buffer)
            server_socket.sendto(message,client_addr)
            frame = cv2.putText(frame,'FPS: '+str(round(fps,1)),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            if cnt == frames_to_count:
                try:
                    fps = (frames_to_count/(time.time()-st))
                    st=time.time()
                    cnt=0
                    if fps>FPS:
                        TS+=0.001
                    elif fps<FPS:
                        TS-=0.001
                    else:
                        pass
                except:
                    pass
            cnt+=1
            
            
            
            cv2.imshow('TRANSMITTING VIDEO', frame)
            key = cv2.waitKey(int(1000*TS)) & 0xFF	
            if key == ord('q'):
                os._exit(1)
                TS=False
                break	
                

def audio_stream():
    s = socket.socket()
    s.bind((host_ip, (port-1)))

    s.listen(5)
    CHUNK = 1024
    wf = wave.open("temp.wav", 'rb')
    p = pyaudio.PyAudio()
    print('server listening at',(host_ip, (port-1)))
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    input=True,
                    frames_per_buffer=CHUNK)

    client_socket,addr = s.accept()

    while True:
        if client_socket:
            while True:
                data = wf.readframes(CHUNK)
                a = pickle.dumps(data)
                message = struct.pack("Q",len(a))+a
                client_socket.sendall(message)
                

from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=3) as executor:
    executor.submit(audio_stream)
    executor.submit(video_stream_gen)
    executor.submit(video_stream)



# Настройки логирования
logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
    handlers=[logging.FileHandler("./logs/server.log"), logging.StreamHandler()],
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def hash(password: str) -> str:
    """Хеширование данных"""
    return sha3.sha3_224(password.encode("utf-8")).hexdigest()

    def reg_logic(self, conn, addr):
        """
        Логика регистрации пользователя
        """
        data = json.loads(conn.recv(1024).decode())
        newuser_password, newuser_username = hash(data["password"]), data["username"]
        newuser_ip = addr[0]
        self.database.user_reg(newuser_ip, newuser_password, newuser_username)
        logger.info(f"Клиент {newuser_ip} -> регистрация прошла успешно")
        data = {"result": True}
        if newuser_ip in self.reg_list:
            self.reg_list.remove(newuser_ip)
            logging.info(f"Удалили клиента {newuser_ip} из списка регистрации")

        self.send_message(conn, data, newuser_ip)
        logger.info(f"Клиент {newuser_ip}. Отправили данные о результате регистрации")

    def auth_logic(self, conn, addr):
        """
        Логика авторизации клиента
        Запрос авторизации у нас априори меньше 1024, так что никакой цикл не запускаем
        """
        user_password = hash(json.loads(conn.recv(1024).decode())["password"])
        client_ip = addr[0]

        # Проверяем на существование данных
        auth_result, username = self.database.user_auth(client_ip, user_password)

        # Если авторизация прошла успешно
        if auth_result == 1:
            logger.info(f"Клиент {client_ip} -> авторизация прошла успешно")
            data = {"result": True, "body": {"username": username}}
            if client_ip not in self.authenticated_list:
                self.authenticated_list.append(client_ip)
                self.ip2username_dict[client_ip] = username
                logging.info(f"Добавили клиента {client_ip} в список авторизации")
        # Если авторизация не удалась, но пользователь с таким ip существует
        elif auth_result == 0:
            logger.info(f"Клиент {client_ip} -> авторизация не удалась")
            data = {"result": False, "description": "wrong auth"}
        # Если пользователя с таким ip не существует, то необходима регистрация
        else:
            logger.info(
                f"Клиент {client_ip} -> необходима предварительная регистрация в системе"
            )
            data = {"result": False, "description": "registration required"}
            if client_ip not in self.reg_list:
                self.reg_list.append(client_ip)
                logging.info(f"Добавили клиента {client_ip} в список регистрации")

        self.send_message(conn, data, client_ip)
        logger.info(f"Клиент {client_ip}. Отправили данные о результате авторизации")

        # Если была успешная авторизация - принимаем последующие сообщения от пользователя
        if auth_result == 1:
            self.message_logic(conn, client_ip)
