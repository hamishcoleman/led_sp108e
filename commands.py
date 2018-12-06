"""Definitions for the various commands acceped by the controller"""

# The list of commands was originally taken from github:
#       https://github.com/Spled/spled.github.io/issues/1
# where alorbach had extracted it from the LEDshopp android app

CMD_CUSTOM_EFFECT = 0x02
CMD_SPEED = 0x03
CMD_MODE_AUTO = 0x06
CMD_CUSTOM_DELETE = 0x07
CMD_WHITE_BRIGHTNESS = 0x08
CMD_SYNC = 0x10
CMD_SET_DEVICE_NAME = 0x14
CMD_SET_DEVICE_PASSWORD = 0x16
CMD_SET_IC_MODEL = 0x1c
CMD_GET_RECORD_NUM = 0x20
CMD_COLOR = 0x22
CMD_CUSTOM_PREVIEW = 0x24
CMD_CHANGE_PAGE = 0x25
CMD_BRIGHTNESS = 0x2a
CMD_MODE_CHANGE = 0x2c
CMD_DOT_COUNT = 0x2d
CMD_SEC_COUNT = 0x2e
CMD_CHECK_DEVICE_IS_COOL = 0x2f
CMD_SET_RGB_SEQ = 0x3c
CMD_CUSTOM_RECODE = 0x4c
CMD_GET_DEVICE_NAME = 0x77
CMD_SET_DEVICE_TO_AP_MODE = 0x88
CMD_TOGGLE_LAMP = 0xaa
CMD_CHECK_DEVICE = 0xd5

# if we know this command, record if we expect a response
response = {
    CMD_BRIGHTNESS: False,
    CMD_CHECK_DEVICE: True,
    CMD_COLOR: False,
    CMD_DOT_COUNT: False,
    CMD_GET_DEVICE_NAME: True,
    CMD_MODE_AUTO: False,
    CMD_MODE_CHANGE: False,
    CMD_SEC_COUNT: False,
    CMD_SET_IC_MODEL: False,
    CMD_SPEED: False,
    CMD_SYNC: True,
}

CMD_FRAME_START = 0x38
CMD_FRAME_END = 0x83

# These modes all have a single color, set by CMD_COLOR
MODE_METEOR = 205
MODE_BREATHING = 206
MODE_STACK = 207
MODE_FLOW = 208
MODE_WAVE = 209
MODE_FLASH = 210
MODE_STATIC = 211
MODE_CATCHUP = 212
MODE_CUSTOM_EFFECT = 219

# Auto sequence through all the multi-color modes
MODE_AUTO = 0xfc

# TODO
#IC_MODEL_xxx = yyy # noqa


def frame(cmd, data):
    """Return the bytes needed for this command packet"""
    if data is None:
        data = b'\x00\x00\x00'
    elif len(data) < 3:
        data += bytes(3-len(data))
    elif len(data) > 3:
        raise ValueError("data length max is 3")

    return bytes([CMD_FRAME_START]) + data + bytes([cmd, CMD_FRAME_END])


def _call0(cmd):
    """Generic command packet with no parameters"""
    return frame(cmd, None)


def _call1(cmd, param1):
    """Generic command packet with one parameter"""
    return frame(cmd, bytes([param1]))


def speed(speed):
    """Set the speed of the programmed effect"""
    return _call1(CMD_SPEED, speed)


def get_device_name():
    """Request the current device name"""
    return _call0(CMD_GET_DEVICE_NAME)


def check_device(challenge):
    """Request a device check"""
    return frame(CMD_CHECK_DEVICE, challenge.to_bytes(3, 'little'))


def mode_change(mode):
    """Request a display pattern mode change"""
    # I dont know why they didnt let you simply MODE_CHANGE to MODE_AUTO
    if mode == MODE_AUTO:
        return _call0(CMD_MODE_AUTO)

    # TODO
    # - the screen freezes when given an invalid mode, maybe validate here?

    return _call1(CMD_MODE_CHANGE, mode)


def sync():
    """Request a status response"""
    return _call0(CMD_SYNC)


def set_ic_model(model):
    """Set which LED protocol is needed"""
    # TODO
    # - the screen freezes when given an invalid model, maybe validate here?

    return _call1(CMD_SET_IC_MODEL, model)


def color(rgb):
    """Set the color to be used for the single-color patterns"""
    return frame(CMD_COLOR, rgb.bytes)


def brightness(value):
    """Set the color to be used for the single-color patterns"""
    return _call1(CMD_BRIGHTNESS, value)


def dot_count(value):
    """configure the number of pixels in each segment"""

    # TODO
    # - range is 1 - 0x697, outside of which it transparently resets to 0x32
    # - simple testing suggests that 300 pixels is the max
    # should we check value here?

    return frame(CMD_DOT_COUNT, value.to_bytes(2, 'little'))


def sec_count(value):
    """configure the number of sections in the display"""
    return frame(CMD_SEC_COUNT, value.to_bytes(2, 'little'))
