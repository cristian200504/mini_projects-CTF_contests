"""Render AS1130 PWM traffic from the decoded I2C packet list (viewer export)."""

from pathlib import Path
import re


ANODES = [[8,1,0,1,1,9,2,2,5,2,6,5,9,6,5,1,5],[1,0,0,0,9,1,6,6,2,6,7,6,7,9,0,6,6],[0,0,9,1,8,1,2,3,2,2,3,3,3,9,0,2,3],[4,4,5,8,3,1,6,4,2,3,9,4,3,3,0,3,8],[8,6,8,8,0,8,7,3,8,1,9,9,2,8,5,8,4],[5,5,9,0,4,5,6,3,4,4,1,5,5,4,2,4,4],[5,8,9,7,0,7,7,7,7,7,1,6,7,2,7,7,4]]
CATHODES = [[11,11,0,2,1,2,10,11,2,6,11,0,6,10,1,6,3],[0,11,1,6,0,7,6,7,7,2,11,3,10,7,7,0,1],[2,10,1,10,1,3,1,6,2,3,11,7,10,3,3,0,8],[11,6,4,4,1,4,4,7,4,2,4,10,3,4,4,0,9],[8,9,6,0,9,7,9,9,3,9,9,10,9,2,9,5,9],[11,10,5,5,0,7,5,5,3,1,5,6,5,2,5,5,4],[8,10,8,0,8,7,8,5,3,1,8,8,6,8,2,4,8]]


def index(anode, cathode):
    # AS1130's first LED digit selects the cathode/CS segment. Within that
    # segment the second digit selects the anode, skipping the same CS line.
    # (For example CS0 is the cathode for LEDs 00..0A.)
    return cathode * 11 + anode - (anode > cathode)


def grid(pwm):
    return tuple(
        ''.join('#' if pwm[index(a, c)] else '.' for a, c in zip(ar, cr))
        for ar, cr in zip(ANODES, CATHODES)
    )


def main():
    root = Path(r'C:\Users\santey\Desktop\NNS CTF\cheese')
    input_path = root / 'i2c_packets.txt'
    output_path = root / 'viewer_display_frames.txt'
    frames = []
    for line in input_path.read_text().splitlines():
        fields = line.split('  ', 2)
        if len(fields) < 3:
            continue
        number = int(fields[0])
        data = [int(x, 16) for x in re.findall(r'\b[0-9A-F]{2}\b', fields[2])]
        if len(data) == 134 and data[:2] == [0x60, 0x18]:
            frames.append((number, grid(data[2:])))
    changes = []
    prev = None
    for frame in frames:
        if frame[1] != prev:
            changes.append(frame)
            prev = frame[1]
    with output_path.open('w', newline='\n') as f:
        f.write(f'{len(frames)} writes, {len(changes)} distinct consecutive states\n\n')
        for ordinal, (message, pixels) in enumerate(changes):
            f.write(f'FRAME {ordinal} I2C={message}\n')
            f.write('\n'.join(pixels))
            f.write('\n\n')
    print(f'{len(frames)} writes, {len(changes)} changes -> {output_path}')
    for ordinal, (message, pixels) in enumerate(changes[:35]):
        print(f'FRAME {ordinal} I2C={message}')
        print('\n'.join(pixels))


if __name__ == '__main__':
    main()
