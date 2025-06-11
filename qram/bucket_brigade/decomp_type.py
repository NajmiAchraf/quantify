from enum import Enum, auto


class ReverseMoments(Enum):

    NO_REVERSE = auto()

    IN_TO_OUT = auto()

    OUT_TO_IN = auto()


class BucketBrigadeDecompType:
    def __init__(
        self,
        toffoli_decomp_types,
        parallel_toffolis,
        reverse_moments=ReverseMoments.NO_REVERSE,
    ):
        self.dec_fan_out = toffoli_decomp_types[0]
        self.dec_mem_write = toffoli_decomp_types[1]
        self.dec_mem_query = toffoli_decomp_types[2]
        self.dec_fan_in = toffoli_decomp_types[3]
        self.dec_mem_read = toffoli_decomp_types[4]

        # Should the Toffoli decompositions be parallelized?
        self.parallel_toffolis = parallel_toffolis

        # If the FANIN is better in terms of depth than the FANOUT
        # we can reverse the FANIN to FANOUT or vice versa
        self.reverse_moments = reverse_moments

    def get_decomp_types(self):
        """
        Returns all decomposition types used in the circuit.

        Returns:
            List of decomposition types [fan_in, mem_write, mem_read, mem_query, fan_out]
        """
        return [
            self.dec_fan_out,
            self.dec_mem_write,
            self.dec_mem_query,
            self.dec_fan_in,
            self.dec_mem_read,
        ]
