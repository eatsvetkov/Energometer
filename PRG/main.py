import socket
from time import sleep
import _thread
import os
from machine import RTC
import ntptime
import network
from machine import UART, Pin
import select
import ujson

# команды опроса счетчика Меркурий 230
cmd_op = b'\xa8\x01\x01\x01\x01\x01\x01\x01\x01\xe8\x46'
cmd_sn = b'\xa8\x08\x00\xf7\xe0'
cmd_energy_t1 = b'\xa8\x05\x00\x01\xf1\x85'
cmd_energy_t2 = b'\xa8\x05\x00\x02\xb1\x84'
cmd_energy_t3 = b'\xa8\x05\x00\x03\x70\x44'

# объявление экземпляра RTC
rtc = RTC()

# считывание значений из списоков EEPROM
try:
    storage = open('config.json', 'r')
    config = ujson.load(storage)
    storage.close()
    # print(config['name'])
    print(config)
except Exception:
    print('Creating json...')
    config = {
        'pulse_hot': '0',
        'pulse_cld': '0',
        'save_hot': '0',
        'save_cld': '0',
        'save_t1': '0',
        'save_t2': '0',
        'save_t3': '0',
        'save_dt': '0'
    }
    storage = open('config.json', 'w')
    ujson.dump(config, storage)
    storage.close()

pulse_hot = config['pulse_hot']
pulse_cld = config['pulse_cld']
save_hot = config['save_hot']
save_cld = config['save_cld']
save_t1 = config['save_t1']
save_t2 = config['save_t2']
save_t3 = config['save_t3']
save_dt = config['save_dt']

# создание глобальных переменных энергии по тарифам
mercury_t1 = 0
mercury_t2 = 0
mercury_t3 = 0

# настройки web-сервера
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

# триггерная переменная Pin
cond_pin = False


# функция подсчета импульсов с Pin
def switch(pin_in_num, pulse_type):
    global cond_pin
    global pulse_hot
    global pulse_cld
    pin = not Pin(pin_in_num, Pin.IN, Pin.PULL_UP).value()
    if pulse_type == "pulse_hot":
        if pin == 1 and cond_pin is False:
            pulse_hot = cntr(1, pulse_hot, pulse_type)
    if pulse_type == "pulse_cld":
        if pin == 1 and cond_pin is False:
            pulse_cld = cntr(1, pulse_cld, pulse_type)
    if pin == 1 and not cond_pin:
        cond_pin = True
    if pin == 0:
        cond_pin = False


