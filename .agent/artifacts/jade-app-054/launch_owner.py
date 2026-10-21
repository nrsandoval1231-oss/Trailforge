from pathlib import Path
import sys
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'src'))
from athena_procurement_arena.operator import main
main(['--data', str(root / '.trailforge-operator.sqlite3'), '--port', '8766'])
