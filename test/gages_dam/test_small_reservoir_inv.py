import os
import unittest
import numpy as np
import torch

import definitions
from data import GagesConfig, GagesSource
from data.data_config import add_model_param
from data.data_input import save_datamodel, GagesModel, _basin_norm
from data.gages_input_dataset import GagesInvDataModel
import pandas as pd

from explore.stat import statError
from hydroDL.master.master import train_lstm_inv, test_lstm_inv
from utils import unserialize_numpy, serialize_numpy
from utils.dataset_format import subset_of_dict
from visual import plot_ts_obs_pred
from visual.plot_model import plot_map
from visual.plot_stat import plot_ecdf, plot_diff_boxes


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """choose basins with small DOR """
        config_dir = definitions.CONFIG_DIR
        self.config_file_1 = os.path.join(config_dir, "dam/config1_exp3.ini")
        self.config_file_2 = os.path.join(config_dir, "dam/config2_exp3.ini")
        self.subdir = r"dam/exp3"
        self.config_data_1 = GagesConfig.set_subdir(self.config_file_1, self.subdir)
        self.config_data_2 = GagesConfig.set_subdir(self.config_file_2, self.subdir)
        add_model_param(self.config_data_1, "model", seqLength=1)
        # choose some small basins, unit: SQKM
        # self.basin_area_screen = 100
        test_epoch_lst = [100, 200, 220, 250, 280, 290, 295, 300, 305, 310, 320, 400, 500]
        # self.test_epoch = test_epoch_lst[0]
        # self.test_epoch = test_epoch_lst[1]
        # self.test_epoch = test_epoch_lst[2]
        # self.test_epoch = test_epoch_lst[3]
        # self.test_epoch = test_epoch_lst[4]
        # self.test_epoch = test_epoch_lst[5]
        # self.test_epoch = test_epoch_lst[6]
        self.test_epoch = test_epoch_lst[7]
        # self.test_epoch = test_epoch_lst[8]
        # self.test_epoch = test_epoch_lst[9]
        # self.test_epoch = test_epoch_lst[10]
        # self.test_epoch = test_epoch_lst[11]
        # self.test_epoch = test_epoch_lst[12]

    def test_some_reservoirs(self):
        """choose some small reservoirs randomly to train and test"""
        # ????????????????????????
        config_data = self.config_data_1
        # according to paper "High-resolution mapping of the world's reservoirs and dams for sustainable river-flow management"
        dor = -0.02
        source_data = GagesSource.choose_some_basins(config_data, config_data.model_dict["data"]["tRangeTrain"],
                                                     DOR=dor)
        sites_id = source_data.all_configs['flow_screen_gage_id']

        # data1 is historical data as input of LSTM-Inv, which will be a kernel for the second LSTM
        quick_data_dir = os.path.join(self.config_data_1.data_path["DB"], "quickdata")
        data_dir = os.path.join(quick_data_dir, "allnonref_85-05_nan-0.1_00-1.0")
        # for inv model, datamodel of  train and test are same
        data_model_8595 = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='data_source.txt',
                                                    stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                    forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                    f_dict_file_name='dictFactorize.json',
                                                    var_dict_file_name='dictAttribute.json',
                                                    t_s_dict_file_name='dictTimeSpace.json')
        # for 2nd model, datamodel of train and test belong to parts of the test time
        data_model_9505 = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='test_data_source.txt',
                                                    stat_file_name='test_Statistics.json',
                                                    flow_file_name='test_flow.npy',
                                                    forcing_file_name='test_forcing.npy',
                                                    attr_file_name='test_attr.npy',
                                                    f_dict_file_name='test_dictFactorize.json',
                                                    var_dict_file_name='test_dictAttribute.json',
                                                    t_s_dict_file_name='test_dictTimeSpace.json')

        t_range1_train = self.config_data_1.model_dict["data"]["tRangeTrain"]
        t_range1_test = self.config_data_1.model_dict["data"]["tRangeTest"]
        gages_model1_train = GagesModel.update_data_model(self.config_data_1, data_model_8595, sites_id_update=sites_id,
                                                          t_range_update=t_range1_train, data_attr_update=True)
        # Because we know data of period "90-95", so that we can get its statistics according to this period
        gages_model1_test = GagesModel.update_data_model(self.config_data_1, data_model_8595, sites_id_update=sites_id,
                                                         t_range_update=t_range1_test, data_attr_update=True)
        t_range2_train = self.config_data_2.model_dict["data"]["tRangeTrain"]
        t_range2_test = self.config_data_2.model_dict["data"]["tRangeTest"]
        gages_model2_train = GagesModel.update_data_model(self.config_data_2, data_model_8595, sites_id_update=sites_id,
                                                          t_range_update=t_range2_train, data_attr_update=True)
        gages_model2_test = GagesModel.update_data_model(self.config_data_2, data_model_9505, sites_id_update=sites_id,
                                                         t_range_update=t_range2_test, data_attr_update=True,
                                                         train_stat_dict=gages_model2_train.stat_dict)
        save_datamodel(gages_model1_train, "1", data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model1_test, "1", data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        save_datamodel(gages_model2_train, "2", data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model2_test, "2", data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_inv_train(self):
        with torch.cuda.device(0):
            df1 = GagesModel.load_datamodel(self.config_data_1.data_path["Temp"], "1",
                                            data_source_file_name='data_source.txt',
                                            stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                            forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                            f_dict_file_name='dictFactorize.json',
                                            var_dict_file_name='dictAttribute.json',
                                            t_s_dict_file_name='dictTimeSpace.json')
            df2 = GagesModel.load_datamodel(self.config_data_2.data_path["Temp"], "2",
                                            data_source_file_name='data_source.txt',
                                            stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                            forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                            f_dict_file_name='dictFactorize.json',
                                            var_dict_file_name='dictAttribute.json',
                                            t_s_dict_file_name='dictTimeSpace.json')
            data_model = GagesInvDataModel(df1, df2)
            # pre_trained_model_epoch = 285
            train_lstm_inv(data_model)
            # train_lstm_inv(data_model, pre_trained_model_epoch=pre_trained_model_epoch)

    def test_inv_test(self):
        with torch.cuda.device(0):
            df1 = GagesModel.load_datamodel(self.config_data_1.data_path["Temp"], "1",
                                            data_source_file_name='test_data_source.txt',
                                            stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                            forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                            f_dict_file_name='test_dictFactorize.json',
                                            var_dict_file_name='test_dictAttribute.json',
                                            t_s_dict_file_name='test_dictTimeSpace.json')
            df2 = GagesModel.load_datamodel(self.config_data_2.data_path["Temp"], "2",
                                            data_source_file_name='test_data_source.txt',
                                            stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                            forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                            f_dict_file_name='test_dictFactorize.json',
                                            var_dict_file_name='test_dictAttribute.json',
                                            t_s_dict_file_name='test_dictTimeSpace.json')
            data_model = GagesInvDataModel(df1, df2)
            pred, obs = test_lstm_inv(data_model, epoch=self.test_epoch)
            basin_area = df2.data_source.read_attr(df2.t_s_dict["sites_id"], ['DRAIN_SQKM'], is_return_dict=False)
            mean_prep = df2.data_source.read_attr(df2.t_s_dict["sites_id"], ['PPTAVG_BASIN'], is_return_dict=False)
            mean_prep = mean_prep / 365 * 10
            pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
            obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
            flow_pred_file = os.path.join(df2.data_source.data_config.data_path['Temp'],
                                          'epoch' + str(self.test_epoch) + 'flow_pred')
            flow_obs_file = os.path.join(df2.data_source.data_config.data_path['Temp'],
                                         'epoch' + str(self.test_epoch) + 'flow_obs')
            serialize_numpy(pred, flow_pred_file)
            serialize_numpy(obs, flow_obs_file)

    def test_inv_plot(self):
        data_model = GagesModel.load_datamodel(self.config_data_2.data_path["Temp"], "2",
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        flow_pred_file = os.path.join(data_model.data_source.data_config.data_path['Temp'],
                                      'epoch' + str(self.test_epoch) + 'flow_pred.npy')
        flow_obs_file = os.path.join(data_model.data_source.data_config.data_path['Temp'],
                                     'epoch' + str(self.test_epoch) + 'flow_obs.npy')
        pred = unserialize_numpy(flow_pred_file)
        obs = unserialize_numpy(flow_obs_file)
        pred = pred.reshape(pred.shape[0], pred.shape[1])
        obs = obs.reshape(obs.shape[0], obs.shape[1])
        inds = statError(obs, pred)
        inds['STAID'] = data_model.t_s_dict["sites_id"]
        inds_df = pd.DataFrame(inds)
        inds_df.to_csv(os.path.join(self.config_data_2.data_path["Out"], 'data_df.csv'))
        # plot box?????????seaborn???
        keys = ["Bias", "RMSE", "NSE"]
        inds_test = subset_of_dict(inds, keys)
        box_fig = plot_diff_boxes(inds_test)
        box_fig.savefig(os.path.join(self.config_data_2.data_path["Out"], "box_fig.png"))
        # plot ts
        show_me_num = 5
        t_s_dict = data_model.t_s_dict
        sites = np.array(t_s_dict["sites_id"])
        t_range = np.array(t_s_dict["t_final_range"])
        time_seq_length = self.config_data_1.model_dict['model']['seqLength']
        time_start = np.datetime64(t_range[0]) + np.timedelta64(time_seq_length - 1, 'D')
        t_range[0] = np.datetime_as_string(time_start, unit='D')
        ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
        ts_fig.savefig(os.path.join(self.config_data_2.data_path["Out"], "ts_fig.png"))

        # plot nse ecdf
        sites_df_nse = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
        plot_ecdf(sites_df_nse, keys[2])
        # plot map
        gauge_dict = data_model.data_source.gage_dict
        plot_map(gauge_dict, sites_df_nse, id_col="STAID", lon_col="LNG_GAGE", lat_col="LAT_GAGE")


if __name__ == '__main__':
    unittest.main()
