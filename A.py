import socket                   

s = socket.socket()           
host = socket.gethostname()   
port = 60000                    

s.connect((host, port))

filename = "code.txt"

f = open(filename,'rb')
chunk = f.read(1024)
while chunk:
   s.send(chunk)
   print('Sent ',repr(chunk))
   chunk = f.read(1024)
f.close()

s.shutdown(socket.SHUT_WR)

print('Sent the file')



with open('code_copy.txt', 'wb') as f:
    while True:
        print('receiving data...')
        data = s.recv(1024)
        print('data=%s', (data))
        if not data:
            break
        f.write(data)



s.close()
print('connection closed')