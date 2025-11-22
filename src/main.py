import math
import random
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


from agents.vtuber_agent import VtuberAgent

if __name__ == "__main__":
    vtuber = VtuberAgent()
    vtuber.start_daily_loop()