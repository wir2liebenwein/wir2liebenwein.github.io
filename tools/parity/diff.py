# Compares two screenshot folders and lists every image with changed pixels.
#   python3 tools/parity/diff.py <baseline_dir> <current_dir> <diff_dir>
# Writes a red-on-grey diff image per changed shot. Exit code 1 if anything changed.
import os, sys
import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), dtype=np.int16)


def main(a_dir, b_dir, d_dir):
    os.makedirs(d_dir, exist_ok=True)
    changed = 0
    names = sorted(set(os.listdir(a_dir)) | set(os.listdir(b_dir)))
    for n in names:
        if not n.endswith('.png'):
            continue
        pa, pb = os.path.join(a_dir, n), os.path.join(b_dir, n)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print(f'MISSING {n}  ({"current" if os.path.exists(pa) else "baseline"})'); changed += 1; continue
        A, B = load(pa), load(pb)
        if A.shape != B.shape:
            print(f'SIZE  {n}  {A.shape[1]}x{A.shape[0]} -> {B.shape[1]}x{B.shape[0]}'); changed += 1
            h = min(A.shape[0], B.shape[0]); A, B = A[:h], B[:h]
        mask = np.abs(A - B).max(axis=2) > 0
        if mask.any():
            ys, xs = np.nonzero(mask)
            print(f'DIFF  {n}  {int(mask.sum())} px, max delta {int(np.abs(A - B).max())}, '
                  f'box x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()}')
            img = (B.mean(axis=2) * 0.35 + 160).astype(np.uint8)
            out = np.stack([img, img, img], axis=2)
            out[mask] = (255, 0, 0)
            Image.fromarray(out).save(os.path.join(d_dir, n))
            changed += 1 if A.shape == B.shape else 0
    print('changed:', changed)
    return 1 if changed else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:4]))
