#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 16:36:05 2021

@author: S. Bartlett

Inputted from K.Ignatyev script that changes energy using a LUT for pitch & roll for S2 feedback 

"""
import epics
import math
from time import sleep
import numpy as np
from time import sleep
import matplotlib.pyplot as plt

def DegtoEv(x):
    return 1*1977.58/math.sin(x/(180/math.pi))

def coords(dataLines, skipLine):
    degRollPitch = {}
    count = 0
    for i in dataLines:
        if count > skipLine:
            degRollPitch[i.split()[0]] = [i.split()[1],i.split()[2]]
        else:
            count += 1
    return degRollPitch

def findPitch(degree):
    return poly(degree)
    
def findRoll(degree):
    return polyR(degree)  
    

#### User options ####   NB earlier iterations have a defined high & low energy setting

eV_feedback_auto = 50 # if energy change is larger than this the script will check for correct energy setup


#### load in look up tables and assign coordinates ####

pRVals = coords([j for j in open('/dls_sw/i18/software/gda/config/lookupTables/Si111/crystal2_converter_Si111_2022.txt').readlines()],2)
degAxis = [float(q) for q in pRVals]   # X axis
rollAx = [float(pRVals[w][0]) for w in pRVals]  # Y axis
pitchAx = [float(pRVals[e][1]) for e in pRVals]  # Yaxis

##### get Pitch model: polynomial #####

poly = np.poly1d(np.polyfit(degAxis, pitchAx, 2)) # int number indicates order of polyfit
print(f'Pitch = {poly}')  # model


### plot of pitch ###
'''
new_x = np.linspace(degAxis[0], degAxis[-1])
new_y = poly(new_x)
plt.plot(degAxis, pitchAx, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('Pitch')
plt.show()
plt.clf()
'''
#### Roll model function ####
polyR = np.poly1d(np.polyfit(degAxis, rollAx, 4)) # int number indicates order of polyfit
print(f'Roll = {polyR}')  # model

'''
dX = degAxis[7] - degAxis[-3]
dY = float(pRVals[str(degAxis[7])][1]) - float(pRVals[str(degAxis[-3])][1])
m = dY/dX
c = float(pRVals[str(degAxis[7])][1])- (degAxis[7]*m)
print(f'Roll: y={m}x+{c}')
'''

## Plot for Roll ###
'''
new_x = np.linspace(degAxis[0], degAxis[-1])
new_y =[m*r+c for r in new_x]
plt.plot(degAxis, pitchAx, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('Roll')
plt.show()
plt.clf()
'''
#### get pVs ########

RollSET = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL')
PitchSET = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH')

rollNotMoving = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL.DMOV')
pitchNotMoving = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH.DMOV')
braggNotMoving = epics.PV('BL18I-MO-DCM-01:BRAGG.DMOV')
#stripeNotMoving = epics.PV('BL18I-OP-HRM-01:MPY:DMOV')
#filter_D6_NotMoving = epics.PV('BL18I-DI-PHDGN-06:A:MP:DMOV')

fb_x = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL:FB.FBON')
fb_y = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH:FB.FBON')
fb_x_auto = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL:FB:AUTO')
fb_y_auto = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH:FB:AUTO')

dcmBraggTarget = epics.PV('BL18I-MO-DCM-01:BRAGG')
dcmBraggRBV = epics.PV('BL18I-MO-DCM-01:BRAGG.RBV')

#coating = epics.PV('BL18I-OP-HRM-01:MPY:SELECT') # Stripe on HRM
#filter_D6 = epics.PV('BL18I-DI-PHDGN-06:A:MP:SELECT') # d6 filter

#### Changes associated with Energy changes   ######
print('monitor changes')
while True:
    if abs((DegtoEv(dcmBraggTarget.get()) - DegtoEv(dcmBraggRBV.get()))) > eV_feedback_auto:#if dcmEnergyTarget.get() - dcmEnergyRBV.get() > pitchRollChange: ## need to change for Bragg
        moving = 0
        fb_x_auto.put(0)
        fb_y_auto.put(0) 
        sleep(0.5)
        fb_x.put(0)
        fb_y.put(0)
        RollSET.put(findRoll(float(dcmBraggTarget.get()))) 
        PitchSET.put(findPitch(float(dcmBraggTarget.get())))
        #coating.put('Silicon(no coat') # Si stripe value
        #filter_D6.put('gap')
        while moving == 0:
            if braggNotMoving.get() != 1 or rollNotMoving.get() != 1 or pitchNotMoving.get() != 1:# or stripeNotMoving.get() != 1 or filter_D6_NotMoving.get() != 1:
                moving = 0
                sleep(1)
            else:
                moving = 1
                print('PASSING CONTROL TO THE AUTO FEEDBACK')
                sleep(1)
                fb_x_auto.put(1)
                fb_y_auto.put(1)
                sleep(3)
    else:
        sleep(0.1)
