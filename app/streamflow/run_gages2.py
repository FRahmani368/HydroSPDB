"""利用GAGES-II数据训练LSTM，进行流域径流模拟，先针对671个CAMELS的reference sites进行训练。
直接使用GAGES-II自己的attributes；
forcing数据利用maurur的数据源通过matlab code进行basin average计算。然后就可以组成输入集；
输出集直接使用GAGES-II的即可。
先和dapeng用CAMELS计算的结果比较，看看结果是否合理，如果合理，直接使用GAGES-II的数据继续接下来的人类活动影响的研究即可。"""

# 首先，配置GAGES-II原始数据文件的路径。在hydroDL的init文件里直接配置输入输出路径
import os

from hydroDL import pathGages2
# 接下来是初始的默认模型配置，这部分直接在master文件夹下的default模块中配置
from hydroDL import master
# 接下来配置计算条件
from hydroDL.master import default
from hydroDL.master.master import namePred
# 导入统计计算和绘图的包
from hydroDL.post import plot, stat
import matplotlib.pyplot as plt
import numpy as np
from hydroDL import utils

cid = 0
# train config
out = os.path.join(pathGages2['Out'], 'All-90-95')
optData = default.optDataGages2
optModel = default.optLstm
optLoss = default.optLossRMSE
optTrain = default.optTrainGages2
masterDict = master.wrapMaster(out, optData, optModel, optLoss, optTrain)

# test config
caseLst = ['All-90-95']
outLst = [os.path.join(pathGages2['Out'], x) for x in caseLst]
subset = 'All'
tRangeTest = [19950101, 20000101]
predLst = list()

# train model
# see whether there are previous results or not, if yes, there is no need to train again.
resultPathLst = namePred(out, tRangeTest, subset, epoch=optTrain['nEpoch'])
if not os.path.exists(resultPathLst[0]):
    master.run_train(masterDict, cuda_id=cid % 3, screen='test')
    cid = cid + 1

# test
for out in outLst:
    df, pred, obs = master.test(out, t_range=tRangeTest, subset=subset)
    predLst.append(pred)

# plot box
statDictLst = [stat.statError(x.squeeze(), obs.squeeze()) for x in predLst]
keyLst = list(statDictLst[0].keys())
dataBox = list()
for iS in range(len(keyLst)):
    statStr = keyLst[iS]
    temp = list()
    for k in range(len(statDictLst)):
        data = statDictLst[k][statStr]
        data = data[~np.isnan(data)]
        temp.append(data)
    dataBox.append(temp)
fig = plot.plotBoxFig(dataBox, keyLst, ['LSTM'], sharey=False)
fig.show()

# plot time series
t = utils.time.tRange2Array(tRangeTest)
fig, axes = plt.subplots(5, 1, figsize=(12, 8))
for k in range(5):
    iGrid = np.random.randint(0, 671)
    yPlot = [obs[iGrid, :]]
    for y in predLst:
        yPlot.append(y[iGrid, :])
    if k == 0:
        plot.plotTS(
            t,
            yPlot,
            ax=axes[k],
            cLst='kbrg',
            markerLst='----',
            legLst=['USGS', 'LSTM'])
    else:
        plot.plotTS(t, yPlot, ax=axes[k], cLst='kbrg', markerLst='----')
fig.show()
