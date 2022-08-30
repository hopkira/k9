 # ===========================================================================
 # Simple routine to make K9's tail wag left and right
 # ===========================================================================
# Import the PCA9685 module.
import time
import board
import busio
import adafruit_pca9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 60

class Tail():
    
    def __init__(self) -> None:
        pca.channels[4].duty_cycle = 5121 # centre tail vertically
        pca.channels[5].duty_cycle = 5601	# tail centre
        pass

    def wag_h(self) -> None:
        pca.channels[4].duty_cycle = 5121 # centre tail vertically
        count= 0
        while count < 4:
            pca.channels[5].duty_cycle = 5201	# tail left
            time.sleep(0.25)
            pca.channels[5].duty_cycle = 7042	# tail right
            time.sleep(0.25)
            count +=1
        pca.channels[5].duty_cycle = 5601	# tail centre horizontally

    def wag_v(self) -> None:
        count= 0
        pca.channels[5].duty_cycle = 5601	# tail centre horizontally
        while count < 4:
            pca.channels[4].duty_cycle = 5921	# tail down
            # pwm.set_pwm(4, 0, 370)	# tail up
            time.sleep(0.25)
            pca.channels[4].duty_cycle = 4321	# tail up
            # pwm.set_pwm(4, 0, 270)	# tail down
            time.sleep(0.25)
            count +=1
        pca.channels[4].duty_cycle = 5121	# tail centre vertically
        # pwm.set_pwm(4, 0, 350)	# tail centre
    
    def center(self) -> None:
        pca.channels[4].duty_cycle = 5121	# tail centre vertically
        pca.channels[5].duty_cycle = 5601	# tail centre horizontally

    def up(self) -> None:
        pca.channels[5].duty_cycle = 5601	# tail centre horizontally
        pca.channels[4].duty_cycle = 4321	# tail up

    def down(self) -> None:
        pca.channels[5].duty_cycle = 5601	# tail centre horizontally
        pca.channels[4].duty_cycle = 5921	# tail down

#import Adafruit_PCA9685
#import time
#pwm = Adafruit_PCA9685.PCA9685()
#pwm.set_pwm_freq(60)		# set frequency to 60 Hz
# origianlly out of 4095, now 65535
# 320 -> 5121
# 325 -> 5201
# 350 -> 5601
# 440 -> 7042
