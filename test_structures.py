import pytest
import structures


def test_RGB():
    assert b'\x00\x00\x00' == structures.RGB().bytes
    assert b'\x12\x34\x56' == structures.RGB(0x12, 0x34, 0x56).bytes
    assert b'\xab\xcd\xef' == structures.RGB(b'\xab\xcd\xef').bytes
    assert 'RGB(18, 52, 86)' == str(structures.RGB(0x12, 0x34, 0x56))

    with pytest.raises(ValueError):
        # data not long enough
        structures.RGB(b'\x01').bytes
