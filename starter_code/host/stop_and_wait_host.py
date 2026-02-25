from abc import ABC

from host.host import Host
from network.network_interface import NetworkInterface
from network.packet import Packet
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator

"""
This host implements the stop and wait protocol. Here the host only
sends one packet in return of an acknowledgement.
"""


class StopAndWaitHost(Host, ABC):

    def __init__(self, clock: Clock, network_interface: NetworkInterface, timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock

        #  The stateful information you might need to track the progress of this protocol as packets are
        #  sent and received.

        self.last_transmitted_sequence_number: int | None = None
        self.inflight_packet: Packet | None = None
        self.last_acked_sequence_number: int | None = None
        self.inflight_timeout: int | None = None

    ## Helper function (you might need it in Step 3)
    def advance_sequence_number(self) -> int:
        if self.last_transmitted_sequence_number is None:
            self.last_transmitted_sequence_number = 0
        else:
            self.last_transmitted_sequence_number += 1
        return self.last_transmitted_sequence_number

    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered. inflight_packet and last_transmitted_sequence_number might need update
        #  - Remember the acked packet also gives as a fresh RTT sample.
        #  REPLACE the pass with your code
        packets_received = self.network_interface.receive_all()
        for packet in packets_received:
            # Only process ACKs
            if not packet.ack_flag:
                continue

            # RTT sample: current time - the timestamp when the packet was sent
            rtt = current_time - packet.sent_timestamp

            # If this ack corresponds to our inflight packet, mark it delivered
            if self.inflight_packet is not None and packet.sequence_number == self.inflight_packet.sequence_number:
                self.last_acked_sequence_number = packet.sequence_number
                # Clear inflight state
                self.inflight_packet = None
                self.inflight_timeout = None

            # Update timeout estimator with the RTT sample
            self.timeout_calculator.add_data_point(rtt)

        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if the inflight message's timeout has already passed.
        #  - If the packet did time out, construct a new packet and transmit
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet
        #  REPLACE the pass with your code
        # Retry if inflight packet timed out
        if self.inflight_packet is not None and self.inflight_timeout is not None and self.inflight_timeout <= current_time:
            # Retransmit packet with same sequence number
            retransmit_pkt = Packet(
                sent_timestamp=current_time,
                sequence_number=self.inflight_packet.sequence_number,
                retransmission_flag=True
            )
            print(f"Tick {current_time}: Retransmitting packet seq={retransmit_pkt.sequence_number} retransmit={retransmit_pkt.retransmission_flag}")
            self.network_interface.transmit(retransmit_pkt)
            # Track the retransmitted packet as inflight and set new timeout
            self.inflight_packet = retransmit_pkt
            self.inflight_timeout = current_time + self.timeout_calculator.timeout()
        
        # TODO: STEP 3 - Transmit new messages 
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - If you don't have a message inflight, we should send the next message
        #  - Construct and transmit the packet
        #      - The packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet
        #  REPLACE the pass with your code
        # If no packet is inflight, send the next new packet
        if self.inflight_packet is None:
            seq = self.advance_sequence_number()
            pkt = Packet(sent_timestamp=current_time, sequence_number=seq, retransmission_flag=False)
            print(f"Tick {current_time}: Sending packet seq={seq} retransmit={pkt.retransmission_flag}")
            self.network_interface.transmit(pkt)
            self.inflight_packet = pkt
            self.inflight_timeout = current_time + self.timeout_calculator.timeout()

        # STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed

        return self.last_acked_sequence_number
