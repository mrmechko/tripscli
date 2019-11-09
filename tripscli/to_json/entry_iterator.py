from itertools import islice

def _fast_select_wrapper(sequence, selected):
    i = 0
    selected = sorted(selected)
    for elt in sequence:
        if selected and i == selected[0]:
            selected = selected[1::]
            yield elt
        i += 1

def get_entries(start=0, stop=-1, selected=None):
    if stop < 0:
        stop = None
    if selected:
        return lambda x: _fast_select_wrapper(islice(x, start, stop), selected)
    return lambda x: islice(x, start, stop)

simple_it=get_entries(start=0)


