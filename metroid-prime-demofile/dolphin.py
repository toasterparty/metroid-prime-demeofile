import math

import dolphin_memory_engine

dolphin = dolphin_memory_engine

def connect():
    dolphin.un_hook()
    dolphin.hook()

    if not dolphin.is_hooked():
        raise Exception("Unable to connect to Dolphin")

def disconnect():
    dolphin.un_hook()

def _check_is_hooked():
    try:
        if len(dolphin.read_bytes(0x0, 4)) != 4:
            raise RuntimeError("Dolphin hook didn't read the correct byte count")
    except RuntimeError as e:
        dolphin.un_hook()

def is_connected() -> bool:
    if dolphin.is_hooked():
        _check_is_hooked()

    return dolphin.is_hooked()

def _deref(ptr, offset):
    addr = dolphin.read_word(ptr)
    return addr + offset

def _read_time():
    addr = _deref(0x804578CC, 0xA0)
    return dolphin.read_double(addr)

def _cplayer_helper(offset):
    addr = _deref(0x80458350, offset)
    return dolphin.read_float(addr)

def _read_pos():
    x = _cplayer_helper(0x40)
    y = _cplayer_helper(0x50)
    z = _cplayer_helper(0x60)
    return (x, y, z)

def _read_rot():
    x = _cplayer_helper(0x500)
    y = _cplayer_helper(0x510)

    rot_rad = math.atan2(y, x)
    rot_deg = math.degrees(rot_rad)
    rot_deg += 270
    rot_deg %= 360
    return rot_deg

def get_room():
    if not is_connected():
        raise Exception("Connection lost")

    # world_ptr = &g_stateManager.world
    world_addr = dolphin.read_word(0x8045A1A8 + 0x850)
    
    # world_ptr->mlvl
    mlvl_id = dolphin.read_word(world_addr + 0x8)
    
    # world_ptr->area_idx
    room_idx = dolphin.read_word(world_addr + 0x68)

    return (mlvl_id, room_idx)

def take_sample():
    if not is_connected():
        raise Exception("Connection lost")

    time = _read_time()
    pos = _read_pos()
    rot = _read_rot()

    if (time < 0.1) or abs(sum(pos)) < 0.01:
        raise Exception("Unable to read memory")

    return (time, pos, rot)
