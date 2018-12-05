import pytest
import commands


def test_frame():
    with pytest.raises(ValueError):
        # data too long
        commands.frame(4, b'\x01\x02\x03\x04')

    assert b'\x38\x00\x00\x00\x7f\x83' == commands.frame(0x7f, None)
    assert b'\x38\x80\x00\x00\x0f\x83' == commands.frame(0xf, b'\x80')
    assert b'\x38\x01\x20\x44\x01\x83' == commands.frame(1, b'\x01\x20\x44')
