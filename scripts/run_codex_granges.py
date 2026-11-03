"""Run Codex against a frozen Betaforge evidence packet."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from betaforge.codex_runner import main

if __name__=='__main__':
    sys.exit(main())
