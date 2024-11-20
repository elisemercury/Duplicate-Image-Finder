import signal


class GracefulWorker:
    interrupts: int = 0
    interrupt_threshold: int = 2
    identifier: int

    run: bool = True

    def __init__(self, identifier: int):
        """
        Attach handlers for interrupts
        :param identifier: identifier of this class
        """
        self.identifier = identifier

    def register_interrupts(self):
        """
        Register the interrupts
        """
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def handle_interrupt(self, signal_type:int, frame: object):
        """
        Handle the interrupt if more than `interrupt_threshold` interrupts are received, exit immediately, otherwise
        wait for the stop to come through the parent process.
        :return:
        """
        print(f"{self.identifier:03} - Interrupt")
        self.run = False
        if self.interrupts >= self.interrupt_threshold:
            print(f"{self.identifier:03} - Exiting immediately")
            exit(1)

        self.interrupts += 1