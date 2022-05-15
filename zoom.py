from os import sep
import mido


def build_sysex_for_summary(bank=1, patch=0):
    sysex_part1 = "f0 52 00 6e 46 00" + " "
    sysex_part2 = " " + "00 f7"
    sysex_string = sysex_part1 + \
        "00 0{} 00 0{}".format(bank - 1, patch) + sysex_part2
    sysex_bytes = [int('0x'+byte, 16) for byte in sysex_string.split()]
    sysex_mido = mido.Message(type='sysex', data=sysex_bytes[1:-1])
    return sysex_mido


def get_name_from_sysex(res):
    name_idx = [43, 44, 46, 47, 48, 49, 50, 51, 52, 54]
    name = ""
    h_name = ""
    bytes = [byte for byte in res.hex().split()]
    for i, byte in enumerate(bytes):
        char = chr(int('0x'+byte, 16))
        if i in name_idx:
            name += char
            h_name += byte
    return name + h_name


print(mido.get_output_names())
print(mido.get_input_names())
midi_in = mido.open_input("ZOOM G Series 0")
midi_out = mido.open_output("ZOOM G Series 1")

for bank in range(1, 6):
    for patch in range(0, 10):
        req = build_sysex_for_summary(bank, patch)
        midi_out.send(req)
        res = midi_in.receive()
        name = get_name_from_sysex(res)
        print(str(bank) + str(patch), name)

midi_in.close()
midi_out.close()
