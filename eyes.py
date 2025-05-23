import board
import busio
import adafruit_pca9685
from memory import Memory
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 60

class Eyes():
    '''
    Sets brightness of K9's eye panel
    '''
    def __init__(self):
        self.mem = Memory()
        self.set_level(0.0)

    def set_level(self, level:float) -> None:
        '''
        Sets brightness to a percentage value (0.0 to 1.0)
        '''
        self.mem.storeState("eyes", str(level))
        value = int(level * 65535)
        pca.channels[0].duty_cycle = value
    
    def off(self) -> None:
        '''
        Turns eye panel off
        '''
        self.set_level(0)

    def on(self) -> None:
        '''
        Turns eye panel to full brightness
        '''
        self.set_level(1)

    def get_level(self) -> float:
        '''
        Returns current level of eye panel illumination as a percentage
        '''
        return float(self.mem.retrieveState("eyes"))