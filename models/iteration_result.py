from dataclasses import dataclass


@dataclass
class IterationResult:
    iteration: int

    cooling_setpoint: float
    heating_setpoint: float

    outdoor_temperature: float
    indoor_temperature: float

    cooling_rate: float
    heating_rate: float

    chiller_electricity: float
    plant_cooling_demand: float

    confidence: float