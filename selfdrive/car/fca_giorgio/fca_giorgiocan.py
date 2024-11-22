def create_steering_control(packer, bus, apply_steer, cruiseState):
  values = {
    "LKA_TORQUE": apply_steer,
    "LKA_ENABLED": 1 if cruiseState else 0,
  }

  return packer.make_can_msg("LKA_COMMAND", bus, values)

def create_lka_hud_2_control(packer, bus, apply_steer, cruiseState):
  values = {
    "LKA_ACTIVE": 6 if cruiseState else 1,
    "NEW_SIGNAL_1": 1 if cruiseState else 0,
  }

  return packer.make_can_msg("LKA_HUD_2", bus, values)

def create_acc_1_control(packer, bus, apply_steer, cruiseState):
  values = {
    "LKA_CHECK": 1 if apply_steer != 0 else 0,
  }

  return packer.make_can_msg("ACC_1", bus, values)

# LKA_ACTIVE
# 6 (0110) = green car with both white lines
# 10 (1010) or 12 (1100) yellow on left, positive torque to turn right
# 8 (1000) or 11 (1011) yellow on right, negative torque to turn left
