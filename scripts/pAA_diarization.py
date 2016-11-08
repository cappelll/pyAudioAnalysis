#!/usr/bin/python

import sys
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


    return parser.parse_args()



def diarization(parser):

    args = parser.parse_args()

    fInAudioName = args.audio
    pOut = args.outdir
    numberOfSpeakers = args.speaker_number
    fInRefName = args.ref
    LDAdim = args.lda
    doPlot = args.plot

    mtStep = 0.1

    fName = lsdutils.getFileBasename(fInAudioName)

    if pOut is None:
        fOutDiarizationName = None
        fOutDERName = None

    else:
        fOutDiarizationName = os.path.join(pOut, fName + ".diarization.json")
        fOutDERName = os.path.join(pOut, fName + ".DER.json")


    cls = aS.speakerDiarization(fInAudioName, numberOfSpeakers, mtStep=mtStep, LDAdim=LDAdim, PLOT=doPlot)
    _times, _speakers = aS.flags2segs(cls, mtStep)
    slices = [ slicelib.Slice(start=_s, end=_e, label="S{}".format(int(_sp))) for (_s, _e), _sp in zip(_times, _speakers)]
    slicelib.writeJson(slices, fOutDiarizationName)

    if fInRefName:

        scores = pAA_scores(fInRefName, cls, mtStep)
        print "Cluster purity: {0:.1f}% - Speaker purity: {1:.1f}%".format(100*scores['purityClusterMean'], 100*scores['puritySpeakerMean'])

        args_ST = ST_parse_args(parser, fInRefName, fOutDiarizationName, fOutDERName)
        scoreTopics.main(args_ST)



def main():

    global parser
    parser = argparse.ArgumentParser(description='pyAudioAnalysis Diarization.')

    parser.add_argument('-a','--audio', help='Input audio file', required=True)
    parser.add_argument('-o','--outdir', help='Output directory', required=True)
    parser.add_argument('--ref', help='Reference file', default=None)
    parser.add_argument('-n','--speaker-number', help='Output directory', type=int, default=0)
    parser.add_argument("--lda", help="FLsD value", type=int, default=0)
    parser.add_argument("--plot", help="Plot", action="store_true", default=False)


    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    diarization(parser)


if __name__ == "__main__":
    main()


