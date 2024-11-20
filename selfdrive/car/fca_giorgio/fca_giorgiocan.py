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
  return crc ^ 0xFF

def fca_compute_checksum(combined_bits):
  checksum = 0xFF
  data = combined_bits.to_bytes(3, byteorder='big')

  for j in range(3):
    shift = 0x80
    curr = data[j]

    for _ in range(8):
      bit_sum = curr & shift
      temp_chk = checksum & 0x80

      if bit_sum != 0:
        bit_sum = 0x1C
        if temp_chk != 0:
          bit_sum = 1
        checksum = checksum << 1
        temp_chk = checksum | 1
        bit_sum ^= temp_chk
      
      else:
        if temp_chk != 0:
          bit_sum = 0x1D
        checksum = checksum << 1
        bit_sum ^= checksum
      
      checksum = bit_sum
      shift = shift >> 1

  return ~checksum & 0xFF

def create_steering_control(packer, bus, apply_steer, lkas_enabled, frame):
  combined_bits = (apply_steer << 13) | (lkas_enabled << 12) | (0 << 4) | frame
  values = {
    "LKA_TORQUE": apply_steer,
    "LKA_ENABLED": lkas_enabled,
    "COUNTER": frame & 0xF,
    "CHKSUM": fca_compute_checksum(combined_bits),
  }

  return packer.make_can_msg("LKA_COMMAND", bus, values)

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
