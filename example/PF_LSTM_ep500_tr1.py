from hydroDL import master, utils
from hydroDL.data import dbCsv
from hydroDL.master import default, wrapMaster, run_train, test
from hydroDL.model import rnn, crit, train
from hydroDL.post import plot, stat

import os
import numpy as np
import pandas as pd
import statistics
import torch

cDir = os.path.dirname(os.path.abspath(__file__))
cDir = r'/mnt/sdc/SUR_VIC/'

rootDB = os.path.join(cDir, 'input_VIC')

df = dbCsv.DataframeCsv(
    rootDB=rootDB, subset='CONUS_VICv16f1', tRange=[20150401, 20160401]
    )

Forcing = df.getDataTs(dbCsv.varForcing, doNorm=True, rmNan=True)
Parameters = df.getDataConst(dbCsv.varConst, doNorm=True, rmNan=True)

Target = df.getDataTs(['SOILM_lev1_VIC'], doNorm=True, rmNan=True)

nx = Forcing.shape[-1] + Parameters.shape[-1]
ny = 1

path_PF = 'multiOutput_CONUSv16f1_VIC/CONUS_v16f1_SOILM_lev1_PF_LSTM'
outFolder = os.path.join(cDir, path_PF)
if os.path.exists(outFolder) is False:
   os.mkdir(outFolder)

epoch=500
model_PF = rnn.CudnnLstmModel(nx=nx, ny=ny, hiddenSize=256)
lossFun_PF = crit.RmseLoss()
model_PF = train.trainModel(
    model_PF, Forcing, Target, Parameters, lossFun_PF, nEpoch=epoch, miniBatch=[100, 60], saveFolder=outFolder)
modelName = 'PF_LSTM'

train.saveModel(outFolder, model_PF, epoch, modelName=modelName)

# test and obtain output
train.testModel(model_PF, Forcing, Parameters)