from .version import __version__


def get_version() -> str:
    return __version__


def main():
    print(f"CAN Frame Retransmission Tool v{__version__}")

if __name__ == "__main__":
    main()
