__author__ = 'sibirrer'

import pytest
import numpy.testing as npt
from lenstronomy.SimulationAPI.simulations import Simulation
from lenstronomy.ImSim.image_model import ImageModel
from lenstronomy.PointSource.point_source import PointSource
from lenstronomy.LensModel.lens_model import LensModel
from lenstronomy.LightModel.light_model import LightModel
from lenstronomy.Workflow.fitting_sequence_new import FittingSequence
from lenstronomy.Data.imaging_data import Data
from lenstronomy.Data.psf import PSF


class TestFittingSequence(object):
    """
    test the fitting sequences
    """

    def setup(self):
        self.SimAPI = Simulation()

        # data specifics
        sigma_bkg = 0.05  # background noise per pixel
        exp_time = 100  # exposure time (arbitrary units, flux per pixel is in units #photons/exp_time unit)
        numPix = 50  # cutout pixel size
        deltaPix = 0.1  # pixel size in arcsec (area per pixel = deltaPix**2)
        fwhm = 0.5  # full width half max of PSF

        # PSF specification

        self.kwargs_data = self.SimAPI.data_configure(numPix, deltaPix, exp_time, sigma_bkg)
        data_class = Data(self.kwargs_data)
        kwargs_psf = self.SimAPI.psf_configure(psf_type='GAUSSIAN', fwhm=fwhm, kernelsize=11, deltaPix=deltaPix,
                                               truncate=3,
                                               kernel=None)
        self.kwargs_psf = self.SimAPI.psf_configure(psf_type='PIXEL', fwhm=fwhm, kernelsize=11, deltaPix=deltaPix,
                                                    truncate=6,
                                                    kernel=kwargs_psf['kernel_point_source'])
        psf_class = PSF(self.kwargs_psf)

        # 'EXERNAL_SHEAR': external shear
        kwargs_shear = {'e1': 0.01, 'e2': 0.01}  # gamma_ext: shear strength, psi_ext: shear angel (in radian)
        kwargs_spemd = {'theta_E': 1., 'gamma': 1.8, 'center_x': 0, 'center_y': 0, 'e1': 0.1, 'e2': 0.1}

        lens_model_list = ['SPEP', 'SHEAR']
        self.kwargs_lens = [kwargs_spemd, kwargs_shear]
        lens_model_class = LensModel(lens_model_list=lens_model_list)
        kwargs_sersic = {'amp': 1., 'R_sersic': 0.1, 'n_sersic': 2, 'center_x': 0, 'center_y': 0}
        # 'SERSIC_ELLIPSE': elliptical Sersic profile
        kwargs_sersic_ellipse = {'amp': 1., 'R_sersic': .6, 'n_sersic': 3, 'center_x': 0, 'center_y': 0,
                                 'e1': 0.1, 'e2': 0.1}

        lens_light_model_list = ['SERSIC']
        self.kwargs_lens_light = [kwargs_sersic]
        lens_light_model_class = LightModel(light_model_list=lens_light_model_list)
        source_model_list = ['SERSIC_ELLIPSE']
        self.kwargs_source = [kwargs_sersic_ellipse]
        source_model_class = LightModel(light_model_list=source_model_list)
        self.kwargs_ps = [{'ra_source': 0.0, 'dec_source': 0.0,
                           'source_amp': 1.}]  # quasar point source position in the source plane and intrinsic brightness
        point_source_list = ['SOURCE_POSITION']
        point_source_class = PointSource(point_source_type_list=point_source_list, fixed_magnification_list=[True])
        kwargs_numerics = {'subgrid_res': 1, 'psf_subgrid': False}
        imageModel = ImageModel(data_class, psf_class, lens_model_class, source_model_class,
                                lens_light_model_class,
                                point_source_class, kwargs_numerics=kwargs_numerics)
        image_sim = self.SimAPI.simulate(imageModel, self.kwargs_lens, self.kwargs_source,
                                         self.kwargs_lens_light, self.kwargs_ps)

        data_class.update_data(image_sim)
        self.data_class = data_class
        self.psf_class = psf_class
        self.kwargs_data['image_data'] = image_sim
        self.kwargs_model = {'lens_model_list': lens_model_list,
                             'source_light_model_list': source_model_list,
                             'lens_light_model_list': lens_light_model_list,
                             'point_source_model_list': point_source_list,
                             'fixed_magnification_list': [False],
                             }
        self.kwargs_numerics = {
            'subgrid_res': 1,
            'psf_subgrid': False}

        num_source_model = len(source_model_list)

        self.kwargs_constraints = {'joint_center_lens_light': False,
                                   'joint_center_source_light': False,
                                   'num_point_source_list': [4],
                                   'additional_images_list': [False],
                                   'fix_to_point_source_list': [False] * num_source_model,
                                   'image_plane_source_list': [False] * num_source_model,
                                   'solver_type': 'NONE',  # 'PROFILE', 'PROFILE_SHEAR', 'ELLIPSE', 'CENTER'
                                   }

        self.kwargs_likelihood = {'force_no_add_image': True,
                                  'source_marg': True,
                                  'point_source_likelihood': False,
                                  'position_uncertainty': 0.004,
                                  'check_solver': False,
                                  'solver_tolerance': 0.001,
                                  'check_positive_flux': True,
                                  }

    def test_simulationAPI_image(self):
        npt.assert_almost_equal(self.data_class.data[4, 4], 0.1, decimal=0)

    def test_simulationAPI_psf(self):
        npt.assert_almost_equal(self.psf_class.kernel_pixel[1, 1], 0.0010335243878451812, decimal=6)

    def test_fitting_sequence(self):
        # kwargs_init = [self.kwargs_lens, self.kwargs_source, self.kwargs_lens_light, self.kwargs_ps]
        lens_sigma = [{'theta_E': 0.1, 'gamma': 0.1, 'e1': 0.1, 'e2': 0.1, 'center_x': 0.1, 'center_y': 0.1},
                      {'e1': 0.1, 'e2': 0.1}]
        lens_lower = [{'theta_E': 0., 'gamma': 1.5, 'center_x': -2, 'center_y': -2, 'e1': -0.4, 'e2': -0.4},
                      {'e1': -0.3, 'e2': -0.3}]
        lens_upper = [{'theta_E': 10., 'gamma': 2.5, 'center_x': 2, 'center_y': 2, 'e1': 0.4, 'e2': 0.4},
                      {'e1': 0.3, 'e2': 0.3}]
        source_sigma = [{'R_sersic': 0.05, 'n_sersic': 0.5, 'center_x': 0.1, 'center_y': 0.1, 'e1': 0.1, 'e2': 0.1}]
        source_lower = [{'R_sersic': 0.01, 'n_sersic': 0.5, 'center_x': -2, 'center_y': -2, 'e1': -0.4, 'e2': -0.4}]
        source_upper = [{'R_sersic': 10, 'n_sersic': 5.5, 'center_x': 2, 'center_y': 2, 'e1': 0.4, 'e2': 0.4}]

        lens_light_sigma = [{'R_sersic': 0.05, 'n_sersic': 0.5, 'center_x': 0.1, 'center_y': 0.1}]
        lens_light_lower = [{'R_sersic': 0.01, 'n_sersic': 0.5, 'center_x': -2, 'center_y': -2}]
        lens_light_upper = [{'R_sersic': 10, 'n_sersic': 5.5, 'center_x': 2, 'center_y': 2}]
        ps_sigma = [{'ra_source': 1, 'dec_source': 1, 'point_amp': 1}]

        lens_param = self.kwargs_lens, lens_sigma, [{}, {'ra_0': 0, 'dec_0': 0}], lens_lower, lens_upper
        source_param = self.kwargs_source, source_sigma, [{}], source_lower, source_upper
        lens_light_param = self.kwargs_lens_light, lens_light_sigma, [{}], lens_light_lower, lens_light_upper
        ps_param = self.kwargs_ps, ps_sigma, [{}], self.kwargs_ps, self.kwargs_ps

        kwargs_params = {'lens_model': lens_param,
                         'source_model': source_param,
                         'lens_light_model': lens_light_param,
                         'point_source_model': ps_param,
                         # 'cosmography': cosmo_param
                         }
        # kwargs_params = [kwargs_init, kwargs_sigma, kwargs_fixed, kwargs_init, kwargs_init]
        image_band = [self.kwargs_data, self.kwargs_psf, self.kwargs_numerics]
        multi_band_list = [image_band]
        fittingSequence = FittingSequence(multi_band_list, self.kwargs_model, self.kwargs_constraints,
                                          self.kwargs_likelihood, kwargs_params)

        lens_temp, source_temp, lens_light_temp, ps_temp, cosmo_temp = fittingSequence.best_fit(bijective=False)
        npt.assert_almost_equal(lens_temp[0]['theta_E'], self.kwargs_lens[0]['theta_E'], decimal=2)

        n_p = 2
        n_i = 2
        fitting_list = []
        fitting_kwargs_list = []

        kwargs_pso = {'sigma_scale': 1, 'n_particles': n_p, 'n_iterations': n_i}
        fitting_list.append('PSO')
        fitting_kwargs_list.append(kwargs_pso)
        fitting_list.append('MCMC')
        kwargs_mcmc = {'sigma_scale': 0.1, 'n_burn': 1, 'n_run': 1, 'walkerRatio': 2}
        fitting_kwargs_list.append(kwargs_mcmc)
        fitting_list.append('align_images')
        kwargs_align = { 'lowerLimit': -0.1, 'upperLimit': 0.1, 'n_particles': 2, 'n_iterations': 2}
        fitting_kwargs_list.append(kwargs_align)
        fitting_list.append('psf_iteration')
        kwargs_psf_iter = {'num_iter': 2, 'psf_iter_factor': 0.5, 'stacking_method': 'mean'}
        fitting_kwargs_list.append(kwargs_psf_iter)
        fitting_list.append('restart')
        fitting_kwargs_list.append({})
        fitting_list.append('update_settings')
        n_sersic_overwrite = 4
        kwargs_update = {'lens_light_add_fixed': [[0, ['n_sersic'], [n_sersic_overwrite]]]}
        fitting_kwargs_list.append(kwargs_update)

        #kwargs_model = {}, kwargs_constraints = {}, kwargs_likelihood = {}, lens_add_fixed = [],
        #source_add_fixed = [], lens_light_add_fixed = [], ps_add_fixed = [], cosmo_add_fixed = [], lens_remove_fixed = [],
        #source_remove_fixed = [], lens_light_remove_fixed = [], ps_remove_fixed = [], cosmo_remove_fixed = []

        chain_list, param_list, samples_mcmc, param_mcmc, dist_mcmc = fittingSequence.fit_sequence(fitting_list,
            fitting_kwargs_list=fitting_kwargs_list)
        lens_temp, source_temp, lens_light_temp, ps_temp, cosmo_temp = fittingSequence.best_fit(bijective=False)
        npt.assert_almost_equal(lens_temp[0]['theta_E'], self.kwargs_lens[0]['theta_E'], decimal=1)
        npt.assert_almost_equal(fittingSequence._updateManager._lens_light_fixed[0]['n_sersic'], n_sersic_overwrite, decimal=8)


if __name__ == '__main__':
    pytest.main()