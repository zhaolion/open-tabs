"""
UID generation utilities using Snowflake ID + Base62 encoding.

Generates unique, URL-safe identifiers for external use.
"""

import threading
import time

# Base62 character set (0-9, A-Z, a-z)
BASE62_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class SnowflakeIDGenerator:
    """
    Snowflake ID generator.

    ID structure (64 bits):
    - 1 bit: sign (always 0)
    - 41 bits: timestamp (milliseconds since epoch)
    - 5 bits: datacenter ID (0-31)
    - 5 bits: machine ID (0-31)
    - 12 bits: sequence number (0-4095)
    """

    def __init__(self, machine_id: int = 1, datacenter_id: int = 1):
        """
        Initialize the generator.

        Args:
            machine_id: Machine ID (0-31)
            datacenter_id: Datacenter ID (0-31)
        """
        self.machine_id = machine_id & 0x1F  # 5 bits max
        self.datacenter_id = datacenter_id & 0x1F  # 5 bits max
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

        # Epoch: 2024-01-01 00:00:00 UTC
        self.epoch = 1704067200000

    def _current_millis(self) -> int:
        """Get current time in milliseconds."""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """Wait until the next millisecond."""
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp

    def generate(self) -> int:
        """
        Generate a new Snowflake ID.

        Returns:
            A unique 64-bit integer ID.

        Raises:
            RuntimeError: If clock moves backwards.
        """
        with self._lock:
            timestamp = self._current_millis()

            if timestamp < self.last_timestamp:
                raise RuntimeError(
                    f"Clock moved backwards. Refusing to generate ID for "
                    f"{self.last_timestamp - timestamp} milliseconds"
                )

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits max
                if self.sequence == 0:
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Assemble the ID
            snowflake_id = (
                ((timestamp - self.epoch) << 22)
                | (self.datacenter_id << 17)
                | (self.machine_id << 12)
                | self.sequence
            )
            return snowflake_id


def encode_base62(num: int) -> str:
    """
    Encode a number to Base62 string.

    Args:
        num: The number to encode.

    Returns:
        Base62 encoded string.
    """
    if num == 0:
        return BASE62_CHARS[0]

    result = []
    while num > 0:
        result.append(BASE62_CHARS[num % 62])
        num //= 62
    return "".join(reversed(result))


def decode_base62(s: str) -> int:
    """
    Decode a Base62 string to number.

    Args:
        s: The Base62 string to decode.

    Returns:
        The decoded number.

    Raises:
        ValueError: If string contains invalid characters.
    """
    result = 0
    for char in s:
        idx = BASE62_CHARS.find(char)
        if idx == -1:
            raise ValueError(f"Invalid Base62 character: {char}")
        result = result * 62 + idx
    return result


# Global generator instance (lazy initialization)
_generator: SnowflakeIDGenerator | None = None
_generator_lock = threading.Lock()


def _get_generator() -> SnowflakeIDGenerator:
    """Get or create the global generator instance."""
    global _generator
    if _generator is None:
        with _generator_lock:
            if _generator is None:
                _generator = SnowflakeIDGenerator()
    return _generator


def generate_uid() -> str:
    """
    Generate a unique user ID.

    Returns:
        A unique Base62 encoded string (typically 11-12 characters).

    Example:
        >>> uid = generate_uid()
        >>> print(uid)  # e.g., "1LY7VK9h7J1"
    """
    generator = _get_generator()
    snowflake_id = generator.generate()
    return encode_base62(snowflake_id)


def init_generator(machine_id: int = 1, datacenter_id: int = 1) -> None:
    """
    Initialize the global generator with custom IDs.

    Should be called at application startup if custom IDs are needed.

    Args:
        machine_id: Machine ID (0-31)
        datacenter_id: Datacenter ID (0-31)
    """
    global _generator
    with _generator_lock:
        _generator = SnowflakeIDGenerator(
            machine_id=machine_id, datacenter_id=datacenter_id
        )
