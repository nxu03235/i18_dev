import os
import glob
import matplotlib.pyplot as plt
import numpy as np


def coords(dataLines, skipLine):
    xyA = {}
    count = 0
    for i in dataLines:
        if count > skipLine:
            xyA[i.split()[0]] = i.split()[1]
        else:
            count += 1
    return xyA ## ordered in python 3 ####

### User Variables ###

harmonic_number = 5
crystal = 111 # 311

########################


### fit of new lookup table ####

xy = coords([i for i in open(max(glob.iglob('/dls/science/groups/i18/lookuptables/*'),key=os.path.getctime)).readlines()], 1) ### open last saved GDA lookup table ####
y = [float(xy[ii]) for ii in xy]
x = [float(jj) for jj in xy]
poly = np.poly1d(np.polyfit(x, y, 2)) # int number indicates order of polyfit
print(poly)  # model
new_x = np.linspace(x[0], x[-1])
new_y = poly(new_x)
plt.plot(x, y, "o", new_x, new_y, "--")
plt.xlabel('Bragg')
plt.ylabel('ID Gap')
plt.show()
plt.clf()


#### read in original lookup table ####

#for i in open('/dls_sw/i18/software/gda/config/lookupTables/Si' + str(crystal) + '/lookuptable_harmonic' + str(harmonic_number) + 'txt' ).readlines(): #convert to f string
gxy = coords([j for j in open('/home/nxu03235/bli18 scripts/lookuptable_harmonic5.txt' ).readlines()],2)
gy = [float(gxy[p]) for p in gxy]
gx = [l for l in gxy]

modelx =[]
samex = []
newT = open('/home/nxu03235/bli18 scripts/lookuptable_harmonic5_update.txt', 'w+' ) ##  new updated lookuptable
modelx = [float(xVal) for xVal in gx if float(xVal) < x[0] and float(xVal) > x[-1]]
newy_y = poly(modelx)
sel =0
for xVal in gx:
    if float(xVal) > x[0] or float(xVal) < x[-1]:
        newT.write(f'{str(xVal)}\t{gxy[xVal]}\n')
    else:
        if sel > 0:
            continue
        else:
            for newx in modelx:
                newT.write(f'{str(newx)}\t{newy_y[sel]}\n')
                sel +=1
newT.close()



newT = open('/home/nxu03235/bli18 scripts/lookuptable_harmonic5_update.txt', 'r' )
nxy = coords([j for j in newT.readlines()],-1)
ny = [float(nxy[p]) for p in nxy]
nx = [float(p) for p in nxy]
gx = [float(l) for l in gxy]
plt.plot(nx, ny,'--' ,gx,gy,'--' )
plt.xlabel('Bragg')
plt.ylabel('Gap')
plt.show()



#### Check ####
#check = str(raw_input('Do you want to update the LUTs (Y/N)?'))  #This maybe changed in python 3
#if check != 'Y':
#    print('Y not entered, update NOT saved')
#    exit()












