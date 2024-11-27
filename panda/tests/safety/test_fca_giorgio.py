#!/usr/bin/env python3
import unittest

import panda.tests.safety.common as common

from panda import Panda
from panda.tests.libpanda import libpanda_py


class TestDefaultRxHookBase(common.PandaSafetyTestcommon, common.DriverTorqueSteeringSafetyTest):
  def test_rx_hook(self):
    # default rx hook allows all msgs
    for bus in range(4):
      for addr in self.SCANNED_ADDRS:
        self.assertTrue(self._rx(common.make_msg(bus, addr, 8)), f"failed RX {addr=}")

  DRIVER_TORQUE_ALLOWANCE = 0
  DRIVER_TORQUE_FACTOR = 0

  @classmethod
  def setUpClass(cls):
    if cls.__name__ == "DriverTorqueSteeringSafetyTest":
      cls.safety = None
      raise unittest.SkipTest

  @abc.abstractmethod
  def _torque_driver_msg(self, torque):
    pass

  def _reset_torque_driver_measurement(self, torque):
    for _ in range(MAX_SAMPLE_VALS):
      self._rx(self._torque_driver_msg(torque))

  def test_non_realtime_limit_up(self):
    self._reset_torque_driver_measurement(0)
    super().test_non_realtime_limit_up()

  def test_against_torque_driver(self):
    # Tests down limits and driver torque blending
    self.safety.set_controls_allowed(True)

    # Cannot stay at MAX_TORQUE if above DRIVER_TORQUE_ALLOWANCE
    for sign in [-1, 1]:
      for driver_torque in np.arange(0, self.DRIVER_TORQUE_ALLOWANCE * 2, 1):
        self._reset_torque_driver_measurement(-driver_torque * sign)
        self._set_prev_torque(self.MAX_TORQUE * sign)
        should_tx = abs(driver_torque) <= self.DRIVER_TORQUE_ALLOWANCE
        self.assertEqual(should_tx, self._tx(self._torque_cmd_msg(self.MAX_TORQUE * sign)))

    # arbitrary high driver torque to ensure max steer torque is allowed
    max_driver_torque = int(self.MAX_TORQUE / self.DRIVER_TORQUE_FACTOR + self.DRIVER_TORQUE_ALLOWANCE + 1)

    # spot check some individual cases
    for sign in [-1, 1]:
      # Ensure we wind down factor units for every unit above allowance
      driver_torque = (self.DRIVER_TORQUE_ALLOWANCE + 10) * sign
      torque_desired = (self.MAX_TORQUE - 10 * self.DRIVER_TORQUE_FACTOR) * sign
      delta = 1 * sign
      self._set_prev_torque(torque_desired)
      self._reset_torque_driver_measurement(-driver_torque)
      self.assertTrue(self._tx(self._torque_cmd_msg(torque_desired)))
      self._set_prev_torque(torque_desired + delta)
      self._reset_torque_driver_measurement(-driver_torque)
      self.assertFalse(self._tx(self._torque_cmd_msg(torque_desired + delta)))

      # If we're well past the allowance, minimum wind down is MAX_RATE_DOWN
      self._set_prev_torque(self.MAX_TORQUE * sign)
      self._reset_torque_driver_measurement(-max_driver_torque * sign)
      self.assertTrue(self._tx(self._torque_cmd_msg((self.MAX_TORQUE - self.MAX_RATE_DOWN) * sign)))
      self._set_prev_torque(self.MAX_TORQUE * sign)
      self._reset_torque_driver_measurement(-max_driver_torque * sign)
      self.assertTrue(self._tx(self._torque_cmd_msg(0)))
      self._set_prev_torque(self.MAX_TORQUE * sign)
      self._reset_torque_driver_measurement(-max_driver_torque * sign)
      self.assertFalse(self._tx(self._torque_cmd_msg((self.MAX_TORQUE - self.MAX_RATE_DOWN + 1) * sign)))

  def test_realtime_limits(self):
    self.safety.set_controls_allowed(True)

    for sign in [-1, 1]:
      self.safety.init_tests()
      self._set_prev_torque(0)
      self._reset_torque_driver_measurement(0)
      for t in np.arange(0, self.MAX_RT_DELTA, 1):
        t *= sign
        self.assertTrue(self._tx(self._torque_cmd_msg(t)))
      self.assertFalse(self._tx(self._torque_cmd_msg(sign * (self.MAX_RT_DELTA + 1))))

      self._set_prev_torque(0)
      for t in np.arange(0, self.MAX_RT_DELTA, 1):
        t *= sign
        self.assertTrue(self._tx(self._torque_cmd_msg(t)))

      # Increase timer to update rt_torque_last
      self.safety.set_timer(self.RT_INTERVAL + 1)
      self.assertTrue(self._tx(self._torque_cmd_msg(sign * (self.MAX_RT_DELTA - 1))))
      self.assertTrue(self._tx(self._torque_cmd_msg(sign * (self.MAX_RT_DELTA + 1))))

  def test_reset_driver_torque_measurements(self):
    # Tests that the driver torque measurement sample_t is reset on safety mode init
    for t in np.linspace(-self.MAX_TORQUE, self.MAX_TORQUE, MAX_SAMPLE_VALS):
      self.assertTrue(self._rx(self._torque_driver_msg(t)))

    self.assertNotEqual(self.safety.get_torque_driver_min(), 0)
    self.assertNotEqual(self.safety.get_torque_driver_max(), 0)

    self._reset_safety_hooks()
    self.assertEqual(self.safety.get_torque_driver_min(), 0)
    self.assertEqual(self.safety.get_torque_driver_max(), 0)



class TestNoOutput(TestDefaultRxHookBase):
  TX_MSGS = []

  def setUp(self):
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_NOOUTPUT, 0)
    self.safety.init_tests()


class TestSilent(TestNoOutput):
  """SILENT uses same hooks as NOOUTPUT"""

  def setUp(self):
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_SILENT, 0)
    self.safety.init_tests()


class TestAllOutput(TestDefaultRxHookBase):
  # Allow all messages
  TX_MSGS = [[addr, bus] for addr in common.PandaSafetyTest.SCANNED_ADDRS
             for bus in range(4)]

  def setUp(self):
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_ALLOUTPUT, 0)
    self.safety.init_tests()

  def test_spam_can_buses(self):
    # asserts tx allowed for all scanned addrs
    for bus in range(4):
      for addr in self.SCANNED_ADDRS:
        should_tx = [addr, bus] in self.TX_MSGS
        self.assertEqual(should_tx, self._tx(common.make_msg(bus, addr, 8)), f"allowed TX {addr=} {bus=}")

  def test_default_controls_not_allowed(self):
    # controls always allowed
    self.assertTrue(self.safety.get_controls_allowed())

  def test_tx_hook_on_wrong_safety_mode(self):
    # No point, since we allow all messages
    pass


class TestAllOutputPassthrough(TestAllOutput):
  FWD_BLACKLISTED_ADDRS = {}
  FWD_BUS_LOOKUP = {0: 2, 2: 0}

  def setUp(self):
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_ALLOUTPUT, 1)
    self.safety.init_tests()


if __name__ == "__main__":
  unittest.main()
