# MicroPython MPU6050 driver
import machine

class accel:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        # Wake up the MPU6050 (reset sleep bit in PWR_MGMT_1 register)
        try:
            self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')
        except Exception as e:
            print("MPU6050 Init Error:", e)

    def get_raw_values(self):
        # Read 14 bytes starting from ACCEL_XOUT_H (0x3B)
        data = self.i2c.readfrom_mem(self.addr, 0x3B, 14)
        return data

    def conv_int16(self, high, low):
        val = (high << 8) | low
        if val >= 0x8000:
            val -= 0x10000
        return val

    def get_values(self):
        raw = self.get_raw_values()
        return {
            'AcX': self.conv_int16(raw[0], raw[1]),
            'AcY': self.conv_int16(raw[2], raw[3]),
            'AcZ': self.conv_int16(raw[4], raw[5]),
            'Tmp': self.conv_int16(raw[6], raw[7]) / 340.0 + 36.53,
            'GyX': self.conv_int16(raw[8], raw[9]),
            'GyY': self.conv_int16(raw[10], raw[11]),
            'GyZ': self.conv_int16(raw[12], raw[13])
        }