import sys
from tutorial_lib import Deck
import slides_a, slides_b, slides_c, slides_svc

# service explainers go right after the services overview (6th slide)
ALL = slides_a.S[:6] + slides_svc.S + slides_a.S[6:] + slides_b.S + slides_c.S
out = sys.argv[1] if len(sys.argv) > 1 else "Daily-Briefing-Agent-Tutorial.pdf"
d = Deck(out, len(ALL), "Automated Daily Briefing AI Agent | Build, Run & Deploy Tutorial")
for f in ALL:
    try:
        f(d)
    except Exception as e:
        print("ERROR in", f.__name__, "->", e); raise
d.save()
print("wrote", out, len(ALL), "slides")
