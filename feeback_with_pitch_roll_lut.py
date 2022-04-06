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
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.interpolate import interp1d

def braggToPerp(bragg):
    return 12.71666138/math.cos(bragg/(180/math.pi)) - 0.35687044

def lutTable(eneryPoint):
    lutList = [5.53,5.974,6.308,7.1,8.121,9.486,11.406,14.312,19.244,23.298,29.63,41.238,44.93,52.282,59.296,64.014,70.339,75] #Bragg lookup values
    try:
        print(f'Moving to {lutList[eneryPoint]}')
        DCMSet.put(lutList[eneryPoint])
        return eneryPoint + 1
    except IndexError:
        print('all energies updated')
        return False

def DegtoEv(x):
    return 1*1977.58/math.sin(x/(180/math.pi))

def coords(dataLines, skipLine,openLUT):
    degRollPitch = {}
    count = 0
    for i in dataLines:
        if count >= skipLine:
            degRollPitch[i.split()[0]] = [i.split()[1],i.split()[2]]
        else:
            count += 1
            if lut_update == True:
                print(i)
                if openLUT == None:
                    openLUT = open(output_lutfile, 'w+')
                openLUT.write(i)
    #openLUT.close()
    return degRollPitch

def fbStable(Tol, loops):
    wait = True
    count = 0
    stableC = 0
    while wait == True:
        xP = XPlus.get()
        xM = XMinus.get()
        yP = YPlus.get()
        yM = XMinus.get()
        if abs(yP - yM) < Tol and abs(xP - xM) < Tol:
            stableC += 1
            sleep(1)
            if stableC > 5 :
                if abs(xP) < 0.005 and abs(yP) < 0.005:
                    print('WARNING - CURRENT IS LOW BEAM MAY BE OFF')
                    return False
                else:
                    print('AUTOFEEDBACK STABLE')
                    return True
        elif count > loops:
            print(f'FEEDBACK NOT STABLE AFTER {count} LOOPS')
            return False
        else:
            sleep(0.1)
            count +=1

def findPitch(degree, model):
    if model == True:
        return sply(degree)
    else:
        return poly(degree)
    
def findRoll(degree, model):
    if model == True:
        return splyR(degree)
    else:
        return polyR(degree)

def lutUpdate():
    rollUpD = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL.RBV')
    pitchUpD = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH.RBV')
    dcmVal = dcmBraggRBV.get()
    rollVal = rollUpD.get()
    pitchVal = pitchUpD.get()
    lutUpFile = open(output_lutfile, 'a')
    nl ='\n'
    tab = '\t'
    lutUpFile.write(f'{dcmVal}{tab}{rollVal}{tab}{pitchVal}{nl}')
    
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

eV_feedback_auto = 1000 # if energy change is larger than this the script will check for correct energy setup
lut_file = '/dls_sw/i18/software/gda/config/lookupTables/Si111/crystal2_converter_Si111.txt'

##### USER OPTION --> Options for creating updated look up tables ####

runLUT = False # Will run and create a new LUT table 
output_lutfile = '/dls/science/groups/i18/software/i18_development/pitch_roll_update_luts/' ##output directory ##
slit_tolerance = 0.1 #  differnce in current needs to be lower than this to pass
attempts = 100 # how many loops to check for stable feedback 1 = 1 second
overide = False # default to not update luts with low current - to overide change to True

##### USER OPTION --> Spline or Polynomial #####

spline = True # if spline funstion set as True otherwise False for polynomial

roll_polyfit_order = 4
pitch_polyfit_order = 3


##############################END####################################






##### GETTING MODEL & PLOTS #####

#### load in look up tables and assign coordinates ####
timestamp = folderTimeStamp()
output_lutfile = f'{output_lutfile}lut_update_{timestamp[:-6]}.txt' 
pRVals = coords([j for j in open(lut_file).readlines()],2,None )
degAxis = [float(q) for q in pRVals]   # X axis
rollAx = [float(pRVals[w][0]) for w in pRVals]  # Y axis
pitchAx = [float(pRVals[e][1]) for e in pRVals]  # Yaxis
autoUpdate = False

