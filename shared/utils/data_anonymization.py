import re

def anonymize_data(data):
    """
    Anonymize sensitive information in the given data.
    """
    # Example: Replace email addresses with [REDACTED]
    data = re.sub(r'[\w.-]+@[\w.-]+', '[REDACTED]', data)
    # Example: Replace phone numbers with [REDACTED]
    data = re.sub(r'\b\d{10}\b', '[REDACTED]', data)
    return data

# Example usage
# anonymized_data = anonymize_data("Contact me at john.doe@example.com or 1234567890.")
# print(anonymized_data)
