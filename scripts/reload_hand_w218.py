"""Select the actual loading hand; existing magazine/shell routes default left."""
import math

def side(reload):
    value = reload.get('hand', 'left')
    if value not in ('left', 'right'):
        raise ValueError('Reload hand must be left or right')
    return value

def attached_translation_shift(reload, palms, target, weight, contexts):
    """Keep the moving part's calibrated contact at the chosen source palm.

    Weight zero releases the payload back to its authored seated trajectory.
    Neither the source palm nor the arm length is moved to hide a mismatch.
    """
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError('Reload attachment weight must be finite in0..1')
    selected = palms[side(reload)]
    return {ctx: [(selected[ctx]['translation'][i] - target[ctx]['translation'][i]) * weight
                  for i in range(3)] for ctx in contexts}