# функция вывода значений на web-страницу
def web_page():
    html = """
    <html>
    <head>
        <title>Energy server</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
            <style>
                html{
                    font-family: Helvetica;
                    display:inline-block;
                    margin: 0px auto;
                    text-align: center;
                }
                h1{
                    color: #0F3376;
                    padding: 2vh;
                }
                h2{
                    color: #0F3376;
                    padding: 1vh;
                }
                p{
                    font-size: 1.5rem;
                }
                .button{
                    display: inline-block;
                    background-color: #e7bd3b;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    padding: 16px 40px;
                    text-decoration: none;
                    font-size: 30px;
                    margin: 2px;
                    cursor: pointer;

                }
                .button2{
                    background-color: #4286f4;
                    padding: 8px 20px;
                }
            </style>
    </head>
    <body>
    <h1>Water meters</h1>
    <p>Hot: """ + str(pulse_hot) + """ liters</p>
    <p>Cold: """ + str(pulse_cld) + """ liters</p>
    <h1>Energy meters</h1>
    <p>T1: """ + str(mercury_t1) + """ kWh</p>
    <p>T2: """ + str(mercury_t2) + """ kWh</p>
    <p>T3: """ + str(mercury_t3) + """ kWh</p>
    <p>
        <a href="/">
            <button class="button">Refresh</button>
        </a>
    </p>
    <p>Saved value:</p>
    <p>Hot: """ + str(save_hot) + """ liters</p>
    <p>Cold: """ + str(save_cld) + """ liters</p>
    <p>T1: """ + str(save_t1) + """ kWh</p>
    <p>T2: """ + str(save_t2) + """ kWh</p>
    <p>T3: """ + str(save_t3) + """ kWh</p>
    <p>from: """ + str(save_dt) + """</p>
    <p>
        <a href="/?num=save">
            <button class="button">Save value</button>
        </a>
    </p>
    <h2>Settings </h2>
    <p>
        <a href="/?num=h_one_plus">
            <button class="button button2" style="background-color:red;">+1H</button>
        </a>
    </p>
    <p>
        <a href="/?num=h_ten_plus">
            <button class="button button2" style="background-color:red;">+10H</button>
        </a>
    </p>
    <p>
        <a href="/?num=h_hun_plus">
            <button class="button button2" style="background-color:red;">+100H</button>
        </a>
    </p>
    <p>
        <a href="/?num=h_tho_plus">
            <button class="button button2" style="background-color:red;">+1000H</button>
        </a>
    </p>
    <p>
        <a href="/?num=h_ttho_plus">
            <button class="button button2" style="background-color:red;">+10000H</button>
        </a>
    </p>
    <p>
        <a href="/?num=c_one_plus">
            <button class="button button2">+1C</button>
        </a>
    </p>
    <p>
        <a href="/?num=c_ten_plus">
            <button class="button button2">+10HC</button>
        </a>
    </p>
    <p>
        <a href="/?num=c_hun_plus">
            <button class="button button2">+100C</button>
        </a>
    </p>
    <p>
        <a href="/?num=c_tho_plus">
            <button class="button button2">+1000C</button>
        </a>
    </p>
    <p>
        <a href="/?num=c_ttho_plus">
            <button class="button button2">+10000C</button>
        </a>
    </p>
    <p>
        <a href="/?num=res">
            <button class="button button2" style="background-color:gray;">Reset</button>
        </a>
    </p>
    </body
    </html>
    """
    return html


# функция добавления значения счетчика с web-страницы
def cntr(plus_value, pulse_value, pulse_type):
    storage = open('config.json', 'w')
    if plus_value != 0:
        pulse_value = int(config[pulse_type])
        pulse_value = pulse_value + plus_value
        config[pulse_type] = str(pulse_value)
    else:
        pulse_value = 0
        config[pulse_type] = str(pulse_value)
    ujson.dump(config, storage)
    storage.close()
    return pulse_value


