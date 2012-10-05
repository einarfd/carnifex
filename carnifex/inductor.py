from twisted.internet.protocol import ProcessProtocol
from twisted.internet import defer


class ProcessInductor(object):
    """Creates and follow up processes of local or remotely executed commands.
    """

    def __init__(self, processFactory):
        self.processFactory = processFactory

    def execute(self, processProtocol, executable, args=None):
        """Form a command and start a process in the desired environment.
        """
        return self.processFactory.spawnProcess(processProtocol,
                                                executable,
                                                args or (executable,))

    def run(self, executable, args=None):
        """Execute a command and return the results of the completed run.
        """
        deferred = defer.Deferred()
        processProtocol = _SummaryProcessProtocol(deferred)
        self.execute(processProtocol, executable, args)
        return deferred


class _SummaryProcessProtocol(ProcessProtocol):
    """Gathers data of the process and delivers a summary when it completes.
    """

    def __init__(self, deferred, stdout=True, stderr=True, returnCode=True,
                 mergeErr=False):
        """
        @param deferred: the deferred to callback with the summary
        @param stdout: weither to gather data from stdout
        @param stderr: weither to gather data from stderr
        @param returnCode: weither to collect the return code (exit status)
        @param mergeErr: if True, merge stderr into stdout
        """
        self.deferred = deferred
        if stdout:
            self.bufOut = []
            self.outReceived = lambda data: self.bufOut.append(data)
        if mergeErr:
            self.errReceived = self.outReceived
        elif stderr:
            self.bufErr = []
            self.errReceived = lambda data: self.bufErr.append(data)

    def processEnded(self, reason):
        stdout = ''.join(getattr(self, 'bufOut', []))
        stderr = ''.join(getattr(self, 'bufErr', []))
        returnCode = reason.value.exitCode
        result = (stdout, stderr, returnCode)
        self.deferred.callback(result)
