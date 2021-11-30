#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 16:36:05 2021

@author: S. Bartlett

modified from K.Ignatyev script that changes energy using a LUT for pitch & roll
only uses autofeedback option & Energy (compound) from 
"""
import epics
from time import sleep

#def findPitch(energy):
    #return m*energy+c #linear

#def findRoll(energy):
    #return m*energy+c #linear


#### USER Define ####
    
tolerance = 0.05 
pitchRollChange = 50 # if energy change is larger than this feedback is controlled by this script
sleepTime = 3 #seconds after bragg move after which the feedback is given to auto control



#### get pVs ########

RollSET = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL')
PitchSET = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH')

rollNotMoving = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL.DMOV')
pitchNotMoving = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH.DMOV')
braggNotMoving = epics.PV('BL18I-MO-DCM-01:BRAGG.DMOV')
stripeNotMoving = epics.PV('BL18I-OP-HRM-01:MPY:DMOV')
filter_D6_NotMoving = epics.PV('BL18I-DI-PHDGN-06:A:MP:DMOV')
fb_x = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL:FB.FBON')
fb_y = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH:FB.FBON')
fb_x_auto = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL:FB:AUTO')
fb_y_auto = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH:FB:AUTO')

fb_x_auto.put(1) 
fb_y_auto.put(1)

dcmEnergyTarget = epics.PV('BL18I-MO-DCM-01:ENERGY')
dcmEnergyRBV = epics.PV('BL18I-MO-DCM-01:ENERGY.RBV')
coating = epics.PV('BL18I-OP-HRM-01:MPY:SELECT') # Stripe on HRM
filter_D6 = epics.PV('BL18I-DI-PHDGN-06:A:MP:SELECT') # d6 filter




while True:
    if filter_D6_NotMoving.get() != 1:
        print('moving')
        sleep(1)

#filter_D6.put('gap') # no filter
#filter_D6.put('15 m Al') # 15 m Al filter

#if braggNotMoving.get() != 1 and rollNotMoving.get() != 1 and pitchNotMoving.get() and != 1 stripeNotMoving.get() and != 1 filter_D6_NotMoving.get() != 1:

#### Changes associated with Energy changes   ######

while True:
    if dcmEnergyTarget.get() - dcmEnergyRBV.get() > pitchRollChange:
        if dcmEnergyTarget.get() < 5000 : # define low energy
            print('Moving to LOW energy setup')
            fb_x_auto.put(0)
            fb_y_auto.put(0) 
            #sleep(0.5)
            fb_x.put(0)
            fb_y.put(0) 
            PitchSET.put(findPitch(dcmEnergyTarget.get()))
            RollSET.put(findRoll(dcmEnergyTarget.get()))
            coating.put('Silicon(no coat') # Si stripe value
            filter_D6.put('gap')
            while moving == 0:
                if braggNotMoving.get() != 1 or rollNotMoving.get() != 1 or pitchNotMoving.get() != 1 or stripeNotMoving.get() != 1 or filter_D6_NotMoving.get() != 1:
                    moving = 0
                else:
                    
                print('PASSING CONTROL TO THE AUTO FEEDBACK')
                fb_x_auto.put(1)
                fb_y_auto.put(1)
        else:
            print('Moving to HIGH energy setup')
            fb_x_auto.put(0) 
            fb_y_auto.put(0)
            #sleep(0.5)
            fb_x.put(0)
            fb_y.put(0) 
            PitchSET.put(findPitch(dcmEnergyTarget.get()))
            RollSET.put(findRoll(dcmEnergyTarget.get()))
            coating.put(19.2) # Rh stripe value
            if braggNotMoving.get() and rollNotMoving.get() and pitchNotMoving.get() and stripeNotMoving.get():
                print('PASSING CONTROL TO THE AUTO FEEDBACK')
                fb_x_auto.put(1)
                fb_y_auto.put(1)
    else:
        sleep(0.1)
'''


