# Функция преобразования байтового массива в строку.
# Код предусматривает запись однозначного числа в виде двузначного с
# добавлением 0.
# Разработано для программы Cntr как наиболее элегантное решение.

# Приведенный пример выводит результат запроса номера счетчика и даты
# изготовления.


cmd = b'\x23\x2b\x15\x44\x01\x08\x12'


def xStrinFromBytearray(xBytearray):
    xString = str()
    for i in range(len(xBytearray)):
        xString = xString + str('%.2d' % xBytearray[i])
    return xString


print('Serial number:', xStrinFromBytearray(cmd)[:8])
print('Produced:', xStrinFromBytearray(cmd)[8:])
