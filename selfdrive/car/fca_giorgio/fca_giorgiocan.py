def create_steering_control(packer, bus, apply_steer, lkas_enabled):
  values = {
    "LKA_ACTIVE": lkas_enabled,
    "LKA_TORQUE": apply_steer,
    "ACC_ENABLED": lkas_enabled,
  }

  return packer.make_can_msg("LKA_COMMAND", bus, values)


#def create_lka_hud_1_control(packer, bus, lat_active):
#  values = {
#    "NEW_SIGNAL_5": 1,
#    "NEW_SIGNAL_4": 6,
#  }
#
#  return packer.make_can_msg("LKA_HUD_1", bus, values)


def create_lka_hud_2_control(packer, bus, lat_active):
  values = {
    "NEW_SIGNAL_1": 1 if lat_active else 0,
    "NEW_SIGNAL_2": 6 if lat_active else 1,
  }

  return packer.make_can_msg("LKA_HUD_2", bus, values)
