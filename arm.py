#!/usr/bin/python
# -*- coding: utf-8 -*-
# move a servo from a Tk slider - scruss 2012-10-28
 
import pyfirmata
import math
 
# don't forget to change the serial port to suit
board = pyfirmata.Arduino('/dev/tty.usbserial-A4WTODKD')
 
# start an iterator thread so
# serial buffer doesn't overflow
iter8 = pyfirmata.util.Iterator(board)
iter8.start()
 
# servos
base = board.get_pin('d:2:s')
shoulder = board.get_pin('d:3:s')
elbow = board.get_pin('d:4:s')
wrist = board.get_pin('d:10:s')
wrist_rotate = board.get_pin('d:12:s')
gripper = board.get_pin('d:11:s')

# arm size
humerus = 5.00
ulna = 5.75
hand = 5.00
base_height = 3.75

def arm(x, y, z, g, wa, wr, test=False):
    # offets for base and tip, relative to wrist, after rotation
    offset_x = math.cos(math.radians(wa)) * hand
    offset_y = math.sin(math.radians(wa)) * hand
    #print 'offset_x: ', offset_x
    #print 'offset_y: ', offset_y

    # wrist location
    wrist_x = x - offset_x 
    wrist_y = y - offset_y - base_height
    #print 'wrist_x: ', wrist_x
    #print 'wrist_y: ', wrist_y

    # inverse kinematics
    shoulder_wrist_line = math.sqrt(wrist_x**2 + wrist_y**2)
    if shoulder_wrist_line > humerus + ulna:
        print 'impossible range'
        return False
    #print 'sw line: ', shoulder_wrist_line

    angle1 = math.atan2(wrist_y, wrist_x)
    angle2 = math.acos((humerus**2 - ulna**2 + shoulder_wrist_line**2) / (2 * humerus * shoulder_wrist_line))
    #print 'angle1: ', angle1
    #print 'angle2: ', angle2

    shoulder_angle = math.degrees(angle1 + angle2)
    elbow_angle = - (180 - math.degrees(math.acos((humerus**2 + ulna**2 - shoulder_wrist_line**2) / (2 * humerus * ulna))))

    # get positions from the angles
    shoulder_position = shoulder_angle
    elbow_position = -1 * elbow_angle
    wrist_position = 90 + wa - elbow_angle - shoulder_angle

    if test:
        print('Arm positions calculated:')
        print('----->base: ' + str(z))
        print('----->shoulder: ' + str(shoulder_position))
        print('----->elbow: ' + str(elbow_position))
        print('----->wrist: ' + str(wrist_position))
        print('---------->rotation: ' + str(wr))
        print('---------->gripper: ' + str(g))
        return True

    elbow.write(elbow_position)
    shoulder.write(shoulder_position)
    wrist.write(wrist_position)
    base.write(z)
    wrist_rotate.write(wr)
    gripper.write(g)
    return True

def starting_position():
    arm(8, 6, 90, 90, 0, 90)

def gui():
    from Tkinter import Tk, Scale, HORIZONTAL
    root = Tk()
    x = Scale(root, from_=0, to=humerus + ulna, resolution=0.1,
              orient = HORIZONTAL, length = 400,
              command=lambda i: arm(float(i), y.get(), z.get(), g.get(), wa.get(), wr.get())
             )
    x.pack()
    x.set(8)
    
    y = Scale(root, from_=0, to=humerus + ulna, resolution=0.1,
              orient = HORIZONTAL, length = 400,
              command=lambda i: arm(x.get(), float(i), z.get(), g.get(), wa.get(), wr.get())
              )
    y.pack()
    y.set(6)
    
    z = Scale(root, from_=0, to=175,
              orient = HORIZONTAL, length = 400,
              command=lambda i: arm(x.get(), y.get(), float(i), g.get(), wa.get(), wr.get())
              )
    z.pack()
    z.set(90)
    
    g = Scale(root, from_=0, to=175,
               orient = HORIZONTAL, length = 400,
               command=lambda i: arm(x.get(), y.get(), z.get(), float(i), wa.get(), wr.get())
               )
    g.pack()
    g.set(90)
    
    wa = Scale(root, from_=-85, to=85,
               orient = HORIZONTAL, length = 400,
               command=lambda i: arm(x.get(), y.get(), z.get(), g.get(), float(i), wr.get())
               )
    wa.pack()
    wa.set(0)
    
    wr = Scale(root, from_=0, to=175,
              orient = HORIZONTAL, length = 400,
              command=lambda i: arm(x.get(), y.get(), z.get(), g.get(), wa.get(), float(i))
              )
    wr.pack()
    wr.set(90)

    root.mainloop()

starting_position()
