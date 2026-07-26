from ai.agent import BuildingOptimizationAgent
from models.building_state import BuildingState


state = BuildingState(
    timestamp="12/31 24:00",
    outdoor_temperature=34,
    average_indoor_temperature=27,
    average_cooling_rate=4200,
    average_heating_rate=0,
    chiller_electricity=1800,
    plant_cooling_demand=3900
)

agent = BuildingOptimizationAgent()

decision = agent.decide(state)

print(decision)