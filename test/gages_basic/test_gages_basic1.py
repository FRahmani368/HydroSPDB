import os
import unittest

import torch
from scipy import stats

from data import *
from data.data_input import save_datamodel, GagesModel, _basin_norm
from data.gages_input_dataset import GagesModels
from hydroDL.master import *
import definitions
from utils import serialize_numpy
from visual.plot_model import plot_we_need
import numpy as np
from matplotlib import pyplot


class MyTestCaseGages(unittest.TestCase):
    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        # self.config_file = os.path.join(config_dir, "basic/config_exp1.ini")
        # self.subdir = r"basic/exp1"
        # self.config_file = os.path.join(config_dir, "basic/config_exp2.ini")
        # self.subdir = r"basic/exp2"
        # self.config_file = os.path.join(config_dir, "basic/config_exp3.ini")
        # self.subdir = r"basic/exp3"
        # self.config_file = os.path.join(config_dir, "basic/config_exp4.ini")
        # self.subdir = r"basic/exp4"
        # self.config_file = os.path.join(config_dir, "basic/config_exp5.ini")
        # self.subdir = r"basic/exp5"
        # self.config_file = os.path.join(config_dir, "basic/config_exp6.ini")
        # self.subdir = r"basic/exp6"
        # self.config_file = os.path.join(config_dir, "basic/config_exp7.ini")
        # self.subdir = r"basic/exp7"
        # self.config_file = os.path.join(config_dir, "basic/config_exp8.ini")
        # self.subdir = r"basic/exp8"
        # self.config_file = os.path.join(config_dir, "basic/config_exp9.ini")
        # self.subdir = r"basic/exp9"
        # self.config_file = os.path.join(config_dir, "basic/config_exp10.ini")
        # self.subdir = r"basic/exp10"
        # self.config_file = os.path.join(config_dir, "basic/config_exp11.ini")
        # self.subdir = r"basic/exp11"
        self.config_file = os.path.join(config_dir, "basic/config_exp12.ini")
        self.subdir = r"basic/exp12"
        # self.config_file = os.path.join(config_dir, "basic/config_exp15.ini")
        # self.subdir = r"basic/exp15"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)

    def test_gages_data_model(self):
        gages_model = GagesModels(self.config_data)
        save_datamodel(gages_model.data_model_train, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model.data_model_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_train_gages(self):
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                               data_source_file_name='data_source.txt',
                                               stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                               forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                               f_dict_file_name='dictFactorize.json',
                                               var_dict_file_name='dictAttribute.json',
                                               t_s_dict_file_name='dictTimeSpace.json')
        with torch.cuda.device(2):
            master_train(data_model)

    def test_test_gages(self):
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        data_model_train = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                                     data_source_file_name='data_source.txt',
                                                     stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                     forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                     f_dict_file_name='dictFactorize.json',
                                                     var_dict_file_name='dictAttribute.json',
                                                     t_s_dict_file_name='dictTimeSpace.json')
        with torch.cuda.device(2):
            pred, obs = master_test(data_model, epoch=300)
            basin_area = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['DRAIN_SQKM'],
                                                          is_return_dict=False)
            mean_prep = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['PPTAVG_BASIN'],
                                                         is_return_dict=False)
            mean_prep = mean_prep / 365 * 10
            pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
            obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
            flow_pred_file = os.path.join(data_model.data_source.data_config.data_path['Temp'], 'flow_pred')
            flow_obs_file = os.path.join(data_model.data_source.data_config.data_path['Temp'], 'flow_obs')
            serialize_numpy(pred, flow_pred_file)
            serialize_numpy(obs, flow_obs_file)
            plot_we_need(data_model, obs, pred, id_col="STAID", lon_col="LNG_GAGE", lat_col="LAT_GAGE")

    def test_explore_gages_prcp_log(self):
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                               data_source_file_name='data_source.txt',
                                               stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                               forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                               f_dict_file_name='dictFactorize.json',
                                               var_dict_file_name='dictAttribute.json',
                                               t_s_dict_file_name='dictTimeSpace.json')
        i = np.random.randint(data_model.data_forcing.shape[0], size=1)
        print(i)
        a = data_model.data_forcing[i, :, 1].flatten()
        series = a[~np.isnan(a)]
        series = series[np.where(series >= 0)]
        # series = series[np.where(series > 0)]
        pyplot.plot(series)
        pyplot.show()
        # histogram
        pyplot.hist(series)
        pyplot.show()
        # sqrt transform
        transform = np.sqrt(series)
        pyplot.figure(1)
        # line plot
        pyplot.subplot(211)
        pyplot.plot(transform)
        # histogram
        pyplot.subplot(212)
        pyplot.hist(transform)
        pyplot.show()
        transform = np.log(series + 1)
        # transform = np.log(series + 0.1)
        pyplot.figure(1)
        # line plot
        pyplot.subplot(211)
        pyplot.plot(transform)
        # histogram
        pyplot.subplot(212)
        pyplot.hist(transform)
        pyplot.show()
        # transform = stats.boxcox(series, lmbda=0.0)
        # pyplot.figure(1)
        # # line plot
        # pyplot.subplot(211)
        # pyplot.plot(transform)
        # # histogram
        # pyplot.subplot(212)
        # pyplot.hist(transform)
        # pyplot.show()
        # for j in range(data_model.data_forcing.shape[2]):
        #     x_explore_j = data_model.data_forcing[i, :, j].flatten()
        #     plot_dist(x_explore_j)

    def test_explore_gages_prcp_basin(self):
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                               data_source_file_name='data_source.txt',
                                               stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                               forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                               f_dict_file_name='dictFactorize.json',
                                               var_dict_file_name='dictAttribute.json',
                                               t_s_dict_file_name='dictTimeSpace.json')
        basin_area = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['DRAIN_SQKM'],
                                                      is_return_dict=False)
        mean_prep = data_model.data_source.read_attr(data_model.t_s_dict["sites_id"], ['PPTAVG_BASIN'],
                                                     is_return_dict=False)
        flow = data_model.data_flow
        temparea = np.tile(basin_area, (1, flow.shape[1]))
        tempprep = np.tile(mean_prep / 365 * 10, (1, flow.shape[1]))
        flowua = (flow * 0.0283168 * 3600 * 24) / (
                (temparea * (10 ** 6)) * (tempprep * 10 ** (-3)))  # unit (m^3/day)/(m^3/day)
        i = np.random.randint(data_model.data_forcing.shape[0], size=1)
        a = flow[i].flatten()
        series = a[~np.isnan(a)]
        # series = series[np.where(series >= 0)]
        # series = series[np.where(series > 0)]
        pyplot.figure(1)
        # line plot
        pyplot.subplot(211)
        pyplot.plot(series)
        # histogram
        pyplot.subplot(212)
        pyplot.hist(series)
        pyplot.show()

        b = flowua[i].flatten()
        transform = b[~np.isnan(b)]
        # transform = series[np.where(transform >= 0)]
        # series = series[np.where(series > 0)]
        pyplot.figure(1)
        # line plot
        pyplot.subplot(211)
        pyplot.plot(transform)
        # histogram
        pyplot.subplot(212)
        pyplot.hist(transform)
        pyplot.show()


if __name__ == '__main__':
    unittest.main()
