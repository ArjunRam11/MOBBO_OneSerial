# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Balance Board Data Acquisition and Visualization System** for analyzing Center of Pressure (COP) data from a 4-sensor force plate. The system receives real-time data from an Arduino-based balance board via serial communication and provides both raw console output and real-time visualization.

## Data Format

The Arduino sends CSV data over serial (115200 baud) in this format:
```
TIME,F1,F2,F3,F4,COPx,COPy
```

- **TIME**: Timestamp in seconds
- **F1, F2, F3, F4**: Force sensor readings in Kg (or N, depending on calibration)
- **COPx, COPy**: Center of Pressure coordinates in cm

**Sensor Layout** (2x2 matrix):
```
F2 (top-left)    | F1 (top-right)
F3 (bottom-left) | F4 (bottom-right)
```

**Board Dimensions**: 60cm (width) × 45cm (height)

## Running the Applications

### Console Receiver (Raw Data Output)
```bash
python balanceboardreceiver.py
```
Prints incoming data to console with minimal latency. Default port: COM7

### Real-time Visualizer
```bash
python balanceboardvisualiser.py
```
Shows two plots:
- **Left**: COP position on the balance board with a 20-point trail
- **Right**: 2×2 force matrix with live values, percentages, and color intensity

## Architecture

### Performance-Critical Design

Both components use **identical fast serial reading** optimized for minimal latency:

1. **Zero timeout** (`timeout=0`) - Non-blocking serial reads
2. **Batch reading** - Reads all available bytes at once using `in_waiting`
3. **Buffer management** - Processes complete lines from internal buffer
4. **No delays** - Removed all `time.sleep()` calls
5. **Cleared input buffer** - Starts fresh with `reset_input_buffer()`

### Serial Reading Pattern (Core Architecture)

```python
# Initialize with zero timeout
self.ser = serial.Serial(port, baudrate, timeout=0)
self.ser.reset_input_buffer()
self.buffer = ""

# Fast reading loop
if self.ser.in_waiting > 0:
    chunk = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
    self.buffer += chunk

    while '\n' in self.buffer:
        line, self.buffer = self.buffer.split('\n', 1)
        # Process line...
```

**Critical**: Always use this pattern for serial communication. Do NOT use `readline()` or blocking reads as they introduce 10-100ms latency.

### BalanceBoardReceiver

- **Purpose**: Raw data output to console
- **No buffering**: Prints lines immediately as they arrive
- **Filters**: Skips Arduino setup messages ("Setup", "Taring", "Format", etc.)

### BalanceBoardVisualizer

- **Purpose**: Real-time matplotlib visualization
- **Update interval**: 1ms (fastest possible)
- **Trail**: Maintains last 20 COP positions for movement visualization
- **Force visualization**: Color intensity reflects force magnitude
- **No history buffers**: Only stores current values + 20-point trail

**Visualization details**:
- COP shown as red dot with blue trail line
- Force rectangles change opacity based on load percentage
- Total weight displayed with individual sensor percentages

## Configuration

Both files default to **COM7** at **115200 baud**. Change the `PORT` variable in `main()`:

```python
PORT = 'COM7'  # Windows
# PORT = '/dev/ttyUSB0'  # Linux
# PORT = '/dev/cu.usbserial-*'  # macOS
```

## Dependencies

```bash
pip install pyserial matplotlib
```

- `pyserial`: Serial communication
- `matplotlib`: Visualization (visualizer only)

## Important Development Notes

### When Modifying Serial Communication

- **Never** add `time.sleep()` in the reading loop
- **Never** use `readline()` - it blocks and causes latency
- **Always** check `in_waiting` before reading
- **Always** read all available data at once: `read(in_waiting)`
- **Always** use `timeout=0` for non-blocking reads

### When Adding Visualizations

- Keep update interval at 1ms: `interval=1` in FuncAnimation
- Avoid buffering - update plots directly from current values
- Use `blit=False` and `cache_frame_data=False` for compatibility
- Limit trail/history to essential points (currently 20 for COP trail)

### Board Dimensions

- Width: 60 cm (not 600mm)
- Height: 45 cm (not 450mm)
- Always use cm as the unit for COP coordinates
