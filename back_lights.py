import board
import busio
import adafruit_pca9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 60

class BackLights():
    def __init__(self):
        self.level = 0
        self.set_level(self.level)

    def on(self):
        self.level = 1
        self.state()

    def off(self):
        self.level = 0
        self.state()

    def state(self):
        value = int(self.level * 65535)
        pca.channels[1].duty_cycle = value

    def get_level(self):
        return self.level