"""CLI launcher for CAN_ID_Reframe (new name at v0.2.0).

Retains same behavior as legacy can_retransmit_cli entry.
"""

from core.main import main

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
