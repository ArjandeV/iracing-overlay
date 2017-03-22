#!python3
import irsdk
ir = irsdk.IRSDK()
ir.startup(test_file='data.bin')
print(ir['Speed'])