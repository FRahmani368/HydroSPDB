import unittest

import torch

import definitions
from data import GagesConfig, GagesSource, DataModel
from data.data_input import save_datamodel, GagesModel, save_result
from data.gages_input_dataset import GagesExploreDataModel, GagesDamDataModel, choose_which_purpose
from data.nid_input import NidModel
from explore.stat import statError
from hydroDL.master.master import master_train, master_test
import numpy as np
import os
import pandas as pd

from utils import unserialize_json
from utils.dataset_format import subset_of_dict
from visual import plot_ts_obs_pred
from visual.plot_model import plot_boxes_inds, plot_ind_map


class MyTestCase(unittest.TestCase):
    """historical data assimilation"""

    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        # classify_datamodel according to dam purpose
        self.config_file = os.path.join(config_dir, "dam/config_exp7.ini")
        self.subdir = r"dam/exp7"
        self.config_data = GagesConfig.set_subdir(self.config_file, self.subdir)
        # self.nid_file = 'OH_U.xlsx'
        self.nid_file = 'NID2018_U.xlsx'

    def test_data_temp_damcls(self):
        quick_data_dir = os.path.join(self.config_data.data_path["DB"], "quickdata")
        data_dir = os.path.join(quick_data_dir, "allnonref_85-05_nan-0.1_00-1.0")
        data_model_train = GagesModel.load_datamodel(data_dir,
                                                     data_source_file_name='data_source.txt',
                                                     stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                     forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                     f_dict_file_name='dictFactorize.json',
                                                     var_dict_file_name='dictAttribute.json',
                                                     t_s_dict_file_name='dictTimeSpace.json')
        data_model_test = GagesModel.load_datamodel(data_dir,
                                                    data_source_file_name='test_data_source.txt',
                                                    stat_file_name='test_Statistics.json',
                                                    flow_file_name='test_flow.npy',
                                                    forcing_file_name='test_forcing.npy',
                                                    attr_file_name='test_attr.npy',
                                                    f_dict_file_name='test_dictFactorize.json',
                                                    var_dict_file_name='test_dictAttribute.json',
                                                    t_s_dict_file_name='test_dictTimeSpace.json')

        gages_model_train = GagesModel.update_data_model(self.config_data, data_model_train)
        gages_model_test = GagesModel.update_data_model(self.config_data, data_model_test,
                                                        train_stat_dict=gages_model_train.stat_dict)
        save_datamodel(gages_model_train, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(gages_model_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_explore_damcls_datamodel(self):
        df = GagesModel.load_datamodel(self.config_data.data_path["Temp"], data_source_file_name='data_source.txt',
                                       stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                       forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                       f_dict_file_name='dictFactorize.json',
                                       var_dict_file_name='dictAttribute.json',
                                       t_s_dict_file_name='dictTimeSpace.json')
        nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
        nid_input = NidModel.load_nidmodel(nid_dir, nid_file=self.nid_file,
                                           nid_source_file_name='nid_source.txt', nid_data_file_name='nid_data.shp')
        gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
        gage_main_dam_purpose_lst = list(gage_main_dam_purpose.values())
        gage_main_dam_purpose_unique = np.unique(gage_main_dam_purpose_lst)
        data_input = GagesDamDataModel(df, nid_input, True, gage_main_dam_purpose)
        for i in range(gage_main_dam_purpose_unique.size):
            gages_input = choose_which_purpose(data_input, purpose=gage_main_dam_purpose_unique[i])
            save_datamodel(gages_input, gage_main_dam_purpose_unique[i], data_source_file_name='data_source.txt',
                           stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                           attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                           var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')

    def test_dam_train(self):
        with torch.cuda.device(0):
            nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
            gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
            gage_main_dam_purpose_lst = list(gage_main_dam_purpose.values())
            gage_main_dam_purpose_unique = np.unique(gage_main_dam_purpose_lst)
            for i in range(9, gage_main_dam_purpose_unique.size):
                df = GagesModel.load_datamodel(self.config_data.data_path["Temp"], gage_main_dam_purpose_unique[i],
                                               data_source_file_name='data_source.txt',
                                               stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                               forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                               f_dict_file_name='dictFactorize.json',
                                               var_dict_file_name='dictAttribute.json',
                                               t_s_dict_file_name='dictTimeSpace.json')
                new_temp_dir = os.path.join(df.data_source.data_config.model_dict["dir"]["Temp"],
                                            gage_main_dam_purpose_unique[i])
                new_out_dir = os.path.join(df.data_source.data_config.model_dict["dir"]["Out"],
                                           gage_main_dam_purpose_unique[i])
                df.update_datamodel_dir(new_temp_dir, new_out_dir)
                master_train(df)

    def test_data_temp_test_damcls(self):
        df = GagesModel.load_datamodel(self.config_data.data_path["Temp"], data_source_file_name='test_data_source.txt',
                                       stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                       forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                       f_dict_file_name='test_dictFactorize.json',
                                       var_dict_file_name='test_dictAttribute.json',
                                       t_s_dict_file_name='test_dictTimeSpace.json')
        nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
        nid_input = NidModel.load_nidmodel(nid_dir, nid_file=self.nid_file,
                                           nid_source_file_name='nid_source.txt', nid_data_file_name='nid_data.shp')
        gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
        gage_main_dam_purpose_lst = list(gage_main_dam_purpose.values())
        gage_main_dam_purpose_unique = np.unique(gage_main_dam_purpose_lst)
        data_input = GagesDamDataModel(df, nid_input, True, gage_main_dam_purpose)
        for i in range(gage_main_dam_purpose_unique.size):
            gages_input = choose_which_purpose(data_input, purpose=gage_main_dam_purpose_unique[i])
            save_datamodel(gages_input, gage_main_dam_purpose_unique[i], data_source_file_name='test_data_source.txt',
                           stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                           forcing_file_name='test_forcing', attr_file_name='test_attr',
                           f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                           t_s_dict_file_name='test_dictTimeSpace.json')

    def test_damcls_test_datamodel(self):
        test_epoch = 300
        with torch.cuda.device(0):
            nid_dir = os.path.join("/".join(self.config_data.data_path["DB"].split("/")[:-1]), "nid", "quickdata")
            gage_main_dam_purpose = unserialize_json(os.path.join(nid_dir, "dam_main_purpose_dict.json"))
            gage_main_dam_purpose_lst = list(gage_main_dam_purpose.values())
            gage_main_dam_purpose_unique = np.unique(gage_main_dam_purpose_lst)
            for i in range(0, gage_main_dam_purpose_unique.size):
                df = GagesModel.load_datamodel(self.config_data.data_path["Temp"], gage_main_dam_purpose_unique[i],
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                                               forcing_file_name='test_forcing', attr_file_name='test_attr',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
                new_temp_dir = os.path.join(df.data_source.data_config.model_dict["dir"]["Temp"],
                                            gage_main_dam_purpose_unique[i])
                new_out_dir = os.path.join(df.data_source.data_config.model_dict["dir"]["Out"],
                                           gage_main_dam_purpose_unique[i])
                df.update_datamodel_dir(new_temp_dir, new_out_dir)
                pred, obs = master_test(df)
                save_result(new_out_dir, test_epoch, pred, obs)

    def test_damcls_test(self):
        models_num = 0
        dirs = os.listdir(self.config_data.data_path["Temp"])
        for dir_temp in dirs:
            if os.path.isdir(os.path.join(self.config_data.data_path["Temp"], dir_temp)):
                models_num += 1
        for count in range(models_num):
            self.test_a_case(count)

    def test_damcls_test_some_cases(self):
        models_num = [1, 2]
        for count in models_num:
            self.test_a_case(count)

    def test_a_case(self, count):
        print("\n", "testing model", str(count + 1), ":\n")
        data_model = GagesModel.load_datamodel(self.config_data.data_path["Temp"], str(count),
                                               data_source_file_name='test_data_source.txt',
                                               stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                               forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                               f_dict_file_name='test_dictFactorize.json',
                                               var_dict_file_name='test_dictAttribute.json',
                                               t_s_dict_file_name='test_dictTimeSpace.json')
        model_file = os.path.join(data_model.data_source.data_config.model_dict['dir']['Out'], 'model_Ep' + str(
            data_model.data_source.data_config.model_dict['train']['nEpoch']) + '.pt')
        if os.path.isfile(model_file):
            pred, obs = master_test(data_model)
            pred = pred.reshape(pred.shape[0], pred.shape[1])
            obs = obs.reshape(obs.shape[0], obs.shape[1])
            inds = statError(obs, pred)
            show_me_num = 1
            t_s_dict = data_model.t_s_dict
            sites = np.array(t_s_dict["sites_id"])
            t_range = np.array(t_s_dict["t_final_range"])
            ts_fig = plot_ts_obs_pred(obs, pred, sites, t_range, show_me_num)
            ts_fig.savefig(os.path.join(data_model.data_source.data_config.data_path["Out"], "ts_fig.png"))
            # # plot box，使用seaborn库
            keys = ["Bias", "RMSE", "NSE"]
            inds_test = subset_of_dict(inds, keys)
            box_fig = plot_boxes_inds(inds_test)
            box_fig.savefig(os.path.join(data_model.data_source.data_config.data_path["Out"], "box_fig.png"))
            # plot map
            sites_df = pd.DataFrame({"sites": sites, keys[2]: inds_test[keys[2]]})
            plot_ind_map(data_model.data_source.all_configs['gage_point_file'], sites_df)


if __name__ == '__main__':
    unittest.main()