import os


def test_guard_no_ai():
    # If pytest visits test/ai/, it will attempt to execute this test and fail
    if os.getenv('E0B_TESTING_NOAI') == 'true':
        assert 32 // 8 == 5, "Bro attempted to execute test/ai/"
