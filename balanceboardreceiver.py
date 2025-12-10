"""
Balance Board Data Receiver - Simple Console Output
Data format: TIME,F1,F2,F3,F4,COPx,COPy
"""

import serial
import time

class BalanceBoardReceiver:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=0)
        self.ser.reset_input_buffer()
        print(f"Connected to {port} at {baudrate} baud\n")

    def start(self):
        """Read and print data continuously"""
        buffer = ""

        while True:
            try:
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += chunk

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            print(line, flush=True)

            except KeyboardInterrupt:
                break
            except:
                pass

    def close(self):
        self.ser.close()
        print("\nSerial connection closed")


def main():
    PORT = 'COM7'
    try:
        receiver = BalanceBoardReceiver(PORT)
        receiver.start()
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {PORT}")
        print(f"Details: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            receiver.close()
        except:
            pass


if __name__ == "__main__":
    main()