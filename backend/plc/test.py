
import rk_mcprotocol as mc
import time
s= mc.open_socket('192.168.1.30',5000)
# print(mc.write_bit(s,'M15',[1]))
# time.sleep(0.2)
# mc.write_bit(s,'M15',[0])
# print(mc.read_sign_Dword(s,'D0',1,signed_type=True))
# mc.write_sign_Dword(s,'D0',[5500000],signed_type=True)
# print(mc.read_sign_Dword(s,'D0',1,signed_type=True))
# print(mc.write_bit(s,'m15', [1]))
# time.sleep(0.1)
# print(mc.write_bit(s,'m15',[0]))
#1,2,4,5
# mc.write_bit(s,'Y1',[1])
# mc.write_bit(s,'Y2',[1])
# mc.write_bit(s,'Y4',[1])
# mc.write_bit(s,'Y5',[1])
# # print(mc.read_bit(s,'Y1',5))
# mc.write_bit(s,'M1',[1])
# print(mc.read_bit(s,'X10',1))
# while True:
#     print(mc.write_bit(s,'M77',[1]))
#     time.sleep(0.5)
#     print(mc.write_bit(s,'M77',[0]))
#     time.sleep(0.5)
# mc.write_bit(s,'Y7',[1])
# print(mc.read_bit(s,'Y7',1))

# mc.write_bit(s,'M4',[1])
print("start")
mc.write_bit(s,'M77',[1])
count=0
while True:
    trigger= mc.read_bit(s,'Y14',2)
    if trigger[0]==1 or trigger[1]==1:
        time.sleep(0.8)
        print(mc.write_bit(s,'M77',[1]))
        print (count)
        count+=1
    if mc.read_bit(s,"X0",1)[0]==1:
        time.sleep(0.8)
        print(mc.write_bit(s,'M77',[1]))
        print (count)
        count+=1
        
    time.sleep(0.1)