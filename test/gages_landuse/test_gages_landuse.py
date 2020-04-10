import os
import unittest
import pandas as pd
import torch

from data import *
from data.data_input import save_datamodel, GagesModel, _basin_norm
from data.gages_input_dataset import GagesModels
from explore.stat import statError
from hydroDL.master import *
from utils import serialize_numpy
from utils.dataset_format import subset_of_dict
from visual import *
import numpy as np
import definitions
from visual.plot_model import plot_boxes_inds, plot_we_need


class MyTestCaseGagesNonref(unittest.TestCase):
    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        # self.config_file = os.path.join(config_dir, "landuse/config_exp1.ini")
        # self.subdir = r"landuse/exp1"
        self.config_file = os.path.join(config_dir, "landuse/config_exp2.ini")
        self.subdir = r"landuse/exp2"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        # ashu_gageid_file = os.path.join(self.config_data.data_path["DB"], "ashu", "AshuGagesId.txt")
        ashu_gageid_file = os.path.join(self.config_data.data_path["DB"], "ashu", "AshuGagesId.xlsx")
        gauge_df = pd.read_excel(ashu_gageid_file, dtype={"STAID": str})
        gauge_list_tmp = gauge_df["STAID"].values
        self.gauge_list = [str_tmp.zfill(8) for str_tmp in gauge_list_tmp]
        test_epoch_lst = [100, 200, 220, 250, 280, 290, 295, 300, 305, 310, 320, 400]
        # self.test_epoch = test_epoch_lst[0]
        # self.test_epoch = test_epoch_lst[1]
        # self.test_epoch = test_epoch_lst[2]
        # self.test_epoch = test_epoch_lst[3]
        # self.test_epoch = test_epoch_lst[4]
        # self.test_epoch = test_epoch_lst[5]
        # self.test_epoch = test_epoch_lst[6]
        # self.test_epoch = test_epoch_lst[7]
        # self.test_epoch = test_epoch_lst[8]
        # self.test_epoch = test_epoch_lst[9]
        # self.test_epoch = test_epoch_lst[10]
        self.test_epoch = test_epoch_lst[11]

    def test_gages_data_model(self):
        gages_model = GagesModels(self.config_data, sites_id=self.gauge_list)
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
        with torch.cuda.device(1):
            pre_trained_model_epoch = 285
            master_train(data_model)
            # master_train(data_model, pre_trained_model_epoch=pre_trained_model_epoch)

    def test_test_gages(self):
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        with torch.cuda.device(1):
            pred, obs = master_test(data_model, epoch=self.test_epoch)
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


if __name__ == '__main__':
    unittest.main()
