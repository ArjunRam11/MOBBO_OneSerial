"""
Balance Board Data Visualizer - Fast Real-time
Data format: TIME,F1,F2,F3,F4,COPx,COPy
"""

import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle

class BalanceBoardVisualizer:
    def __init__(self, port, baudrate=115200):
        # Fast serial connection
        self.ser = serial.Serial(port, baudrate, timeout=0)
        self.ser.reset_input_buffer()
        print(f"Connected to {port} at {baudrate} baud\n")

        # Serial buffer
        self.buffer = ""

        # Current data
        self.copx = 0
        self.copy = 0
        self.f1 = 0
        self.f2 = 0
        self.f3 = 0
        self.f4 = 0

        # Trail storage (last 20 COP positions)
        self.trail_x = []
        self.trail_y = []

        self.setup_plot()

    def setup_plot(self):
        """Setup matplotlib figure"""
        self.fig = plt.figure(figsize=(14, 6))

        # COP Board Plot
        self.ax_board = plt.subplot(1, 2, 1)
        self.ax_board.set_title('Center of Pressure', fontsize=14, fontweight='bold')
        self.ax_board.set_xlabel('X (cm)', fontsize=12)
        self.ax_board.set_ylabel('Y (cm)', fontsize=12)

        # Board dimensions: 60cm x 45cm
        w, h = 60, 45
        board_rect = Rectangle((-w/2, -h/2), w, h, linewidth=3,
                              edgecolor='black', facecolor='lightgray', alpha=0.3)
        self.ax_board.add_patch(board_rect)

        self.ax_board.set_xlim(-w/2 - 5, w/2 + 5)
        self.ax_board.set_ylim(-h/2 - 5, h/2 + 5)
        self.ax_board.axhline(0, color='k', linestyle='--', alpha=0.3)
        self.ax_board.axvline(0, color='k', linestyle='--', alpha=0.3)
        self.ax_board.grid(True, alpha=0.3)
        self.ax_board.set_aspect('equal')

        # COP trail line
        self.cop_trail, = self.ax_board.plot([], [], 'b-', alpha=0.5, linewidth=2)

        # COP current point
        self.cop_point = self.ax_board.scatter([0], [0], c='red', s=300,
                                              alpha=0.9, edgecolors='darkred', linewidths=2)
        self.cop_text = self.ax_board.text(0.02, 0.98, '', transform=self.ax_board.transAxes,
                                          fontsize=11, verticalalignment='top',
                                          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # Force Matrix Plot
        self.ax_forces = plt.subplot(1, 2, 2)
        self.ax_forces.set_title('Force Sensors', fontsize=14, fontweight='bold')
        self.ax_forces.set_xlim(0, 2)
        self.ax_forces.set_ylim(0, 2)
        self.ax_forces.set_aspect('equal')
        self.ax_forces.axis('off')

        # 2x2 Force grid: F2 (top-left), F1 (top-right), F3 (bottom-left), F4 (bottom-right)
        positions = [(0, 1, 'F2'), (1, 1, 'F1'), (0, 0, 'F3'), (1, 0, 'F4')]
        colors = ['green', 'red', 'blue', 'magenta']

        self.force_patches = []
        self.force_value_texts = []
        self.force_pct_texts = []

        for i, (x, y, label) in enumerate(positions):
            rect = Rectangle((x + 0.05, y + 0.05), 0.9, 0.9,
                           linewidth=2, edgecolor='black', facecolor=colors[i], alpha=0.3)
            self.ax_forces.add_patch(rect)
            self.force_patches.append(rect)

            self.ax_forces.text(x + 0.5, y + 0.75, label, ha='center', va='center',
                              fontsize=16, fontweight='bold')

            val_text = self.ax_forces.text(x + 0.5, y + 0.5, '0.0 Kg', ha='center', va='center',
                                         fontsize=14, fontweight='bold')
            self.force_value_texts.append(val_text)

            pct_text = self.ax_forces.text(x + 0.5, y + 0.25, '0%', ha='center', va='center',
                                         fontsize=12)
            self.force_pct_texts.append(pct_text)

        self.total_text = self.ax_forces.text(1.0, -0.15, 'Total: 0.0 Kg', ha='center', va='top',
                                             fontsize=14, fontweight='bold',
                                             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

        plt.tight_layout()

    def read_data(self):
        """Read data from serial - fast version"""
        if self.ser.in_waiting > 0:
            chunk = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            self.buffer += chunk

            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                line = line.strip()

                if line and not any(line.startswith(x) for x in ["Setup", "Taring", "Format", "Force", "Calculating"]):
                    parts = line.split(',')
                    if len(parts) == 7:
                        try:
                            self.f1 = float(parts[1])
                            self.f2 = float(parts[2])
                            self.f3 = float(parts[3])
                            self.f4 = float(parts[4])
                            self.copx = float(parts[5])
                            self.copy = float(parts[6])

                            # Update trail (keep last 20 positions)
                            self.trail_x.append(self.copx)
                            self.trail_y.append(self.copy)
                            if len(self.trail_x) > 20:
                                self.trail_x.pop(0)
                                self.trail_y.pop(0)
                        except:
                            pass

    def update(self, frame):
        """Update plots"""
        self.read_data()

        # Update COP trail
        if len(self.trail_x) > 0:
            self.cop_trail.set_data(self.trail_x, self.trail_y)

        # Update COP current point
        self.cop_point.set_offsets([[self.copx, self.copy]])
        self.cop_text.set_text(f'COP: ({self.copx:.1f}, {self.copy:.1f}) cm')

        # Update forces
        forces = [self.f2, self.f1, self.f3, self.f4]
        total = self.f1 + self.f2 + self.f3 + self.f4

        for i, force in enumerate(forces):
            self.force_value_texts[i].set_text(f'{force:.1f} Kg')

            if total > 1.0:
                pct = (abs(force) / abs(total)) * 100
                self.force_pct_texts[i].set_text(f'{pct:.1f}%')
                alpha = min(max(0.3 + (abs(force) / max(abs(total), 1)) * 0.7, 0.3), 1.0)
                self.force_patches[i].set_alpha(alpha)
            else:
                self.force_pct_texts[i].set_text('0%')
                self.force_patches[i].set_alpha(0.3)

        self.total_text.set_text(f'Total: {total:.1f} Kg')

        return []

    def start(self):
        """Start visualization"""
        print("Starting visualization...")
        print("Close the plot window to stop\n")

        anim = FuncAnimation(self.fig, self.update, interval=1, blit=False, cache_frame_data=False)

        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def close(self):
        self.ser.close()
        print("\nSerial connection closed")


def main():
    PORT = 'COM7'

    try:
        visualizer = BalanceBoardVisualizer(PORT)
        visualizer.start()
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {PORT}")
        print(f"Details: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
