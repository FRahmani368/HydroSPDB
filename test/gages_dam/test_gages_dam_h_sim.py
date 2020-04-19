import unittest

import torch

import definitions
from data import GagesConfig, GagesSource, DataModel
from data.data_config import add_model_param
from data.data_input import save_datamodel, GagesModel
from data.gages_input_dataset import GagesDamDataModel, GagesModels, GagesSimDataModel
from data.nid_input import NidModel, save_nidinput
from explore.stat import statError
from hydroDL.master.master import master_train, master_test, master_train_natural_flow
import numpy as np
import os
import pandas as pd

from utils import serialize_json, unserialize_json
from utils.dataset_format import subset_of_dict
from visual import plot_ts_obs_pred
from visual.plot_model import plot_boxes_inds, plot_ind_map


class MyTestCase(unittest.TestCase):
    """historical data assimilation"""

    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        self.sim_config_file = os.path.join(config_dir, "dam/config1_exp14.ini")
        self.config_file = os.path.join(config_dir, "dam/config2_exp14.ini")
        self.subdir = "dam/exp14"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        self.sim_config_data = GagesConfig.set_subdir(self.sim_config_file, self.subdir)
        add_model_param(self.config_data, "model", seqLength=1)
        # self.nid_file = 'PA_U.xlsx'
        # self.nid_file = 'OH_U.xlsx'
        self.nid_file = 'NID2018_U.xlsx'

    def test_data_temp_dam(self):
        quick_data_dir = os.path.join(self.config_data.data_path["DB"], "quickdata")
        sim_data_dir = os.path.join(quick_data_dir, "allref_85-05_nan-0.1_00-1.0")
        data_dir = os.path.join(quick_data_dir, "allnonref_85-05_nan-0.1_00-1.0")
        data_model_sim8595 = GagesModel.load_datamodel(sim_data_dir,
                                                       data_source_file_name='data_source.txt',
                                                       stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                       forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                       f_dict_file_name='dictFactorize.json',
                                                       var_dict_file_name='dictAttribute.json',
                                                       t_s_dict_file_name='dictTimeSpace.json')
        data_model_8595 = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='data_source.txt',
                                                    stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                    forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                    f_dict_file_name='dictFactorize.json',
                                                    var_dict_file_name='dictAttribute.json',
                                                    t_s_dict_file_name='dictTimeSpace.json')
        data_model_sim9505 = GagesModel.load_datamodel(sim_data_dir,
                                                       data_source_file_name='test_data_source.txt',
                                                       stat_file_name='test_Statistics.json',
                                                       flow_file_name='test_flow.npy',
                                                       forcing_file_name='test_forcing.npy',
                                                       attr_file_name='test_attr.npy',
                                                       f_dict_file_name='test_dictFactorize.json',
                                                       var_dict_file_name='test_dictAttribute.json',
                                                       t_s_dict_file_name='test_dictTimeSpace.json')
        data_model_9505 = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='test_data_source.txt',
                                                    stat_file_name='test_Statistics.json',
                                                    flow_file_name='test_flow.npy',
                                                    forcing_file_name='test_forcing.npy',
                                                    attr_file_name='test_attr.npy',
                                                    f_dict_file_name='test_dictFactorize.json',
                                                    var_dict_file_name='test_dictAttribute.json',
                                                    t_s_dict_file_name='test_dictTimeSpace.json')

        sim_gages_model_train = GagesModel.update_data_model(self.sim_config_data, data_model_sim8595,
                                                             data_attr_update=True)
        gages_model_train = GagesModel.update_data_model(self.config_data, data_model_8595, data_attr_update=True)
        sim_gages_model_test = GagesModel.update_data_model(self.sim_config_data, data_model_sim9505,
                                                            data_attr_update=True,
                                                            train_stat_dict=sim_gages_model_train.stat_dict)
        gages_model_test = GagesModel.update_data_model(self.config_data, data_model_9505, data_attr_update=True,
                                                        train_stat_dict=gages_model_train.stat_dict)
        save_datamodel(sim_gages_model_train, "1", data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(sim_gages_model_test, "1", data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        save_datamodel(gages_model_train, "2", data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model_test, "2", data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_dam_train(self):
        with torch.cuda.device(0):
            data_model1 = GagesModel.load_datamodel(self.config_data.data_path["Temp"], "1",
                                                    data_source_file_name='data_source.txt',
                                                    stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                    forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                    f_dict_file_name='dictFactorize.json',
                                                    var_dict_file_name='dictAttribute.json',
                                                    t_s_dict_file_name='dictTimeSpace.json')
            data_model1.update_model_param('train', nEpoch=300)
            df = GagesModel.load_datamodel(self.config_data.data_path["Temp"], "2",
                                           data_source_file_name='data_source.txt',
                                           stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                           forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                           f_dict_file_name='dictFactorize.json',
                                           var_dict_file_name='dictAttribute.json',
                                           t_s_dict_file_name='dictTimeSpace.json')
            nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
            nid_input = NidModel.load_nidmodel(nid_dir, nid_file=self.nid_file,
                                               nid_source_file_name='nid_source.txt', nid_data_file_name='nid_data.shp')
            gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
            data_input = GagesDamDataModel(df, nid_input, True, gage_main_dam_purpose)
            purpose_chosen = 'H'
            data_input.choose_which_purpose(purpose=purpose_chosen)
            data_model = GagesSimDataModel(data_model1, data_input.gages_input)
            # pre_trained_model_epoch = 25
            # master_train_natural_flow(data_model, pre_trained_model_epoch=pre_trained_model_epoch)
            master_train_natural_flow(data_model)

    def test_data_temp_test_dam(self):
        config_data_test = self.config_data
        source_data_test = GagesSource(config_data_test, config_data_test.model_dict["data"]["tRangeTest"])
        df_test = DataModel(source_data_test)
        save_datamodel(df_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')

    def test_dam_test(self):
        df_test = GagesModel.load_datamodel(self.config_data.data_path["Temp"],
                                            data_source_file_name='test_data_source.txt',
                                            stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                            forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                            f_dict_file_name='test_dictFactorize.json',
                                            var_dict_file_name='test_dictAttribute.json',
                                            t_s_dict_file_name='test_dictTimeSpace.json')
        nid_input = NidModel()
        # nid_input = NidModel(self.nid_file)
        data_input_test = GagesDamDataModel(df_test, nid_input)
        pred, obs = master_test(data_input_test.gages_input)
        pred = pred.reshape(pred.shape[0], pred.shape[1])
        obs = obs.reshape(obs.shape[0], obs.shape[1])
        inds = statError(obs, pred)
        show_me_num = 5
        t_s_dict = data_input_test.gages_input.t_s_dict
        sites = np.array(t_s_dict["sites_id"])
        t_range = np.array(t_s_dict["t_final_range"])
        ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
        ts_fig.savefig(os.path.join(data_input_test.gages_input.data_source.data_config.data_path["Out"], "ts_fig.png"))
        # # plot box，使用seaborn库
        keys = ["Bias", "RMSE", "NSE"]
        inds_test = subset_of_dict(inds, keys)
        box_fig = plot_boxes_inds(inds_test)
        box_fig.savefig(
            os.path.join(data_input_test.gages_input.data_source.data_config.data_path["Out"], "box_fig.png"))
        # plot map
        sites_df = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
        plot_ind_map(data_input_test.gages_input.data_source.all_configs['gage_point_file'], sites_df)


if __name__ == '__main__':
    unittest.main()
