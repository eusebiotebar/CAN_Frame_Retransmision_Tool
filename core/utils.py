def format_can_frame(frame: dict) -> str:
    frame_id = frame.get("id")
    data = frame.get("data", b"")
    hex_data = ' '.join(f"{b:02X}" for b in data)
    return f"ID=0x{frame_id:X} DATA={hex_data}"
