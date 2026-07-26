from controller.schedule_modifier import ScheduleModifier

modifier = ScheduleModifier(
    "data/idf/working/current.idf"
)

modifier.update_setpoints(
    cooling=24.5,
    heating=20.0
)

print("Done")