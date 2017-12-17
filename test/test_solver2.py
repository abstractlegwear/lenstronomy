__author__ = 'sibirrer'

import numpy as np
import numpy.testing as npt
import pytest
from astrofunc.LensingProfiles.nfw import NFW
from lenstronomy.LensModel.lens_model import LensModel
from lenstronomy.Solver.lens_equation_solver import LensEquationSolver
from lenstronomy.Solver.solver2point import Solver2Point


class TestSolver(object):
    """
    tests the Gaussian methods
    """
    def setup(self):
        pass

    def test_subtract(self):
        solver_spep_center = Solver2Point(['SPEP'], solver_type='CENTER')
        x_cat = np.array([0, 0])
        y_cat = np.array([1, 2])
        a = solver_spep_center._subtract_constraint(x_cat, y_cat)
        assert a[0] == 0
        assert a[1] == 1

    def test_all_spep(self):
        solver_spep_center = Solver2Point(['SPEP'], solver_type='CENTER')
        solver_spep_ellipse = Solver2Point(['SPEP'], solver_type='ELLIPSE')
        image_position_spep = LensEquationSolver(['SPEP'])
        sourcePos_x = 0.1
        sourcePos_y = 0.03
        deltapix = 0.05
        numPix = 100
        gamma = 1.9
        kwargs_lens = [{'theta_E': 1, 'gamma': gamma, 'q': 0.8, 'phi_G': 0.5, 'center_x': 0.1, 'center_y': -0.1}]
        x_pos, y_pos = image_position_spep.findBrightImage(sourcePos_x, sourcePos_y, kwargs_lens, deltapix, numPix)
        x_pos = x_pos[:2]
        y_pos = y_pos[:2]
        kwargs_init = [{'theta_E': 1, 'gamma': gamma, 'q': 0.8, 'phi_G': 0.5, 'center_x': 0, 'center_y': 0}]
        kwargs_out_center = solver_spep_center.constraint_lensmodel(x_pos, y_pos, kwargs_init)

        kwargs_init = [{'theta_E': 1, 'gamma': gamma, 'q': 0.99, 'phi_G': 0., 'center_x': 0.1, 'center_y': -0.1}]
        kwargs_out_ellipse = solver_spep_ellipse.constraint_lensmodel(x_pos, y_pos, kwargs_init)

        npt.assert_almost_equal(kwargs_out_center[0]['center_x'], kwargs_lens[0]['center_x'], decimal=3)
        npt.assert_almost_equal(kwargs_out_center[0]['center_y'], kwargs_lens[0]['center_y'], decimal=3)
        npt.assert_almost_equal(kwargs_out_center[0]['center_y'], -0.1, decimal=3)

        npt.assert_almost_equal(kwargs_out_ellipse[0]['q'], kwargs_lens[0]['q'], decimal=3)
        npt.assert_almost_equal(kwargs_out_ellipse[0]['phi_G'], kwargs_lens[0]['phi_G'], decimal=3)
        npt.assert_almost_equal(kwargs_out_ellipse[0]['q'], 0.8, decimal=3)

    def test_all_nfw(self):
        solver_nfw_ellipse = Solver2Point(['SPEP'], solver_type='ELLIPSE')
        solver_nfw_center = Solver2Point(['SPEP'], solver_type='CENTER')
        spep = LensModel(['SPEP'])
        image_position_nfw = LensEquationSolver(['SPEP', 'NFW'])
        sourcePos_x = 0.1
        sourcePos_y = 0.03
        deltapix = 0.05
        numPix = 100
        gamma = 1.9
        Rs = 0.1
        nfw = NFW()
        theta_Rs = nfw._rho02alpha(1., Rs)
        kwargs_lens = [{'theta_E': 1., 'gamma': gamma, 'q': 0.8, 'phi_G': 0.5, 'center_x': 0.1, 'center_y': -0.1},
                       {'Rs': Rs, 'theta_Rs': theta_Rs, 'center_x': -0.5, 'center_y': 0.5}]
        x_pos, y_pos = image_position_nfw.findBrightImage(sourcePos_x, sourcePos_y, kwargs_lens, kwargs_else=None, numImages=2, min_distance=deltapix, search_window=numPix*deltapix)
        print(len(x_pos), 'number of images')
        x_pos = x_pos[:2]
        y_pos = y_pos[:2]

        kwargs_init = [{'theta_E': 1, 'gamma': gamma, 'q': 0.8, 'phi_G': 0.5, 'center_x': 0., 'center_y': 0},
                       {'Rs': Rs, 'theta_Rs': theta_Rs, 'center_x': -0.5, 'center_y': 0.5}]
        kwargs_out_center = solver_nfw_center.constraint_lensmodel(x_pos, y_pos, kwargs_init)
        source_x, source_y = spep.ray_shooting(x_pos[0], y_pos[0], kwargs_out_center)
        x_pos_new, y_pos_new = image_position_nfw.findBrightImage(source_x, source_y, kwargs_out_center, kwargs_else=None, numImages=2, min_distance=deltapix, search_window=numPix*deltapix)

        npt.assert_almost_equal(x_pos_new[0], x_pos[0], decimal=2)
        npt.assert_almost_equal(y_pos_new[0], y_pos[0], decimal=2)

        npt.assert_almost_equal(kwargs_out_center[0]['center_x'], kwargs_lens[0]['center_x'], decimal=2)
        npt.assert_almost_equal(kwargs_out_center[0]['center_y'], kwargs_lens[0]['center_y'], decimal=2)
        npt.assert_almost_equal(kwargs_out_center[0]['center_y'], -0.1, decimal=2)

        kwargs_init = [{'theta_E': 1., 'gamma': gamma, 'q': 0.99, 'phi_G': 0., 'center_x': 0.1, 'center_y': -0.1},
                       {'Rs': Rs, 'theta_Rs': theta_Rs, 'center_x': -0.5, 'center_y': 0.5}]
        kwargs_out_ellipse = solver_nfw_ellipse.constraint_lensmodel(x_pos, y_pos, kwargs_init)

        npt.assert_almost_equal(kwargs_out_ellipse[0]['q'], kwargs_lens[0]['q'], decimal=2)
        npt.assert_almost_equal(kwargs_out_ellipse[0]['phi_G'], kwargs_lens[0]['phi_G'], decimal=2)
        npt.assert_almost_equal(kwargs_out_ellipse[0]['q'], 0.8, decimal=2)


    def test_all_spep_sis(self):
        solver_ellipse = Solver2Point(['SPEP', 'SIS'], solver_type='ELLIPSE')
        solver_center = Solver2Point(['SPEP', 'SIS'], solver_type='CENTER')
        spep = LensModel(['SPEP', 'SIS'])
        image_position = LensEquationSolver(['SPEP', 'SIS'])
        sourcePos_x = 0.1
        sourcePos_y = 0.03
        deltapix = 0.05
        numPix = 100
        gamma = 1.9
        kwargs_lens = [{'theta_E': 1., 'gamma': gamma, 'q': 0.8, 'phi_G': 0.5, 'center_x': 0.1, 'center_y': -0.1},
                       {'theta_E': 0.6, 'center_x': -0.5, 'center_y': 0.5}]
        x_pos, y_pos = image_position.findBrightImage(sourcePos_x, sourcePos_y, kwargs_lens, kwargs_else=None, numImages=2, min_distance=deltapix, search_window=numPix*deltapix, precision_limit=10**(-10))
        print(len(x_pos), 'number of images')
        x_pos = x_pos[:2]
        y_pos = y_pos[:2]

        kwargs_init = [{'theta_E': 1, 'gamma': gamma, 'q': 0.8, 'phi_G': 0.5, 'center_x': 0., 'center_y': 0},
                       {'theta_E': 0.6, 'center_x': -0.5, 'center_y': 0.5}]
        kwargs_out_center = solver_center.constraint_lensmodel(x_pos, y_pos, kwargs_init)
        print(kwargs_out_center, 'output')
        source_x, source_y = spep.ray_shooting(x_pos[0], y_pos[0], kwargs_out_center)
        x_pos_new, y_pos_new = image_position.findBrightImage(source_x, source_y, kwargs_out_center, kwargs_else=None, numImages=2, min_distance=deltapix, search_window=numPix*deltapix)
        npt.assert_almost_equal(x_pos_new[0], x_pos[0], decimal=3)
        npt.assert_almost_equal(y_pos_new[0], y_pos[0], decimal=3)

        npt.assert_almost_equal(kwargs_out_center[0]['center_x'], kwargs_lens[0]['center_x'], decimal=3)
        npt.assert_almost_equal(kwargs_out_center[0]['center_y'], kwargs_lens[0]['center_y'], decimal=3)
        npt.assert_almost_equal(kwargs_out_center[0]['center_y'], -0.1, decimal=3)

        kwargs_init = [{'theta_E': 1., 'gamma': gamma, 'q': 0.99, 'phi_G': 0., 'center_x': 0.1, 'center_y': -0.1},
                       {'theta_E': 0.6, 'center_x': -0.5, 'center_y': 0.5}]
        kwargs_out_ellipse = solver_ellipse.constraint_lensmodel(x_pos, y_pos, kwargs_init)

        npt.assert_almost_equal(kwargs_out_ellipse[0]['q'], kwargs_lens[0]['q'], decimal=3)
        npt.assert_almost_equal(kwargs_out_ellipse[0]['phi_G'], kwargs_lens[0]['phi_G'], decimal=3)
        npt.assert_almost_equal(kwargs_out_ellipse[0]['q'], 0.8, decimal=3)


if __name__ == '__main__':
    pytest.main()