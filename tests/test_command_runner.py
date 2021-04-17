from unittest import TestCase
from pymongoclient.connection.commandrunner import CommandRunner


class TestCommandRunner(TestCase):
    def test_run_query(self):

        command_runner = CommandRunner("mongodb://dkmongo:dk1234@192.168.50.101:27017/dk")

        command_runner.start()

        result = command_runner.execute("db.DKCustomersdkmaster.find({})")
        print(result)
