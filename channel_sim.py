"""
channel_sim.py — Simulates a low-bitrate, lossy radio link for SwarSetu

For a hackathon demo you want to *show* the bitrate win and *show* the link
being resilient to noise, without needing real SDR hardware. This module:

  1. Chunks the wire-format payload into packets sized for a given bitrate.
  2. Adds artificial latency proportional to bitrate (so a demo can show
     "X seconds to send at 300 bps" vs raw audio streaming).
  3. Optionally drops/corrupts a fraction of packets to simulate a noisy
     link, so you can demonstrate retransmission / error handling.
"""

import math
import random
import time


class LowBitrateChannel:
    def __init__(self, bitrate_bps: int = 300, packet_loss: float = 0.0,
                 simulate_delay: bool = False):
        """
        bitrate_bps: link capacity in bits/second (e.g. 100-2400 for HF/VHF
                     narrowband or satellite store-and-forward links).
        packet_loss: probability (0-1) a given packet is dropped, to
                     simulate a noisy channel.
        simulate_delay: if True, actually sleep to mimic real transmission
                         time (useful for a live demo; disable for tests).
        """
        self.bitrate_bps = bitrate_bps
        self.packet_loss = packet_loss
        self.simulate_delay = simulate_delay

    def transmission_time(self, payload_bits: int) -> float:
        return payload_bits / self.bitrate_bps

    def send(self, wire_str: str, packet_size_bytes: int = 32) -> dict:
        """
        Splits `wire_str` into packets and "transmits" them.
        Returns stats plus the (possibly lossy) received string.
        """
        payload_bytes = wire_str.encode("ascii")
        total_bits = len(payload_bytes) * 8
        est_time = self.transmission_time(total_bits)

        n_packets = math.ceil(len(payload_bytes) / packet_size_bytes)
        received_chunks = []
        dropped = 0

        for i in range(n_packets):
            chunk = payload_bytes[i * packet_size_bytes:(i + 1) * packet_size_bytes]
            if random.random() < self.packet_loss:
                dropped += 1
                continue  # packet lost — in a real system this triggers a NACK/retransmit
            received_chunks.append(chunk)

            if self.simulate_delay:
                time.sleep(len(chunk) * 8 / self.bitrate_bps)

        received_str = b"".join(received_chunks).decode("ascii", errors="ignore")

        return {
            "bitrate_bps": self.bitrate_bps,
            "total_bits": total_bits,
            "estimated_seconds": round(est_time, 3),
            "n_packets": n_packets,
            "packets_dropped": dropped,
            "received_wire": received_str,
            "complete": dropped == 0,
        }


if __name__ == "__main__":
    from compress import compress_text, to_wire_format

    text = "आज मौसम बहुत अच्छा है"
    wire = to_wire_format(compress_text(text, language="hi"))

    for bps in (100, 300, 1200, 2400):
        ch = LowBitrateChannel(bitrate_bps=bps)
        stats = ch.send(wire)
        print(f"{bps:>5} bps -> {stats['estimated_seconds']:.3f}s for "
              f"{stats['total_bits']} bits ({stats['n_packets']} packets)")

    # Compare against raw 16kHz 16-bit PCM audio for the same sentence (~3s speech)
    raw_audio_bits = 16000 * 16 * 3
    print(f"\nEquivalent raw PCM audio (~3s): {raw_audio_bits} bits "
          f"-> {raw_audio_bits/300:.1f}s at 300 bps")
