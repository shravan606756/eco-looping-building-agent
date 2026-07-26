import pandas as pd
from models.building_state import BuildingState


class OutputParser:

    outdoor_temp_col = "Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"

    indoor_temp_cols = [
        "SPACE1-1:Zone Air Temperature [C](Hourly)",
        "SPACE2-1:Zone Air Temperature [C](Hourly)",
        "SPACE3-1:Zone Air Temperature [C](Hourly)",
        "SPACE4-1:Zone Air Temperature [C](Hourly)",
        "SPACE5-1:Zone Air Temperature [C](Hourly)"
    ]

    cooling_cols = [
        "SPACE1-1:Zone Air System Sensible Cooling Rate [W](Hourly)",
        "SPACE2-1:Zone Air System Sensible Cooling Rate [W](Hourly)",
        "SPACE3-1:Zone Air System Sensible Cooling Rate [W](Hourly)",
        "SPACE4-1:Zone Air System Sensible Cooling Rate [W](Hourly)",
        "SPACE5-1:Zone Air System Sensible Cooling Rate [W](Hourly)"
    ]

    heating_cols = [
        "SPACE1-1:Zone Air System Sensible Heating Rate [W](Hourly)",
        "SPACE2-1:Zone Air System Sensible Heating Rate [W](Hourly)",
        "SPACE3-1:Zone Air System Sensible Heating Rate [W](Hourly)",
        "SPACE4-1:Zone Air System Sensible Heating Rate [W](Hourly)",
        "SPACE5-1:Zone Air System Sensible Heating Rate [W](Hourly)"
    ]

    chiller_col = "CENTRAL CHILLER:Chiller Electricity Rate [W](Hourly)"
    plant_cooling_col = "CHILLED WATER LOOP:Plant Supply Side Cooling Demand Rate [W](Hourly)"

    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)

    def _compute_weather_features(self, window: pd.DataFrame) -> dict:
        series = window[self.outdoor_temp_col]
        return {
            "average_outdoor_temperature": float(series.mean()),
            "minimum_outdoor_temperature": float(series.min()),
            "maximum_outdoor_temperature": float(series.max()),
        }

    def _compute_indoor_comfort_features(self, window: pd.DataFrame) -> dict:
        indoor_df = window[self.indoor_temp_cols]
        vals = indoor_df.values.flatten()
        return {
            "average_indoor_temperature": float(indoor_df.mean().mean()),
            "minimum_indoor_temperature": float(indoor_df.min().min()),
            "maximum_indoor_temperature": float(indoor_df.max().max()),
            "temperature_standard_deviation": float(vals.std()),
        }

    def _compute_cooling_features(self, window: pd.DataFrame) -> dict:
        total_cooling_series = window[self.cooling_cols].sum(axis=1)
        avg_rate = float(total_cooling_series.mean())
        peak_rate = float(total_cooling_series.max())
        total_energy = float(total_cooling_series.sum())
        load_factor = (avg_rate / peak_rate) if peak_rate > 0 else 0.0
        return {
            "average_cooling_rate": avg_rate,
            "peak_cooling_rate": peak_rate,
            "total_cooling_energy": total_energy,
            "cooling_load_factor": float(load_factor),
        }

    def _compute_heating_features(self, window: pd.DataFrame) -> dict:
        total_heating_series = window[self.heating_cols].sum(axis=1)
        avg_rate = float(total_heating_series.mean())
        peak_rate = float(total_heating_series.max())
        total_energy = float(total_heating_series.sum())
        load_factor = (avg_rate / peak_rate) if peak_rate > 0 else 0.0
        return {
            "average_heating_rate": avg_rate,
            "peak_heating_rate": peak_rate,
            "total_heating_energy": total_energy,
            "heating_load_factor": float(load_factor),
        }

    def _compute_chiller_features(self, window: pd.DataFrame) -> dict:
        series = window[self.chiller_col]
        return {
            "average_chiller_power": float(series.mean()),
            "peak_chiller_power": float(series.max()),
        }

    def _compute_plant_features(self, window: pd.DataFrame) -> dict:
        series = window[self.plant_cooling_col]
        return {
            "average_plant_cooling_demand": float(series.mean()),
            "peak_plant_cooling_demand": float(series.max()),
        }

    def _compute_comfort_metrics(
        self,
        window: pd.DataFrame,
        comfort_min: float = 21.0,
        comfort_max: float = 25.0
    ) -> dict:
        mean_indoor_per_hour = window[self.indoor_temp_cols].mean(axis=1)
        comfort_mask = (mean_indoor_per_hour >= comfort_min) & (mean_indoor_per_hour <= comfort_max)
        c_hours = float(comfort_mask.sum())
        d_hours = float((~comfort_mask).sum())
        total_hours = float(len(window))
        c_pct = (c_hours / total_hours * 100.0) if total_hours > 0 else 0.0
        return {
            "comfort_hours": c_hours,
            "discomfort_hours": d_hours,
            "comfort_percentage": float(c_pct),
        }

    def _determine_hvac_operating_mode(self, avg_heating: float, avg_cooling: float) -> str:
        threshold = 100.0
        if avg_cooling > avg_heating + threshold:
            return "Cooling Dominant"
        elif avg_heating > avg_cooling + threshold:
            return "Heating Dominant"
        else:
            return "Balanced"

    def _determine_temperature_trend(self, window: pd.DataFrame) -> str:
        mean_indoor_per_hour = window[self.indoor_temp_cols].mean(axis=1)
        n = len(mean_indoor_per_hour)
        if n < 4:
            return "Stable"

        sample_size = max(1, n // 4)
        first_avg = mean_indoor_per_hour.iloc[:sample_size].mean()
        last_avg = mean_indoor_per_hour.iloc[-sample_size:].mean()

        diff = last_avg - first_avg
        if diff > 0.5:
            return "Increasing"
        elif diff < -0.5:
            return "Decreasing"
        else:
            return "Stable"

    def latest_state(self, hours: int = 24) -> BuildingState:
        window = self.df.tail(hours)

        weather = self._compute_weather_features(window)
        comfort_stats = self._compute_indoor_comfort_features(window)
        cooling = self._compute_cooling_features(window)
        heating = self._compute_heating_features(window)
        chiller = self._compute_chiller_features(window)
        plant = self._compute_plant_features(window)
        comfort_metrics = self._compute_comfort_metrics(window)

        hvac_mode = self._determine_hvac_operating_mode(
            heating["average_heating_rate"],
            cooling["average_cooling_rate"]
        )
        temp_trend = self._determine_temperature_trend(window)

        timestamp = str(window.iloc[-1]["Date/Time"]).strip()

        return BuildingState(
            timestamp=timestamp,

            # Weather
            average_outdoor_temperature=weather["average_outdoor_temperature"],
            minimum_outdoor_temperature=weather["minimum_outdoor_temperature"],
            maximum_outdoor_temperature=weather["maximum_outdoor_temperature"],

            # Indoor Comfort
            average_indoor_temperature=comfort_stats["average_indoor_temperature"],
            minimum_indoor_temperature=comfort_stats["minimum_indoor_temperature"],
            maximum_indoor_temperature=comfort_stats["maximum_indoor_temperature"],
            temperature_standard_deviation=comfort_stats["temperature_standard_deviation"],

            # Cooling
            average_cooling_rate=cooling["average_cooling_rate"],
            peak_cooling_rate=cooling["peak_cooling_rate"],
            total_cooling_energy=cooling["total_cooling_energy"],
            cooling_load_factor=cooling["cooling_load_factor"],

            # Heating
            average_heating_rate=heating["average_heating_rate"],
            peak_heating_rate=heating["peak_heating_rate"],
            total_heating_energy=heating["total_heating_energy"],
            heating_load_factor=heating["heating_load_factor"],

            # Chiller
            average_chiller_power=chiller["average_chiller_power"],
            peak_chiller_power=chiller["peak_chiller_power"],

            # Plant Loop
            average_plant_cooling_demand=plant["average_plant_cooling_demand"],
            peak_plant_cooling_demand=plant["peak_plant_cooling_demand"],

            # Comfort Metrics
            comfort_hours=comfort_metrics["comfort_hours"],
            discomfort_hours=comfort_metrics["discomfort_hours"],
            comfort_percentage=comfort_metrics["comfort_percentage"],

            # Categorical Trends
            hvac_operating_mode=hvac_mode,
            temperature_trend=temp_trend,

            # Legacy attributes
            outdoor_temperature=weather["average_outdoor_temperature"],
            chiller_electricity=chiller["average_chiller_power"],
            plant_cooling_demand=plant["average_plant_cooling_demand"],
        )