"""Annotate COM calls on SDK objects with the SDK method name (vtable order read from the SDK header, not guessed).

Used by split_source.py for the 'directplay' group: the game's wrapper object keeps its IDirectPlay2A pointer at +4 (param_1[1]),
so calls like (**(code **)(*(int *)param_1[1] + 0x60))(...) are IDirectPlay2::Open. Order comes from dplay.h (IDirectPlay2).
"""
import re

DP2 = ['QueryInterface', 'AddRef', 'Release', 'AddPlayerToGroup', 'Close', 'CreateGroup', 'CreatePlayer',
       'DeletePlayerFromGroup', 'DestroyGroup', 'DestroyPlayer', 'EnumGroupPlayers', 'EnumGroups', 'EnumPlayers',
       'EnumSessions', 'GetCaps', 'GetGroupData', 'GetGroupName', 'GetMessageCount', 'GetPlayerAddress', 'GetPlayerCaps',
       'GetPlayerData', 'GetPlayerName', 'GetSessionDesc', 'Initialize', 'Open', 'Receive', 'Send', 'SetGroupData',
       'SetGroupName', 'SetPlayerData', 'SetPlayerName', 'SetSessionDesc']

ASSIGN = re.compile(r'\s*(\w+) = \(int \*\)(?:param_1\[1\]|\*\(int \*\)\(param_1 \+ 4\))')
CALL = re.compile(r'\(\*\*\(code \*\*\)\((?:\*\(int \*\)param_1\[1\]|\*\*\(int \*\*\)\(param_1 \+ 4\)|\*(\w+)) \+ (0x[0-9a-f]+|\d+)\)\)')


def annotate_dp(text):
    out, com = [], set()
    for ln in text.split('\n'):
        m = ASSIGN.match(ln)
        if m:
            com.add(m[1])
        for m in CALL.finditer(ln):
            if m[1] is None or m[1] in com:
                k = int(m[2], 0) // 4
                if 0 <= k < len(DP2):
                    ln += '  /* IDirectPlay2::%s */' % DP2[k]
        out.append(ln)
    return '\n'.join(out)
