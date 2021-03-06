#!/usr/bin/env python3
# Author: Piyush Agram
# Copyright 2016
#Heresh Fattahi, Adopted for stack

import argparse
import logging
import isce
import isceobj
import mroipac
import os
import s1a_isce_utils as ut

def createParser():
    parser = argparse.ArgumentParser( description='Use polynomial offsets and create burst by burst interferograms')

    parser.add_argument('-m', '--reference', dest='reference', type=str, required=True,
            help='Directory with reference acquisition')

    parser.add_argument('-s', '--secondary', dest='secondary', type=str, required=True,
            help='Directory with secondary acquisition')

    parser.add_argument('-b', '--baseline_file', dest='baselineFile', type=str, required=True,
                help='An output text file which contains the computed baseline')


    return parser

def cmdLineParse(iargs = None):
    parser = createParser()
    return parser.parse_args(args=iargs)



#logger = logging.getLogger('isce.topsinsar.runPreprocessor')

def main(iargs=None):
    '''Compute baseline.
    '''
    inps=cmdLineParse(iargs)
    from isceobj.Planet.Planet import Planet
    import numpy as np



    #swathList = self._insar.getInputSwathList(self.swaths)
    #commonBurstStartReferenceIndex = [-1] * self._insar.numberOfSwaths
    #commonBurstStartSecondaryIndex = [-1] * self._insar.numberOfSwaths
    #numberOfCommonBursts = [0] * self._insar.numberOfSwaths

    referenceSwathList = ut.getSwathList(inps.reference)
    secondarySwathList = ut.getSwathList(inps.secondary)
    swathList = list(sorted(set(referenceSwathList+secondarySwathList)))

    #catalog = isceobj.Catalog.createCatalog(self._insar.procDoc.name)
    baselineDir = os.path.dirname(inps.baselineFile)
    os.makedirs(baselineDir, exist_ok=True)

    f = open(inps.baselineFile , 'w')

    for swath in swathList:

        referencexml = os.path.join( inps.reference, 'IW{0}.xml'.format(swath))
        secondaryxml = os.path.join( inps.secondary, 'IW{0}.xml'.format(swath))

        if os.path.exists(referencexml) and os.path.exists(secondaryxml):

            reference = ut.loadProduct(os.path.join(inps.reference , 'IW{0}.xml'.format(swath)))
            secondary = ut.loadProduct(os.path.join(inps.secondary , 'IW{0}.xml'.format(swath)))

            minReference = reference.bursts[0].burstNumber
            maxReference = reference.bursts[-1].burstNumber

            minSecondary = secondary.bursts[0].burstNumber
            maxSecondary = secondary.bursts[-1].burstNumber

            minBurst = max(minSecondary, minReference)
            maxBurst = min(maxSecondary, maxReference)
            print ('minSecondary,maxSecondary',minSecondary, maxSecondary)
            print ('minReference,maxReference',minReference, maxReference)
            print ('minBurst, maxBurst: ', minBurst, maxBurst)
            refElp = Planet(pname='Earth').ellipsoid
            Bpar = []
            Bperp = []

            for ii in range(minBurst, maxBurst + 1):


                ###Bookkeeping
                #commonBurstStartReferenceIndex[swath-1] = minBurst
                #commonBurstStartSecondaryIndex[swath-1]  = commonSecondaryIndex
                #numberOfCommonBursts[swath-1] = numberCommon


                #catalog.addItem('IW-{0} Number of bursts in reference'.format(swath), reference.numberOfBursts, 'baseline')
                #catalog.addItem('IW-{0} First common burst in reference'.format(swath), minBurst, 'baseline')
                #catalog.addItem('IW-{0} Last common burst in reference'.format(swath), maxBurst, 'baseline')
                #catalog.addItem('IW-{0} Number of bursts in secondary'.format(swath), secondary.numberOfBursts, 'baseline')
                #catalog.addItem('IW-{0} First common burst in secondary'.format(swath), minBurst + burstOffset, 'baseline')
                #catalog.addItem('IW-{0} Last common burst in secondary'.format(swath), maxBurst + burstOffset, 'baseline')
                #catalog.addItem('IW-{0} Number of common bursts'.format(swath), numberCommon, 'baseline')

                #refElp = Planet(pname='Earth').ellipsoid
                #Bpar = []
                #Bperp = []

                #for boff in [0, numberCommon-1]:
                    ###Baselines at top of common bursts
                mBurst = reference.bursts[ii-minReference]
                sBurst = secondary.bursts[ii-minSecondary]

                    ###Target at mid range 
                tmid = mBurst.sensingMid
                rng = mBurst.midRange
                referenceSV = mBurst.orbit.interpolate(tmid, method='hermite')
                target = mBurst.orbit.rdr2geo(tmid, rng)

                slvTime, slvrng = sBurst.orbit.geo2rdr(target)
                secondarySV = sBurst.orbit.interpolateOrbit(slvTime, method='hermite')

                targxyz = np.array(refElp.LLH(target[0], target[1], target[2]).ecef().tolist())
                mxyz = np.array(referenceSV.getPosition())
                mvel = np.array(referenceSV.getVelocity())
                sxyz = np.array(secondarySV.getPosition())

                aa = np.linalg.norm(sxyz-mxyz)
                costheta = (rng*rng + aa*aa - slvrng*slvrng)/(2.*rng*aa)

                Bpar.append(aa*costheta)

                perp = aa * np.sqrt(1 - costheta*costheta)
                direction = np.sign(np.dot( np.cross(targxyz-mxyz, sxyz-mxyz), mvel))
                Bperp.append(direction*perp)    


                #catalog.addItem('IW-{0} Bpar at midrange for first common burst'.format(swath), Bpar[0], 'baseline')
                #catalog.addItem('IW-{0} Bperp at midrange for first common burst'.format(swath), Bperp[0], 'baseline')
                #catalog.addItem('IW-{0} Bpar at midrange for last common burst'.format(swath), Bpar[1], 'baseline')
                #catalog.addItem('IW-{0} Bperp at midrange for last common burst'.format(swath), Bperp[1], 'baseline')

            print('Bprep: ', Bperp)
            print('Bpar: ', Bpar)
            f.write('swath: IW{0}'.format(swath) + '\n')
            f.write('Bperp (average): ' + str(np.mean(Bperp))  + '\n')
            f.write('Bpar (average): ' + str(np.mean(Bpar))  + '\n')

    f.close()
        #else:
        #    print('Skipping processing for swath number IW-{0}'.format(swath))

            
    #self._insar.commonBurstStartReferenceIndex = commonBurstStartReferenceIndex 
    #self._insar.commonBurstStartSecondaryIndex = commonBurstStartSecondaryIndex   
    #self._insar.numberOfCommonBursts = numberOfCommonBursts


    #if not any([x>=2 for x in self._insar.numberOfCommonBursts]):
    #    print('No swaths contain any burst overlaps ... cannot continue for interferometry applications')

    #catalog.printToLog(logger, "runComputeBaseline")
    #self._insar.procDoc.addAllFromCatalog(catalog)

if __name__ == '__main__':
    '''
    Main driver.
    '''
    main()

