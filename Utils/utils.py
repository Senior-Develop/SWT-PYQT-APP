# a > b: return 1
# a < b: return -1
# a == b: return 0
def compare_floats(a, b, precision=1e-10):
    diff = float(a) - float(b)
    return 1 if diff > precision else -1 if diff < -precision else 0
