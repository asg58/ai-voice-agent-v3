class FederatedLearning:
    def aggregate_models(self, local_models):
        """
        Combineer lokale modellen tot een globaal model.
        """
        # Mock implementatie
        global_model = sum(local_models) / len(local_models)
        return global_model
