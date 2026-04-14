"""Compile .po files to .mo without needing GNU gettext."""
import struct
import re


def unescape(s):
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            c = s[i + 1]
            if c == 'n':
                result.append('\n')
            elif c == 't':
                result.append('\t')
            elif c == '"':
                result.append('"')
            elif c == '\\':
                result.append('\\')
            else:
                result.append(c)
            i += 2
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)


def parse_po(po_path):
    with open(po_path, encoding='utf-8') as f:
        content = f.read()

    messages = {}
    # Match msgid ... msgstr ... blocks (single or multi-line)
    block_re = re.compile(
        r'msgid\s+((?:"[^"]*"\s*)+)\s*msgstr\s+((?:"[^"]*"\s*)+)',
        re.MULTILINE
    )
    str_re = re.compile(r'"([^"]*)"')

    for m in block_re.finditer(content):
        raw_id  = ''.join(str_re.findall(m.group(1)))
        raw_str = ''.join(str_re.findall(m.group(2)))
        msgid  = unescape(raw_id)
        msgstr = unescape(raw_str)
        if msgstr:  # skip untranslated
            messages[msgid] = msgstr

    return messages


def compile_mo(messages, mo_path):
    keys   = sorted(messages.keys())
    values = [messages[k] for k in keys]
    n      = len(keys)

    kenc = [k.encode('utf-8') for k in keys]
    venc = [v.encode('utf-8') for v in values]

    header_size = 28
    ktable_size = 8 * n
    vtable_size = 8 * n

    kdata = b'\x00'.join(kenc) + (b'\x00' if kenc else b'')
    vdata = b'\x00'.join(venc) + (b'\x00' if venc else b'')

    kstring_base = header_size + ktable_size + vtable_size
    vstring_base = kstring_base + len(kdata)

    koffsets = []
    pos = kstring_base
    for k in kenc:
        koffsets.append((len(k), pos))
        pos += len(k) + 1

    voffsets = []
    pos = vstring_base
    for v in venc:
        voffsets.append((len(v), pos))
        pos += len(v) + 1

    output = struct.pack('<IIIIIII',
        0x950412de,  # magic
        0,           # revision
        n,           # num strings
        header_size,                  # offset of key table
        header_size + ktable_size,    # offset of value table
        0, 0                          # hash table (unused)
    )
    for length, offset in koffsets:
        output += struct.pack('<II', length, offset)
    for length, offset in voffsets:
        output += struct.pack('<II', length, offset)
    output += kdata
    output += vdata

    with open(mo_path, 'wb') as f:
        f.write(output)

    print(f'  Compiled {n} messages  ->  {mo_path}')


if __name__ == '__main__':
    import os
    for lang in ('en', 'ar'):
        po = os.path.join('locale', lang, 'LC_MESSAGES', 'django.po')
        mo = os.path.join('locale', lang, 'LC_MESSAGES', 'django.mo')
        if os.path.exists(po):
            msgs = parse_po(po)
            compile_mo(msgs, mo)
            print(f'  [{lang}] done')
        else:
            print(f'  [{lang}] .po not found, skipping')
