from gpiozero import CPUTemperature
import board
import busio
import adafruit_am2320

cputemp = CPUTemperature()

i2c = busio.I2C(board.SCL, board.SDA)
temp_sensor = adafruit_am2320.AM2320(i2c)
