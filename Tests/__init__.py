import ModuleTests
import IntensityTransferTests
import unittest


def getSuites():
    modsuites=ModuleTests.suite()
    intensitysuites=IntensityTransferTests.suite()

    suite=unittest.TestSuite((modsuites,intensitysuites))
    return suite
