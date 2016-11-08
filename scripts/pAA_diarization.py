#!/usr/bin/python

import sys
import copy
import os
import argparse

pathToAdd = os.path.join(os.path.dirname(sys.argv[0]), "../../pyAudioAnalysis/")
sys.path.append(pathToAdd)

import audioSegmentation as aS

pathToAdd = os.path.join(os.path.dirname(sys.argv[0]), "../../recordsure/experiments/share/")
sys.path.append(pathToAdd)

from lsdpylib import lsdutils
from lsdpylib import phraselib
from lsdpylib import slicelib
import eval.scoreTopics as scoreTopics


def pAA_scores(fInRefName, cls, mtStep):

    _phrases = phraselib.readSERP(fInRefName)
    segStart = [ _p.start for _p in _phrases]
    segEnd = [ _p.end for _p in _phrases]
    segLabels = [ _p.speaker for _p in _phrases]

    flagsGT, classNamesGT = aS.segs2flags(segStart, segEnd, segLabels, mtStep)
    purityClusterMean, puritySpeakerMean = aS.evaluateSpeakerDiarization(cls, flagsGT)

    scores = {'purityClusterMean': purityClusterMean, 'puritySpeakerMean' : puritySpeakerMean}

    return scores


def ST_parse_args(parser, fInRefName, fInHypName, fOutDERName):

    parser.set_defaults(hyptype='diarization.json')
    parser.set_defaults(reftype='SERP.tsv')
    parser.set_defaults(mode='DER')
    parser.set_defaults(nophrasemod=False)
    parser.set_defaults(collar=0.0)
    parser.set_defaults(der_json_output=fOutDERName)
    parser.set_defaults(hyp=fInHypName)
    parser.set_defaults(ref=fInRefName)


    return parser.parse_args()


class Diarization():

    def __init__(self, pOut=None, mtStep=0.1, LDAdim=0, doPlot=False):

        self.pOut = pOut
        self.mtStep = mtStep
        self.LDAdim = LDAdim
        self.doPlot = doPlot
        self.numberOfSpeakers = {}

        self.DERs = {}
        self.CLRs = {}
        self.DIAs = {}
        self.pAAScores = {}

#        self._defaultsDERParser()


    def _defaultsDERParser(self, collar=0.0):

        self.DERParser = argparse.ArgumentParser()
        self.DERParser.set_defaults(hyptype='diarization.json')
        self.DERParser.set_defaults(reftype='SERP.tsv')
        self.DERParser.set_defaults(mode='DER')
        self.DERParser.set_defaults(nophrasemod=False)
        self.DERParser.set_defaults(collar=collar)

#        _a  = self.DERParser.parse_args()

    def updateDERParser(self, fInRefName, fName):

        parser = copy.copy(self.DERParser)
        parser.set_defaults(ref=fInRefName)
        parser.set_defaults(der_json_output=self.DERs[fName])
        parser.set_defaults(hyp=self.DIAs[fName])

        return parser

    def diarization(self, fInAudioName, numberOfSpeakers=0):

        fName = lsdutils.getFileBasename(fInAudioName)
        self.numberOfSpeakers[fName] = numberOfSpeakers

        if self.pOut is None:
            self.DIAs[fName] = None
            self.DERs[fName] = None

        else:
            self.DIAs[fName] = os.path.join(self.pOut, fName + ".diarization.json")
            self.DERs[fName] = os.path.join(self.pOut, fName + ".DER.json")


        self.CLRs[fName] = aS.speakerDiarization(fInAudioName, self.numberOfSpeakers[fName], mtStep=self.mtStep, LDAdim=self.LDAdim, PLOT=self.doPlot)
        _times, _speakers = aS.flags2segs(self.CLRs[fName], self.mtStep)
        slices = [ slicelib.Slice(start=_s, end=_e, label="S{}".format(int(_sp))) for (_s, _e), _sp in zip(_times, _speakers)]
        slicelib.writeJson(slices, self.DIAs[fName])

        return fName


    def scoring(self, fInRefName, fName, parser):

        self.pAAScores[fName] = pAA_scores(fInRefName, self.CLRs[fName], self.mtStep)
        print "Cluster purity: {0:.1f}% - Speaker purity: {1:.1f}%".format(100*self.pAAScores[fName]['purityClusterMean'], 100*self.pAAScores[fName]['puritySpeakerMean'])

        _p = ST_parse_args(parser, fInRefName, self.DIAs[fName], self.DERs[fName])
#        parser = self.updateDERParser(fInRefName, fName)
        scoreTopics.main(_p)


def main():


    parser = argparse.ArgumentParser(description='pyAudioAnalysis Diarization.')
    parser.add_argument('-a','--audio', help='Input audio file', default=None)
    parser.add_argument('--audio-list', help='Input audio file list', default=None)
    parser.add_argument('-o','--outdir', help='Output directory', required=True)
    parser.add_argument('-n','--speaker-number', help='Output directory', type=int, default=0)
    parser.add_argument("--lda", help="FLsD value", type=int, default=0)
    parser.add_argument('--ref', help='Reference file', default=None)
    parser.add_argument('--ref-list', help='Reference file', default=None)
    parser.add_argument("--plot", help="Plot", action="store_true", default=False)


    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    fInAudioName = args.audio

    fInAudioLstName = args.audio_list
    pOut = args.outdir
    numberOfSpeakers = args.speaker_number
    fInRefName = args.ref
    fInRefLstName = args.ref_list
    LDAdim = args.lda
    doPlot = args.plot

    mtStep = 0.1


    dia = Diarization(pOut=pOut, mtStep=mtStep, LDAdim=LDAdim, doPlot=doPlot)

    if fInAudioName is not None:
        fName = dia.diarization(fInAudioName)
        if fInRefName is not None:
            dia.scoring(fInRefName, fName)


    if fInAudioLstName is not None:
        audios = lsdutils.getFIlesFromList(fInAudioLstName)

        if fInRefLstName is not None:
            refs = lsdutils.getFIlesFromList(fInRefLstName)

        for k in audios:

            dia.diarization(audios[k])

            if refs and k in refs:
                dia.scoring(refs[k], k, parser)


if __name__ == "__main__":
    main()




















