from dataclasses import dataclass


@dataclass
class BuildingState:

    timestamp: str

    # Weather
    average_outdoor_temperature: float = 0.0
    minimum_outdoor_temperature: float = 0.0
    maximum_outdoor_temperature: float = 0.0

    # Indoor Comfort
    average_indoor_temperature: float = 0.0
    minimum_indoor_temperature: float = 0.0
    maximum_indoor_temperature: float = 0.0
    temperature_standard_deviation: float = 0.0

    # Cooling
    average_cooling_rate: float = 0.0
    peak_cooling_rate: float = 0.0
    total_cooling_energy: float = 0.0
    cooling_load_factor: float = 0.0

    # Heating
    average_heating_rate: float = 0.0
    peak_heating_rate: float = 0.0
    total_heating_energy: float = 0.0
    heating_load_factor: float = 0.0

    # Chiller
    average_chiller_power: float = 0.0
    peak_chiller_power: float = 0.0

    # Plant Loop
    average_plant_cooling_demand: float = 0.0
    peak_plant_cooling_demand: float = 0.0

    # Comfort Metrics
    comfort_hours: float = 0.0
    discomfort_hours: float = 0.0
    comfort_percentage: float = 0.0

    # HVAC Intelligence & Categorical Trends
    hvac_operating_mode: str = "Balanced"
    temperature_trend: str = "Stable"

    # Legacy attributes for backward compatibility
    outdoor_temperature: float = 0.0
    chiller_electricity: float = 0.0
    plant_cooling_demand: float = 0.0

    def __post_init__(self):
        if self.outdoor_temperature == 0.0 and self.average_outdoor_temperature != 0.0:
            self.outdoor_temperature = self.average_outdoor_temperature
        if self.chiller_electricity == 0.0 and self.average_chiller_power != 0.0:
            self.chiller_electricity = self.average_chiller_power
        if self.plant_cooling_demand == 0.0 and self.average_plant_cooling_demand != 0.0:
            self.plant_cooling_demand = self.average_plant_cooling_demand