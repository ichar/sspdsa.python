

'%x' % 240
'%x%x' % (255,1)

0xf0
0xf0f1

hex(240)+hex(1)

bytes(0xf00x01)
x=0xf001
x1=b'\xf0\x01'
x1.decode()
x1.encode()

x1=b'\xf0\x01'

bytearray(b'\xf1')

b = bytearray(b'')
b.append(0xf1)
b.append(0x01)

from bitstring import BitArray
c = BitArray(b'\xf1\x01')
c
c.bin
BitArray(b)

