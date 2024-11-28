from opendbc.can.packer import CANPacker
from openpilot.selfdrive.car import apply_driver_steer_torque_limits
from openpilot.selfdrive.car.interfaces import CarControllerBase

from openpilot.selfdrive.car.fca_giorgio import fca_giorgiocan
from openpilot.selfdrive.car.fca_giorgio.values import CANBUS, CarControllerParams


class CarController(CarControllerBase):
  def __init__(self, dbc_name, CP, VM):
    self.CP = CP
    self.CCP = CarControllerParams(CP)
    self.packer_pt = CANPacker(dbc_name)

    self.apply_steer_last = 0
    self.frame = 0
    
    self.lkas_control_bit_prev = False
    self.last_lkas_falling_edge = 0

  def update(self, CC, CS, now_nanos):
    actuators = CC.actuators
    can_sends = []

    lkas_active = CC.latActive and self.lkas_control_bit_prev
    high_beam = CS.out.stockAeb

    # **** Steering Controls ************************************************ #

    lkas_control_bit = self.lkas_control_bit_prev
    if CS.out.vEgo > self.CP.minSteerSpeed:
      lkas_control_bit = True
    
    # EPS faults if LKAS re-enables too quickly
    lkas_control_bit = lkas_control_bit and (self.frame - self.last_lkas_falling_edge > 200)

    if not lkas_control_bit and self.lkas_control_bit_prev:
      self.last_lkas_falling_edge = self.frame
    self.lkas_control_bit_prev = lkas_control_bit

    if self.frame % self.CCP.STEER_STEP == 0:
      if CC.latActive and lkas_active and lkas_control_bit:
        new_steer = int(round(actuators.steer * self.CCP.STEER_MAX))
        apply_steer = apply_driver_steer_torque_limits(new_steer, self.apply_steer_last, CS.out.steeringTorque, self.CCP)
      else:
        apply_steer = 0

      self.apply_steer_last = apply_steer
      can_sends.append(fca_giorgiocan.create_steering_control(self.packer_pt, CANBUS.pt, apply_steer, lkas_active))

    # **** HUD Controls ***************************************************** #

    if self.frame % self.CCP.HUD_2_STEP == 0:
      can_sends.append(fca_giorgiocan.create_lka_hud_2_control(self.packer_pt, CANBUS.pt, lkas_control_bit, high_beam))
    
    if self.frame % self.CCP.ACC_1_STEP == 0:
      can_sends.append(fca_giorgiocan.create_acc_1_control(self.packer_pt, CANBUS.pt, apply_steer))

    new_actuators = actuators.as_builder()
    new_actuators.steer = self.apply_steer_last / self.CCP.STEER_MAX
    new_actuators.steerOutputCan = self.apply_steer_last

    self.frame += 1
    return new_actuators, can_sends