##### get Pitch model #####

if spline == True:
    sply = interp1d(degAxis, pitchAx)
else:
    poly = np.poly1d(np.polyfit(degAxis, pitchAx, pitch_polyfit_order)) # int number indicates order of polyfit
    print(f'Pitch : {poly}')  # model

### plot of pitch ###

new_x = np.linspace(degAxis[0], degAxis[-1])
if spline == True:
    new_y = sply(new_x)
else:
    new_y = poly(new_x)
plt.plot(degAxis, pitchAx, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('Pitch')
plt.show()
plt.clf()

#### Roll model function ####
if spline == True:
    splyR = interp1d(degAxis, rollAx)
else:
    polyR = np.poly1d(np.polyfit(degAxis, rollAx, roll_polyfit_order)) # int number indicates order of polyfit
    print(f'Roll : {polyR}')  # model

## Plot for Roll ###

new_x = np.linspace(degAxis[0], degAxis[-1])
if spline == True:
    new_y = splyR(new_x)
else:
    new_y = polyR(new_x)
plt.plot(degAxis, rollAx, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('Roll')
plt.show()
plt.clf()

'''
#### get pVs ########

RollSET = epics.PV('BL18I-MO-DCM-01:XTAL2:ROLL')
PitchSET = epics.PV('BL18I-MO-DCM-01:XTAL2:PITCH')
DCMSet = epics.PV('BL18I-MO-DCM-01:BRAGG')

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

## S2 Slit Values ##
XPlus = epics.PV('BL18I-AL-SLITS-02:X:PLUS:I')
XMinus = epics.PV('BL18I-AL-SLITS-02:X:MINUS:I')
YPlus = epics.PV('BL18I-AL-SLITS-02:Y:PLUS:I')
YMinus = epics.PV('BL18I-AL-SLITS-02:Y:MINUS:I')

energyNum = 0
lut_update = False # For testing Do you want to create an updated look up table while running? 
if runLUT == True:
    lut_update = True

#### Changes associated with Energy changes   ######
print('Monitoring changes for feedback')
while True:
    if runLUT == True:
        energyNum = lutTable(energyNum)
        if energyNum == False:
            runLUT = False
    if abs((DegtoEv(dcmBraggTarget.get()) - DegtoEv(dcmBraggRBV.get()))) > eV_feedback_auto:#if dcmEnergyTarget.get() - dcmEnergyRBV.get() > pitchRollChange: ## need to change for Bragg
        moving = 0
        print('Adjusting Pitch & Roll for Energy Move')
        fb_x_auto.put(0)
        fb_y_auto.put(0) 
        sleep(0.5)
        fb_x.put(0)
        fb_y.put(0)
        RollSET.put(findRoll(float(dcmBraggTarget.get())), spline) 
        PitchSET.put(findPitch(float(dcmBraggTarget.get())),spline)
        #coating.put('Silicon(no coat') # Si stripe value
        #filter_D6.put('gap')
        while moving == 0:
            if braggNotMoving.get() != 1 or rollNotMoving.get() != 1 or pitchNotMoving.get() != 1:# or stripeNotMoving.get() != 1 or filter_D6_NotMoving.get() != 1:
                moving = 0
                sleep(1)
            else:
                moving = 1
                print('CHECKING STATUS OF FEEDBACK')
                sleep(1)
                fb_x_auto.put(1)
                fb_y_auto.put(1)
                sleep(3)
                updateOk = fbStable(slit_tolerance, attempts)
                if lut_update == True:
                    if updateOk == True:
                        lutUpdate()
                    else:
                        print('LUT not updated due to low current - if you want to overide change overide to True')
                        if overide == True:
                            lutUpdate()
    else:
        sleep(0.1)

'''



''' 
#linear function 
dX = degAxis[7] - degAxis[-3]
dY = float(pRVals[str(degAxis[7])][1]) - float(pRVals[str(degAxis[-3])][1])
m = dY/dX
c = float(pRVals[str(degAxis[7])][1])- (degAxis[7]*m)
print(f'Roll: y={m}x+{c}')
'''