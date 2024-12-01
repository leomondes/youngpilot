from dataclasses import dataclass, field

from openpilot.selfdrive.car import dbc_dict, CarSpecs, DbcDict, PlatformConfig, Platforms
from openpilot.selfdrive.car.docs_definitions import CarHarness, CarDocs, CarParts
from openpilot.selfdrive.car.fw_query_definitions import FwQueryConfig, Request, StdQueries


class CarControllerParams:
  def __init__(self, CP):
   self.STEER_STEP = 1
   self.HUD_2_STEP = 25
   self.ACC_1_STEP = 100
   self.STEER_ERROR_MAX = 80

   self.STEER_MAX = 300
   self.STEER_DRIVER_ALLOWANCE = 80
   self.STEER_DRIVER_MULTIPLIER = 4  # weight driver torque heavily
   self.STEER_DRIVER_FACTOR = 1  # from dbc
   self.STEER_DELTA_UP = 2
   self.STEER_DELTA_DOWN = 2


class CANBUS:
  pt = 0
  body = 1
  cam = 2


@dataclass
class FcaGiorgioPlatformConfig(PlatformConfig):
  dbc_dict: DbcDict = field(default_factory=lambda: dbc_dict('fca_giorgio', None))


@dataclass(frozen=True, kw_only=True)
class FcaGiorgioCarSpecs(CarSpecs):
  centerToFrontRatio: float = 0.45
  steerRatio: float = 16
  minSteerSpeed: float = 14.0 # m/s, newer EPS racks fault below this speed, don't show a low speed alert


@dataclass
class FcaGiorgioCarDocs(CarDocs):
  package: str = "Adaptive Cruise Control (ACC) & Lane Assist"
  car_parts: CarParts = field(default_factory=CarParts.common([CarHarness.vw_a]))


class CAR(Platforms):
  config: FcaGiorgioPlatformConfig

  JEEP_RENEGADE_MY22 = FcaGiorgioPlatformConfig(
    [FcaGiorgioCarDocs("Jeep Renegade 4xe Hybrid 2022")],
    FcaGiorgioCarSpecs(mass=1845, wheelbase=2.57),
  )


FW_QUERY_CONFIG = FwQueryConfig(
  requests=[
    # TODO: check data to ensure ABS does not skip ISO-TP frames on bus 0
    Request(
      [StdQueries.MANUFACTURER_SOFTWARE_VERSION_REQUEST],
      [StdQueries.MANUFACTURER_SOFTWARE_VERSION_RESPONSE],
      bus=0,
    ),
  ],
)


DBC = CAR.create_dbc_map()
