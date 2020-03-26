import os
import unittest

import torch

import definitions
from data import CamelsConfig
from data.data_input import save_datamodel, CamelsModel, _basin_norm
from data.camels_input_dataset import CamelsModels
from hydroDL.master.master import master_train, master_test, master_train_1by1, master_test_1by1
from visual.plot_model import plot_we_need
import numpy as np

from visual.plot_stat import plot_loss_early_stop


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """before all of these, natural flow model need to be generated by config.ini of gages dataset, and it need
        to be moved to right dir manually """
        config_dir = definitions.CONFIG_DIR
        # self.config_file = os.path.join(config_dir, "camels1by1/config_exp1.ini")
        # self.subdir = r"camels1by1/exp1"
        self.config_file = os.path.join(config_dir, "camels1by1/config_exp2.ini")
        self.subdir = r"camels1by1/exp2"
        self.config_data = CamelsConfig.set_subdir(self.config_file, self.subdir)

    def test_camels_data_model(self):
        camels_model = CamelsModels(self.config_data)
        save_datamodel(camels_model.data_model_train, data_source_file_name='data_source.txt',
                       stat_file_name='Statistics.json', flow_file_name='flow', forcing_file_name='forcing',
                       attr_file_name='attr', f_dict_file_name='dictFactorize.json',
                       var_dict_file_name='dictAttribute.json', t_s_dict_file_name='dictTimeSpace.json')
        save_datamodel(camels_model.data_model_test, data_source_file_name='test_data_source.txt',
                       stat_file_name='test_Statistics.json', flow_file_name='test_flow',
                       forcing_file_name='test_forcing', attr_file_name='test_attr',
                       f_dict_file_name='test_dictFactorize.json', var_dict_file_name='test_dictAttribute.json',
                       t_s_dict_file_name='test_dictTimeSpace.json')
        print("read and save data model")

    def test_train_camels(self):
        data_model = CamelsModel.load_datamodel(self.config_data.data_path["Temp"],
                                                data_source_file_name='data_source.txt',
                                                stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                f_dict_file_name='dictFactorize.json',
                                                var_dict_file_name='dictAttribute.json',
                                                t_s_dict_file_name='dictTimeSpace.json')
        with torch.cuda.device(1):
            data_models = CamelsModel.every_model(data_model)
            for i in range(len(data_models)):
                print("\n", "Training model", str(i + 1), ":\n")
                model, train_loss, valid_loss = master_train(data_models[i], valid_size=0.2)
                fig = plot_loss_early_stop(train_loss, valid_loss)
                out_dir = self.config_data.data_path["Out"]
                fig.savefig(os.path.join(out_dir, 'loss_plot.png'), bbox_inches='tight')

    def test_train_camels_iter(self):
        data_model = CamelsModel.load_datamodel(self.config_data.data_path["Temp"],
                                                data_source_file_name='data_source.txt',
                                                stat_file_name='Statistics.json', flow_file_name='flow.npy',
                                                forcing_file_name='forcing.npy', attr_file_name='attr.npy',
                                                f_dict_file_name='dictFactorize.json',
                                                var_dict_file_name='dictAttribute.json',
                                                t_s_dict_file_name='dictTimeSpace.json')
        valid_size = 0.2
        with torch.cuda.device(1):
            data_models = CamelsModel.every_model(data_model)
            for i in range(98, len(data_models)):
                print("\n", "Training model", str(i + 1), ":\n")
                model, train_loss, valid_loss = master_train_1by1(data_models[i], valid_size=valid_size)
                fig = plot_loss_early_stop(train_loss, valid_loss)
                out_dir = data_models[i].data_source.data_config.data_path["Out"]
                fig.savefig(os.path.join(out_dir, 'loss_plot.png'), bbox_inches='tight')

    def test_test_camels_iter(self):
        data_model = CamelsModel.load_datamodel(self.config_data.data_path["Temp"],
                                                data_source_file_name='test_data_source.txt',
                                                stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                                forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                                f_dict_file_name='test_dictFactorize.json',
                                                var_dict_file_name='test_dictAttribute.json',
                                                t_s_dict_file_name='test_dictTimeSpace.json')
        with torch.cuda.device(1):
            data_models = CamelsModel.every_model(data_model)
            obs_lst = []
            pred_lst = []
            for i in range(len(data_models)):
                print("\n", "Testing model", str(i + 1), ":\n")
                pred, obs = master_test_1by1(data_models[i])
                obs_lst.append(obs.flatten())
                pred_lst.append(pred.flatten())
            preds = np.array(pred_lst)
            obss = np.array(obs_lst)
            plot_we_need(data_model, obss, preds, id_col="id", lon_col="lon", lat_col="lat")

    def test_test_camels(self):
        data_model = CamelsModel.load_datamodel(self.config_data.data_path["Temp"],
                                                data_source_file_name='test_data_source.txt',
                                                stat_file_name='test_Statistics.json', flow_file_name='test_flow.npy',
                                                forcing_file_name='test_forcing.npy', attr_file_name='test_attr.npy',
                                                f_dict_file_name='test_dictFactorize.json',
                                                var_dict_file_name='test_dictAttribute.json',
                                                t_s_dict_file_name='test_dictTimeSpace.json')
        with torch.cuda.device(1):
            data_models = CamelsModel.every_model(data_model)
            obs_lst = []
            pred_lst = []
            for i in range(len(data_models)):
                print("\n", "Testing model", str(i + 1), ":\n")
                pred, obs = master_test(data_models[i])
                basin_area = data_models[i].data_source.read_attr(data_models[i].t_s_dict["sites_id"], ['area_gages2'],
                                                                  is_return_dict=False)
                mean_prep = data_models[i].data_source.read_attr(data_models[i].t_s_dict["sites_id"], ['p_mean'],
                                                                 is_return_dict=False)
                pred = _basin_norm(pred, basin_area, mean_prep, to_norm=False)
                obs = _basin_norm(obs, basin_area, mean_prep, to_norm=False)
                obs_lst.append(obs.flatten())
                pred_lst.append(pred.flatten())
            preds = np.array(pred_lst)
            obss = np.array(obs_lst)
            plot_we_need(data_model, obss, preds, id_col="id", lon_col="lon", lat_col="lat")


if __name__ == '__main__':
    unittest.main()
