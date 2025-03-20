import argparse as ap

p=ap.ArgumentParser()
_=p.add_argument('-a', nargs='*')
print(set(p.parse_args().a))