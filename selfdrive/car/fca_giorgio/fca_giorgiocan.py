def crc8(combined_bits):
  crc = 0xFF
  poly = 0x1D
  data = combined_bits.to_bytes(3, byteorder='big')
  
  for byte in data:
    crc = crc ^ byte
    for _ in range(8):
      if crc & 0x80:
        crc = ((crc << 1) ^ poly) & 0xFF
      else:
        crc = (crc << 1) & 0xFF
  return [crc ^ 0xFF]
    
def create_steering_control(packer, bus, apply_steer, lkas_enabled, frame):
  combined_bits = (apply_steer << 13) | (lkas_enabled << 12) | (0 << 4) | frame
  values = {
    "LKA_TORQUE": apply_steer,
    "LKA_ENABLED": lkas_enabled,
    "COUNTER": 15, #frame % 0x10,
    "CHKSUM": 0xFF, #crc8(combined_bits),
  }

  return packer.make_can_msg("LKA_COMMAND", bus, values)

#def create_lka_hud_1_control(packer, bus, lat_active):
#  values = {
#    "NEW_SIGNAL_5": 1,
#    "NEW_SIGNAL_4": 6,
#  }
#
#  return packer.make_can_msg("LKA_HUD_1", bus, values)

def create_lka_hud_2_control(packer, bus, apply_steer, lkas_enabled):
  values = {
    "LKA_ACTIVE": 10 if apply_steer > 0 else 8 if apply_steer < 0 else 6,
    "NEW_SIGNAL_1": lkas_enabled,
  }

  return packer.make_can_msg("LKA_HUD_2", bus, values)

# LKA_ACTIVE
# 6 (0110) = green car with both white lines
# 10 (1010) or 12 (1100) yellow on left, positive torque to turn right
# 8 (1000) or 11 (1011) yellow on right, negative torque to turn left