# функция обработки действий с web-страницы
def srv():
    global pulse_hot
    global pulse_cld
    global mercury_t1
    global mercury_t2
    global mercury_t3
    global dt
    global save_hot
    global save_cld
    global save_t1
    global save_t2
    global save_t3
    global save_dt
    while True:
        conn, addr = s.accept()
        request = str(conn.recv(1024))

        h_plus_1 = request.find('/?num=h_one_plus')
        h_plus_10 = request.find('/?num=h_ten_plus')
        h_plus_100 = request.find('/?num=h_hun_plus')
        h_plus_1000 = request.find('/?num=h_tho_plus')
        h_plus_10000 = request.find('/?num=h_ttho_plus')
        c_plus_1 = request.find('/?num=c_one_plus')
        c_plus_10 = request.find('/?num=c_ten_plus')
        c_plus_100 = request.find('/?num=c_hun_plus')
        c_plus_1000 = request.find('/?num=c_tho_plus')
        c_plus_10000 = request.find('/?num=c_ttho_plus')
        res = request.find('/?num=res')
        save = request.find('/?num=save')

        if h_plus_1 == 6:
            pulse_hot = cntr(1, pulse_hot, 'pulse_hot')
        if h_plus_10 == 6:
            pulse_hot = cntr(10, pulse_hot, 'pulse_hot')
        if h_plus_100 == 6:
            pulse_hot = cntr(100, pulse_hot, 'pulse_hot')
        if h_plus_1000 == 6:
            pulse_hot = cntr(1000, pulse_hot, 'pulse_hot')
        if h_plus_10000 == 6:
            pulse_hot = cntr(10000, pulse_hot, 'pulse_hot')
        if c_plus_1 == 6:
            pulse_cld = cntr(1, pulse_cld, 'pulse_cld')
        if c_plus_10 == 6:
            pulse_cld = cntr(10, pulse_cld, 'pulse_cld')
        if c_plus_100 == 6:
            pulse_cld = cntr(100, pulse_cld, 'pulse_cld')
        if c_plus_1000 == 6:
            pulse_cld = cntr(1000, pulse_cld, 'pulse_cld')
        if c_plus_10000 == 6:
            pulse_cld = cntr(10000, pulse_cld, 'pulse_cld')
        if res == 6:
            pulse_hot = cntr(0, pulse_hot, 'pulse_hot')
            pulse_cld = cntr(0, pulse_cld, 'pulse_cld')
            save_hot = 0
            save_cld = 0
            save_t1 = 0
            save_t2 = 0
            save_t3 = 0
            save_dt = 0
            storage = open('config.json', 'w')
            config['save_hot'] = str(save_hot)
            config['save_cld'] = str(save_cld)
            config['save_t1'] = str(save_t1)
            config['save_t2'] = str(save_t2)
            config['save_t3'] = str(save_t3)
            config['save_dt'] = str(save_dt)
            ujson.dump(config, storage)
            storage.close()
        if save == 6:
            try:
                ntptime.settime()
            except Exception:
                None
            dt = rtc.datetime()
            save_hot = pulse_hot
            save_cld = pulse_cld
            save_t1 = mercury_t1
            save_t2 = mercury_t2
            save_t3 = mercury_t3
            save_dt = str(str(dt[2]) + '.' + str(dt[1]) + '.' + str(dt[0]))
            storage = open('config.json', 'w')
            config['save_hot'] = str(save_hot)
            config['save_cld'] = str(save_cld)
            config['save_t1'] = str(save_t1)
            config['save_t2'] = str(save_t2)
            config['save_t3'] = str(save_t3)
            config['save_dt'] = str(save_dt)
            ujson.dump(config, storage)
            storage.close()
        response = web_page()
        try:
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(response)
            conn.close()
        except Exception:
            conn.close()


def cnnctn():
    ssid = 'iphoneegor'
    password = 'Password'
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.ifconfig(
        ('172.20.10.14', '255.255.255.240', '172.20.10.1', '8.8.8.8')
    )
    station.connect(ssid, password)

    while not station.isconnected():
        pass

    print('Connection successful')
    print(station.ifconfig())


class uMercurySerial:

    def __init__(
        self,
        uart_id,
        baudrate=9600,
        data_bits=8,
        stop_bits=1,
        parity=None,
        pins=None,
        ctrl_pin=None
    ):
        self._uart = UART(
            uart_id,
            baudrate=baudrate,
            bits=data_bits,
            parity=parity,
            stop=stop_bits,
            timeout_char=10
        )

        self.poll = select.poll()
        self.poll
        self.poll.register(self._uart, select.POLLIN)

    def RecieveValue(self, cmd):
        prmssn_to_read = False
        self._uart.write(cmd)
        if len(self.poll.poll(1000)) != 0:
            prmssn_to_read = True
        while not prmssn_to_read:
            pass
        out = self._uart.read()
        res = ':'.join('{:02x}'.format(c) for c in out)
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
        # print('Result Energy T: ', en)
        return en


mercury = uMercurySerial(
    uart_id=2,
    baudrate=9600,
    data_bits=8,
    stop_bits=1,
    parity=None
)


def get_energy():
    global mercury_t1
    global mercury_t2
    global mercury_t3
    while True:
        mercury_t1 = mercury.PerfomEn(cmd_energy_t1)
        mercury_t2 = mercury.PerfomEn(cmd_energy_t2)
        mercury_t3 = mercury.PerfomEn(cmd_energy_t3)
        switch(26, 'pulse_hot')
        switch(27, 'pulse_cld')


mercury.RecieveValue(cmd_op)
print('UART is connected')
sleep(2)  # исключение бесонечного цикла при запуске программы


p1 = _thread.start_new_thread(srv, [])
p2 = _thread.start_new_thread(cnnctn, [])
p3 = _thread.start_new_thread(get_energy, [])
