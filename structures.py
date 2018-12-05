
# import struct


class RGB(object):

    def __new__(cls, *args):
        obj = super().__new__(cls)

        if len(args) == 1:
            # constructing from an existing bytes-like array
            if len(args[0]) != 3:
                raise ValueError('RGB bytearrays must be 3 bytes long')
            obj.bytes = bytes(args[0])
        elif len(args) == 3:
            # constructing from raw R,G,B values
            obj.bytes = bytes(args)
        else:
            # otherwise, just an empty pixel
            obj.bytes = bytes(3)
        return obj

    def __str__(self):
        fqname = self.__class__.__name__
        return "{}({}, {}, {})".format(
            fqname,
            self.bytes[0], self.bytes[1], self.bytes[2]
        )
