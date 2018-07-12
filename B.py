import socket                  

port = 60000                   
s = socket.socket()            
host = socket.gethostname()     
s.bind((host, port))           
s.listen(5)                    

print 'Node B listening....'

while True:
    conn, addr = s.accept()     
    print 'Got connection from', addr

    with open('received_code.txt', 'wb') as f:
        while True:
            print('receiving data...')
            data = conn.recv(1024)
            print('data=%s', (data))
            if not data:
                break
            f.write(data)

    f = open('received_code.txt','rb')
    chunk = f.read(1024)
    while (chunk):
       conn.send(chunk)
       print('Sent ',repr(chunk))
       chunk = f.read(1024)
    f.close()

    print('Done sending')
    conn.close()
