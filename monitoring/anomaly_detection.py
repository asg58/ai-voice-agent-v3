class AnomalyDetection:
    def detect_anomalies(self, metrics):
        """
        Detecteer afwijkingen in systeemgedrag.
        """
        # Mock implementatie
        anomalies = [metric for metric in metrics if metric > 100]
        return {"anomalies": anomalies}
