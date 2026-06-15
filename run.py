import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    import asyncio
    from main import main
    asyncio.run(main())
