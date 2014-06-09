import pyfirmata
import math
import os
import time
import logging
logging.basicConfig()
logger = logging.getLogger()


class Board(object):
    '''
    This is a BotBoarduino
    '''
    def __init__(self):
        with open(os.path.join(os.path.expanduser('~'),'.arm_tty'), 'r') as f:
            self.tty = f.read().strip()
        self.start()

    def start(self):
        self.board = pyfirmata.Arduino(self.tty)
        self.iter8 = pyfirmata.util.Iterator(self.board)
        self.iter8.start()

    def stop(self):
        self.board.exit()

    def get_pin(self, pin):
        '''
        Conveniently gets the board's get_pin as part of this object
        '''
        return self.board.get_pin(pin)

class Arm(object):
    '''
    This is a lynxmotion arm
    '''
    def __init__(self):
        self.HUMERUS = 5.00
        self.ULNA = 5.75
        self.HAND = 5.00
        self.BASE = 3.25

        self.board = Board()

        # servos
        self.base = self.board.get_pin('d:2:s')
        self.shoulder = self.board.get_pin('d:3:s')
        self.elbow = self.board.get_pin('d:4:s')
        self.wrist = self.board.get_pin('d:10:s')
        self.wrist_rotate = self.board.get_pin('d:12:s')
        self.gripper = self.board.get_pin('d:11:s')

        self.starting_position()

    def exit(self):
        self.board.stop()

    def move(self, x, y, z, g, wa, wr, test=False):
        # offets for base and tip, relative to wrist, after rotation
        offset_x = math.cos(math.radians(wa)) * self.HAND
        offset_y = math.sin(math.radians(wa)) * self.HAND
        #print 'offset_x: ', offset_x
        #print 'offset_y: ', offset_y

        # wrist location
        wrist_x = x - offset_x 
        wrist_y = y - offset_y - self.BASE
        #print 'wrist_x: ', wrist_x
        #print 'wrist_y: ', wrist_y

        # inverse kinematics
        shoulder_wrist_line = math.sqrt(wrist_x**2 + wrist_y**2)
        if shoulder_wrist_line > self.HUMERUS + self.ULNA:
            logger.error('impossible range')
            return False
        #print 'sw line: ', shoulder_wrist_line

        angle1 = math.atan2(wrist_y, wrist_x)
        angle2 = math.acos((self.HUMERUS**2 - self.ULNA**2 + shoulder_wrist_line**2) / (2 * self.HUMERUS * shoulder_wrist_line))
        #print 'angle1: ', angle1
        #print 'angle2: ', angle2

        shoulder_angle = math.degrees(angle1 + angle2)
        elbow_angle = - (180 - math.degrees(math.acos((self.HUMERUS**2 + self.ULNA**2 - shoulder_wrist_line**2) / (2 * self.HUMERUS * self.ULNA))))

        # get positions from the angles
        shoulder_position = shoulder_angle
        elbow_position = -1 * elbow_angle
        wrist_position = 90 + wa - elbow_angle - shoulder_angle

        if test:
            logger.debug('Arm positions calculated:')
            logger.debug('----->base: ' + str(z))
            logger.debug('----->shoulder: ' + str(shoulder_position))
            logger.debug('----->elbow: ' + str(elbow_position))
            logger.debug('----->wrist: ' + str(wrist_position))
            logger.debug('---------->rotation: ' + str(wr))
            logger.debug('---------->gripper: ' + str(g))
            return True

        self.elbow.write(elbow_position)
        self.shoulder.write(shoulder_position)
        self.wrist.write(wrist_position)
        self.base.write(z)
        self.wrist_rotate.write(wr)
        self.gripper.write(g)
        self.current_position = (x, y, z, g, wa, wr)
        return True

    def starting_position(self):
        self.move(8, 6, 90, 90, 0, 90)

    def smooth_move(self, x, y, z, g, wa, wr):
        xo, yo, zo, go, wao, wro = self.current_position
        inch_increment = 0.1
        angle_increment = 1

        steps = int(max(abs(x - xo) / inch_increment,
                    abs(y - yo) / inch_increment,
                    abs(z - zo) / angle_increment,
                    abs(g - go) / angle_increment,
                    abs(wa - wao) / angle_increment,
                    abs(wr - wro) / angle_increment)) + 1

        logger.debug('steps computed: ' + str(steps))

        # start by setting equal to existing position
        xn = xo
        yn = yo
        zn = zo
        gn = go
        wan = wao
        wrn = wro

        for step in range(steps):
            if xn != x:
                xn += max(min(x - xn, inch_increment), -inch_increment)
            if yn != y:
                yn += max(min(y - yn, inch_increment), -inch_increment)
            if zn != z:
                zn += max(min(z - zn, angle_increment), -angle_increment)
            if gn != g:
                gn += max(min(g - gn, angle_increment), -angle_increment)
            if wan != wa:
                wan += max(min(wa - wan, angle_increment), -angle_increment)
            if wrn != wr:
                wrn += max(min(wr - wrn, angle_increment), -angle_increment)
            logger.debug('step ' + str(step) + ': ' + str((xn, yn, zn, gn, wan, wrn)))
            self.move(xn, yn, zn, gn, wan, wrn)
            time.sleep(.01)

        return True

    def gui(self):
        from Tkinter import Tk, Scale, HORIZONTAL
        root = Tk()
        x = Scale(root, from_=0, to=self.HUMERUS + self.ULN + 2, resolution=0.1,
                orient = HORIZONTAL, length = 400,
                command=lambda i: self.move(float(i), y.get(), z.get(), g.get(), wa.get(), wr.get())
                )
        x.pack()
        x.set(8)
        
        y = Scale(root, from_=0, to=self.HUMERUS + self.ULNA + 2, resolution=0.1,
                orient = HORIZONTAL, length = 400,
                command=lambda i: self.move(x.get(), float(i), z.get(), g.get(), wa.get(), wr.get())
                )
        y.pack()
        y.set(6)
        
        z = Scale(root, from_=0, to=175,
                orient = HORIZONTAL, length = 400,
                command=lambda i: self.move(x.get(), y.get(), float(i), g.get(), wa.get(), wr.get())
                )
        z.pack()
        z.set(90)
        
        g = Scale(root, from_=0, to=175,
                orient = HORIZONTAL, length = 400,
                command=lambda i: self.move(x.get(), y.get(), z.get(), float(i), wa.get(), wr.get())
                )
        g.pack()
        g.set(90)
        
        wa = Scale(root, from_=-85, to=85,
                orient = HORIZONTAL, length = 400,
                command=lambda i: self.move(x.get(), y.get(), z.get(), g.get(), float(i), wr.get())
                )
        wa.pack()
        wa.set(0)
        
        wr = Scale(root, from_=0, to=175,
                orient = HORIZONTAL, length = 400,
                command=lambda i: self.move(x.get(), y.get(), z.get(), g.get(), wa.get(), float(i))
                )
        wr.pack()
        wr.set(90)

        root.mainloop()
