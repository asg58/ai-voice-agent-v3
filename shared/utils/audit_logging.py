import logging

class AuditLogger:
    def __init__(self, log_file="audit.log"):
        self.logger = logging.getLogger("AuditLogger")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, message):
        self.logger.info(message)

# Example usage
# audit_logger = AuditLogger()
# audit_logger.log("User accessed sensitive data.")
