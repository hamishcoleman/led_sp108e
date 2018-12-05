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
    CMD_SPEED: False,
}

CMD_FRAME_START = 0x38
CMD_FRAME_END = 0x83


def frame(cmd, data):
    """Return the bytes needed for this command packet"""
    if data is None:
        data = b'\x00\x00\x00'
    elif len(data) < 3:
        data += bytes(3-len(data))
    elif len(data) > 3:
        raise ValueError("data length max is 3")

    return bytes([CMD_FRAME_START]) + data + bytes([cmd, CMD_FRAME_END])
