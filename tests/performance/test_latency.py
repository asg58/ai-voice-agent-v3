import pytest
import time

class MockPipeline:
    def process(self, audio_input):
        return "processed_response"

pipeline = MockPipeline()
audio_input = "mock_audio_data"

@pytest.mark.performance
def test_latency():
    """
    Meet de latentie van de end-to-end pipeline.
    """
    start_time = time.time()
    pipeline.process(audio_input)
    end_time = time.time()

    latency = end_time - start_time
    assert latency < 1.2
