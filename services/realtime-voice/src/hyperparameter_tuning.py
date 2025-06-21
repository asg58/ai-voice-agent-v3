class HyperparameterTuning:
    def tune_parameters(self, model, param_grid):
        """
        Optimaliseer modelparameters.
        """
        # Mock implementatie
        best_params = {key: max(values) for key, values in param_grid.items()}
        model.set_parameters(best_params)
        return model
