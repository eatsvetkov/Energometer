import serial
import time

cmd_op = b'\xa8\x01\x01\x01\x01\x01\x01\x01\x01\xe8\x46'
cmd_sn = b'\xa8\x08\x00\xf7\xe0'
cmd_energy_t1 = b'\xa8\x05\x00\x01\xf1\x85'
cmd_energy_t2 = b'\xa8\x05\x00\x02\xb1\x84'
cmd_energy_t3 = b'\xa8\x05\x00\x03\x70\x44'

# Открываем соединение
ser = serial.Serial(
    'COM10',
    9600,
    serial.EIGHTBITS,
    serial.PARITY_NONE,
    serial.STOPBITS_ONE
)

print('Connected:', ser.isOpen())


class uMercurySerial:

    def RecieveValue(self, cmd):
        ser.write(cmd)
        time.sleep(1)
        out = ser.read_all()
        res = ':'.join('{:02x}'.format(i) for i in out)
        return res

    def PerfomSn(self, cmd):
        sn = self.RecieveValue(cmd_sn).split(':')[1:-5]
        clear = []
        for i in sn:
            clear.append(int(i, 16))
        sn = "".join(str(i) for i in clear)
        print('Result Serial num: ', sn)

    def PerfomEn(self, cmd):
        en = self.RecieveValue(cmd).split(':')[1:-14]
        for i in range(0, len(en) - 1, 2):
            en[i], en[i + 1] = en[i + 1], en[i]
        en = float(int(("".join(str(x) for x in en)), 16)) / 1000
        print('Result Energy T: ', en)


mercury = uMercurySerial()


mercury.RecieveValue(cmd_op)
mercury.PerfomSn(cmd_sn)
mercury.PerfomEn(cmd_energy_t1)
mercury.PerfomEn(cmd_energy_t2)
mercury.PerfomEn(cmd_energy_t3)
