#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 16:36:05 2021

@author: S. Bartlett

Perp lookup
spline function added
lut make up

"""
import epics
import math
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.interpolate import interp1d
import xml.etree.ElementTree as ET
import os as os

def braggToPerp(bragg, *args):
    return float(a)/math.cos(bragg/(180/math.pi)) - float(b)

def setBraggPerp(eneryPoint, conA, conB):
    print(f'Moving to {eneryPoint}')
    DCMSet.put(eneryPoint)
    PERPset.put(braggToPerp(eneryPoint,conA, conB))


def DegtoEv(x):
    return 1*1977.58/math.sin(x/(180/math.pi))

def coords(dataLines, skipLine):
    degRollPitch = {}
    count = 0
    for i in dataLines:
        if count >= skipLine:
            degRollPitch[i.split()[0]] = [i.split()[1],i.split()[2]]
        else:
            count += 1
            openLUT = open(output_lutfile, 'a')
            openLUT.write(i)
    return degRollPitch

def fbStable(Tol, loops):
    stable = 0
    tries = 0
    XPlus = epics.PV('BL18I-AL-SLITS-02:X:PLUS:I')
    XMinus = epics.PV('BL18I-AL-SLITS-02:X:MINUS:I')
    YPlus = epics.PV('BL18I-AL-SLITS-02:Y:PLUS:I')
    YMinus = epics.PV('BL18I-AL-SLITS-02:Y:MINUS:I')
    while True:
        X = abs(XPlus.get() - XMinus.get())
        Y = abs(YPlus.get() - YMinus.get())
        if XPlus.get() < 0.01 and YPlus.get() < 0.01:
            print('Feedback current low (< 0.01) - LUT Stopped!')
            return 'Low Current Values of S2 Slits' 
        if X < Tol and Y < Tol:
            stable +=1
            print(f'Feedback currently Stable...')
            sleep(1)
            if stable > 4:
                return True
        else:
            tries +=1
            print(f'Feedback currently Unstable - attempt number {tries}...')
            if tries == loops:
                print(f'Feedback Not Stable after {loops} attempts')
                return 'Feedback unable to stablise'
            sleep(1)

def findPitch(degree):
    return poly(degree)
    
def findRoll(degree):
    return polyR(degree)

def lutUpdate():
    dcmVal = dcmBraggRBV.get()
    rollVal = rollUpD.get()
    pitchVal = pitchUpD.get()
    lutUpFile = open(output_lutfile, 'a')
    nl ='\n'
    tab = '\t'
    lutUpFile.write(f'{dcmVal}{tab}{rollVal}{tab}{pitchVal}{nl}')
    lutUpFile.close()
    
def folderTimeStamp():                                                      
    dT = []                                                                 
    for i in str(datetime.now()):                                           
        try:                                                                
            i = int(i)                                                      
            dT.append(str(i))                                               
        except:                                                             
            pass                                                            
    dT = ''.join(dT)                                                        
    return dT                                                                


##### USER OPTION --> for load in file and when to set feedback #######

lut_file = '/dls_sw/i18/software/gda/config/lookupTables/Si111/crystal2_converter_Si111.txt'
lutList = [6.308,7.1,8.121,9.486,11.406,14.312,19.244,23.298,29.63,41.238] #[5.53,5.974,6.308,7.1,8.121,9.486,11.406,14.312,19.244,23.298,29.63,41.238,44.93,52.282,59.296,64.014,70.339,75] #Bragg lookup values

##### USER OPTION --> Options for creating updated look up tables ####

output_lutfile = '/dls/science/groups/i18/software/i18_development/pitch_roll_update_luts/' ##output directory ##
slit_tolerance = 0.1 # differnce in current needs to be lower than this to be accpeted to write
attempts = 10 # how many loops to check for feedback has stabilised (1 = 1 second)

overide = False # if True, overides the slit checks to write pitch & roll irrespective

##### USER OPTION --> Spline or Polynomial #####

spline = True # spline function if set as True otherwise False for polynomial

roll_polyfit_order = 4 # polynomial fit orders
pitch_polyfit_order = 3 # polynomial fit orders


##############################END####################################




##### GETTING MODEL & PLOTS #####

#### load in look up tables and assign coordinates ####
timestamp = folderTimeStamp()
output_lutfile = f'{output_lutfile}lut_update_{timestamp[:-6]}.txt' 
pRVals = coords([j for j in open(lut_file).readlines()],2)
degAxis = [float(q) for q in pRVals]   # X axis
rollAx = [float(pRVals[w][0]) for w in pRVals]  # Y axis
pitchAx = [float(pRVals[e][1]) for e in pRVals]  # Yaxis

##### get Pitch model #####

if spline == True:
    poly = interp1d(degAxis, pitchAx)
else:
    poly = np.poly1d(np.polyfit(degAxis, pitchAx, pitch_polyfit_order))
    print(f'Pitch : {poly}')  # model

### plot of pitch ###

new_x = np.linspace(degAxis[0], degAxis[-1])
new_y = poly(new_x)
plt.plot(degAxis, pitchAx, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('Pitch')
plt.show()
plt.clf()

#### Roll model function ####
if spline == True:
    polyR = interp1d(degAxis, rollAx)
else:
    polyR = np.poly1d(np.polyfit(degAxis, rollAx, roll_polyfit_order))
    print(f'Roll : {polyR}')  # model

## Plot for Roll ###

new_x = np.linspace(degAxis[0], degAxis[-1])
new_y = polyR(new_x)
plt.plot(degAxis, rollAx, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('Roll')
plt.show()
plt.clf()

##### read Perp converter Vals #####

tree = ET.parse('/dls_sw/i18/software/gda/config/lookupTables/Si111/Deg_dcm_perp_mm_converter.xml')
root = tree.getroot()
xml = [i.text for i in root]
getNum = True
getNum2 = False
a = ''
b = ''
for i in xml[:1]:
    for j in i:
        if j != '/' and getNum == True:
            a += j
        else:
            getNum = False
            if j == '-':
                getNum2 = True
            else:
                if getNum2 == True:
                    b += j



#### get pVs ########

RollSET = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL')
PitchSET = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH')
DCMSet = epics.PV('BL18I-MO-DCM-01:BRAGG')
PERPset = epics.PV('BL18I-MO-DCM-01:PERP')

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

rollUpD = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL.RBV')
pitchUpD = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH.RBV')

#coating = epics.PV('BL18I-OP-HRM-01:MPY:SELECT') # Stripe on HRM
#filter_D6 = epics.PV('BL18I-DI-PHDGN-06:A:MP:SELECT') # d6 filter

#### Changes associated with Energy changes   ######

for ii in lutList:
    fb_x_auto.put(0)
    fb_y_auto.put(0) 
    sleep(0.5)
    fb_x.put(0)
    fb_y.put(0)    # auto FB off
    sleep(0.5)
    setBraggPerp(ii, a, b) # move to Bragg & perp
    RollSET.put(findRoll(float(dcmBraggTarget.get())))
    PitchSET.put(findPitch(float(dcmBraggTarget.get())))
    move = 0
    while move == 0:
        if braggNotMoving.get() != 1 or rollNotMoving.get() != 1 or pitchNotMoving.get() != 1:# or stripeNotMoving.get() != 1 or filter_D6_NotMoving.get() != 1: ## Need to add perp moving
            move = 1
        else:
            sleep(0.5)
    print('CHECKING STATUS OF FEEDBACK')
    sleep(1)
    fb_x_auto.put(1)  # does this gostraight to Auto??
    fb_y_auto.put(1)
    sleep(3)
    updateOk = fbStable(slit_tolerance, attempts)
    if updateOk == True:
        lutUpdate()
    else:
        print(f'LUT not updated due to {updateOk}')
        if overide == True:
            lutUpdate()
        else:
            print('Quiting LUT update')
            os.remove(output_lutfile)  # will remove current lut file
            exit()

print('LUT completed')



