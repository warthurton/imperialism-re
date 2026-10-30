"""Show or set the name of an Imperialism save (.imp): a 32-byte NUL-padded text field at offset 12 (max 31 characters).
Usage: python -I name_save.py <file.imp> ["new name"]"""
import sys
p = sys.argv[1]
d = bytearray(open(p, 'rb').read())
assert d[:4] == b'IBMA', 'not an Imperialism save'
print('name:', bytes(d[12:44]).split(b'\0')[0].decode('latin-1'))
if len(sys.argv) > 2:
    n = sys.argv[2].encode('latin-1')
    assert len(n) <= 31, 'name too long (max 31 characters)'
    d[12:44] = n + b'\0' * (32 - len(n))
    open(p, 'wb').write(d)
    print('now :', sys.argv[2])
