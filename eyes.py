import board
import busio
import adafruit_pca9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 60

class Eyes():
    def __init__(self):
        self.level = 0
        self.set_level(self.level)

    def set_level(self, level):
        self.level = level
        value = int(level * 65535)
        pca.channels[0].duty_cycle = value

    def get_level(self):
        return self.level