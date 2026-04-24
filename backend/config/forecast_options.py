class ForecastOptionsSettings:
    """Forecast entry options served to the frontend."""

    def __init__(self) -> None:
        self.estimate_types = [
            "source_point_estimate",
            "llm_point_estimate",
            "llm_scenario_estimate",
            "manual_point_estimate",
            "manual_scenario_estimate",
        ]
        self.scenarios = ["bear", "base", "bull", "single"]
