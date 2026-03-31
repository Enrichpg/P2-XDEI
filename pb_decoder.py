import sys

def decode_varint(data, pos):
    result = 0
    shift = 0
    while True:
        try:
            b = data[pos]
        except IndexError:
            return None, pos
        result |= (b & 0x7f) << shift
        pos += 1
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 64:
            return None, pos

def parse_pb(data):
    pos = 0
    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        if tag is None: break
        
        wire_type = tag & 0x7
        field_num = tag >> 3
        
        if wire_type == 0: # Varint
            val, pos = decode_varint(data, pos)
        elif wire_type == 1: # 64-bit
            pos += 8
        elif wire_type == 2: # Length-delimited (string, bytes, submessage)
            length, pos = decode_varint(data, pos)
            if length is None: break
            content = data[pos:pos+length]
            pos += length
            
            # Try to see if it's a UTF-8 string
            try:
                s = content.decode('utf-8')
                if any(c.isprintable() for c in s) and len(s) > 3:
                   print(f"[{field_num}] STRING: {s}")
                else:
                    # Might be a submessage, try parsing recursively?
                    # For now just skip
                    pass
            except UnicodeDecodeError:
                pass
        elif wire_type == 5: # 32-bit
            pos += 4
        else:
            # Unknown wire type, might be corrupted or not PB
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pb_decoder.py <file.pb>")
        sys.exit(1)
        
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    
    parse_pb(data)
