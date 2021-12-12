import unittest

def stopTestRun(self):
    """
    https://docs.python.org/3/library/unittest.html#unittest.TestResult.stopTestRun
    Called once after all tests are executed.

    :return:
    """
    from opasCentralDBLib import opasCentralDB
    ocd = opasCentralDB()
    ocd.end_session(session_id=headers["client-session"])
    print ("Session End")

setattr(unittest.TestResult, 'stopTestRun', stopTestRun)