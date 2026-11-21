"""Az adatokra épülő TikZ/pgfplots-ábrák adatfájljainak előállítása (figures/data/*.dat)."""
from pathlib import Path
import numpy as np
import pandas as pd
import adatbanyaszat as ab

D = Path(__file__).resolve().parent / "data"
D.mkdir(exist_ok=True)

def fig03_hampel():
    m = ab.load_plant().measurements.set_index("ido")
    s = m.T_reaktor
    up = s[(s > 120)]
    t0 = up.index[2] - pd.Timedelta(hours=8)
    w = s[t0:t0 + pd.Timedelta(hours=16)].interpolate()
    med = w.rolling(9, center=True, min_periods=1).median()
    mad = (w - med).abs().rolling(9, center=True, min_periods=1).median() * 1.4826
    mad = mad.clip(lower=0.1)
    out = pd.DataFrame({"t": (w.index - w.index[0]) / pd.Timedelta(hours=1), "x": w.values,
                        "med": med.values, "lo": (med - 3 * mad).values, "hi": (med + 3 * mad).values})
    out["flag"] = ((w - med).abs() > 3 * mad).astype(int).values
    out.to_csv(D / "03-hampel.dat", sep=" ", index=False, float_format="%.4f")

if __name__ == "__main__":
    fig03_hampel()
    print("ok")


def fig04_pca():
    rng = np.random.default_rng(4)
    C = np.array([[3.0, 1.6], [1.6, 1.4]])
    X = rng.multivariate_normal([0, 0], C, size=60)
    Xc = X - X.mean(0)
    lam, V = np.linalg.eigh(np.cov(Xc.T))
    order = lam.argsort()[::-1]; lam, V = lam[order], V[:, order]
    if V[0, 0] < 0: V[:, 0] *= -1
    if V[1, 1] < 0: V[:, 1] *= -1
    pd.DataFrame(Xc, columns=["x", "y"]).to_csv(D / "04-pca-pontok.dat", sep=" ", index=False, float_format="%.4f")
    t1 = Xc @ V[:, 0]; res = Xc @ V[:, 1]
    cand = np.where((t1 > 0.8) & (t1 < 2.2))[0]
    k = int(cand[np.argmax(np.abs(res[cand]))])  # egy kiemelt pont nagy maradékkal
    p = Xc[k]; proj = (p @ V[:, 0]) * V[:, 0]
    with open(D / "04-pca-param.tex", "w") as f:
        f.write("\\def\\vax{%.4f}\\def\\vay{%.4f}\\def\\vbx{%.4f}\\def\\vby{%.4f}\n" % (V[0,0], V[1,0], V[0,1], V[1,1]))
        f.write("\\def\\la{%.4f}\\def\\lb{%.4f}\n" % (np.sqrt(lam[0]), np.sqrt(lam[1])))
        f.write("\\def\\px{%.4f}\\def\\py{%.4f}\\def\\qx{%.4f}\\def\\qy{%.4f}\n" % (p[0], p[1], proj[0], proj[1]))


def fig04_kde():
    pts = np.array([1.0, 1.8, 2.2, 3.9, 4.3, 6.5])
    h = 0.6
    xs = np.linspace(-1, 8.5, 300)
    K = np.exp(-0.5 * ((xs[:, None] - pts[None, :]) / h) ** 2) / (np.sqrt(2 * np.pi) * h) / len(pts)
    out = pd.DataFrame({"x": xs, "f": K.sum(1)})
    for i in range(len(pts)):
        out[f"k{i}"] = K[:, i]
    out.to_csv(D / "04-kde.dat", sep=" ", index=False, float_format="%.5f")
    pd.DataFrame({"x": pts, "y": 0}).to_csv(D / "04-kde-pontok.dat", sep=" ", index=False)


if __name__ == "__main__":
    fig04_pca(); fig04_kde(); print("ok4")


def fig05():
    from sklearn.datasets import make_blobs, make_moons, make_circles
    rng = np.random.default_rng(5)
    # (a) kompakt, (b) elnyújtott, (c) nem konvex, (d) eltérő sűrűség + zaj
    Xa, ya = make_blobs(n_samples=150, centers=[[-2, 0], [2, 1], [0, 3]], cluster_std=0.6, random_state=1)
    Xb, yb = make_blobs(n_samples=150, centers=[[0, 0], [0, 2.2]], cluster_std=0.5, random_state=2)
    Xb = Xb @ np.array([[2.2, 0.0], [0.9, 0.35]])
    Xc, yc = make_moons(n_samples=200, noise=0.07, random_state=3)
    Xd1 = rng.normal([0, 0], 0.25, size=(90, 2)); Xd2 = rng.normal([2.2, 1.2], 0.8, size=(60, 2))
    noise = rng.uniform([-1.5, -1.5], [4, 3.5], size=(25, 2))
    Xd = np.vstack([Xd1, Xd2, noise]); yd = np.r_[np.zeros(90), np.ones(60), np.full(25, 4)].astype(int)
    for name, X, y in [("a", Xa, ya), ("b", Xb, yb), ("c", Xc, yc), ("d", Xd, yd)]:
        pd.DataFrame({"x": X[:, 0], "y": X[:, 1], "c": y}).to_csv(D / f"05-alak-{name}.dat", sep=" ", index=False, float_format="%.4f")
    # k-átlag iterációk
    rng = np.random.default_rng(7)
    centers = np.array([[1.0, 1.2], [4.2, 1.0], [2.6, 3.8]])
    X = np.vstack([c + rng.normal(scale=0.55, size=(50, 2)) for c in centers])
    V = np.array([[0.4, 3.9], [1.2, 3.6], [4.6, 3.4]])
    hist, labs, J = [V.copy()], [], []
    for t in range(20):
        Dm = ((X[:, None, :] - V[None, :, :]) ** 2).sum(-1); lab = Dm.argmin(1); labs.append(lab)
        J.append(Dm[np.arange(len(X)), lab].sum())
        Vn = np.array([X[lab == i].mean(0) for i in range(3)]); hist.append(Vn)
        if np.allclose(Vn, V): break
        V = Vn
    for nm, lab in [("iter0", labs[0]), ("iter1", labs[1]), ("final", labs[-1])]:
        pd.DataFrame({"x": X[:, 0], "y": X[:, 1], "c": lab}).to_csv(D / f"05-km-{nm}.dat", sep=" ", index=False, float_format="%.4f")
    for i in range(3):
        pd.DataFrame([h[i] for h in hist], columns=["x", "y"]).to_csv(D / f"05-km-traj{i}.dat", sep=" ", index=False, float_format="%.4f")
    with open(D / "05-km-param.tex", "w") as f:
        f.write("\\def\\Ja{%s}\\def\\Jb{%s}\\def\\Jc{%s}\n" % tuple(f"{v:.1f}".replace(".", "{,}") for v in [J[0], J[1], J[-1]]))
        for nm, V in [("a", hist[0]), ("b", hist[1]), ("c", hist[-1])]:
            f.write("\\def\\V%s{%s}\n" % (nm, " ".join(f"({v[0]:.3f},{v[1]:.3f})" for v in V)))


if __name__ == "__main__":
    fig05(); print("ok5")


def fig07():
    rng = np.random.default_rng(11)
    f = lambda x: np.sin(1.6 * x) + 0.3 * x
    xtr = np.sort(rng.uniform(0, 4, 25)); ytr = f(xtr) + rng.normal(0, 0.3, 25)
    xte = rng.uniform(0, 4, 400); yte = f(xte) + rng.normal(0, 0.3, 400)
    rows = []
    for deg in range(0, 13):
        c = np.polyfit(xtr, ytr, deg)
        rows.append((deg, np.mean((np.polyval(c, xtr) - ytr) ** 2), np.mean((np.polyval(c, xte) - yte) ** 2)))
    pd.DataFrame(rows, columns=["fok", "tanito", "teszt"]).to_csv(D / "07-komplexitas.dat", sep=" ", index=False, float_format="%.5f")
    xs = np.linspace(0, 4, 200)
    out = pd.DataFrame({"x": xs, "f": f(xs)})
    for deg in [1, 4, 12]:
        out[f"p{deg}"] = np.clip(np.polyval(np.polyfit(xtr, ytr, deg), xs), -2.5, 3.5)
    out.to_csv(D / "07-illesztes.dat", sep=" ", index=False, float_format="%.4f")
    pd.DataFrame({"x": xtr, "y": ytr}).to_csv(D / "07-pontok.dat", sep=" ", index=False, float_format="%.4f")


if __name__ == "__main__":
    fig07(); print("ok7")


def fig08():
    from scipy.interpolate import BSpline
    k = 3
    inner = np.linspace(0, 10, 6)
    t = np.r_[[inner[0]] * k, inner, [inner[-1]] * k]
    xs = np.linspace(0, 10, 300)
    out = pd.DataFrame({"x": xs})
    nb = len(t) - k - 1
    for i in range(nb):
        c = np.zeros(nb); c[i] = 1
        out[f"b{i}"] = np.nan_to_num(BSpline(t, c, k, extrapolate=False)(xs))
    w = np.array([0.5, 1.4, 0.2, 1.8, 1.0, 1.6, 0.4, 1.1])[:nb]
    out["s"] = (out[[f"b{i}" for i in range(nb)]].to_numpy() * w).sum(1)
    out.to_csv(D / "08-bspline.dat", sep=" ", index=False, float_format="%.5f")
    with open(D / "08-bspline-param.tex", "w") as f:
        f.write("\\def\\nb{%d}\\def\\csomok{%s}\n" % (nb - 1, ",".join(f"{v:g}" for v in inner)))


if __name__ == "__main__":
    fig08(); print("ok8")


def fig11():
    rng = np.random.default_rng(11)
    # (a) Mahalanobis: korrelált felhő + két kiemelt pont
    C = np.array([[1.0, 0.85], [0.85, 1.0]])
    X = rng.multivariate_normal([0, 0], C, 160)
    pd.DataFrame(X, columns=["x", "y"]).to_csv(D / "11-maha.dat", sep=" ", index=False, float_format="%.4f")
    # (b) LOF: sűrű és ritka csoport, globális és lokális kiugró
    A = rng.normal([1.0, 1.0], 0.18, (60, 2))
    B = rng.normal([4.0, 3.0], 0.75, (60, 2))
    pd.DataFrame(np.vstack([A, B]), columns=["x", "y"]).to_csv(D / "11-lof.dat", sep=" ", index=False, float_format="%.4f")
    # (c) izolációs fa: véletlen vágások egy normál és egy kiugró pont elszigeteléséig
    N = rng.normal([0.5, 0.5], [0.12, 0.12], (90, 2)).clip(0.05, 0.95)
    pd.DataFrame(N, columns=["x", "y"]).to_csv(D / "11-iso-pts.dat", sep=" ", index=False, float_format="%.4f")
    def isolate(P, target, rng, box=(0, 1, 0, 1), depth=0, segs=None):
        segs = [] if segs is None else segs
        x0, x1, y0, y1 = box
        inside = P[(P[:, 0] >= x0) & (P[:, 0] <= x1) & (P[:, 1] >= y0) & (P[:, 1] <= y1)]
        if len(inside) <= 1 or depth > 30:
            return segs
        j = rng.integers(2)
        lo, hi = inside[:, j].min(), inside[:, j].max()
        if hi - lo < 1e-9:
            return segs
        c = rng.uniform(lo, hi)
        if j == 0:
            segs.append((c, y0, c, y1)); box = (x0, c, y0, y1) if target[0] <= c else (c, x1, y0, y1)
        else:
            segs.append((x0, c, x1, c)); box = (x0, x1, y0, c) if target[1] <= c else (x0, x1, c, y1)
        return isolate(P, target, rng, box, depth + 1, segs)
    out = {}
    anom = np.array([0.92, 0.12]); norm_pt = N[np.argmin(((N - [0.5, 0.5]) ** 2).sum(1))]
    P = np.vstack([N, anom])
    for nev, t, seed in [("anom", anom, 3), ("norm", norm_pt, 5)]:
        segs = isolate(P, t, np.random.default_rng(seed))
        out[nev] = segs
        pd.DataFrame(segs, columns=["x0", "y0", "x1", "y1"]).to_csv(D / f"11-iso-{nev}.dat", sep=" ", index=False, float_format="%.4f")
    with open(D / "11-iso-meta.tex", "w") as f:
        f.write(f"\\def\\isoAx{{{anom[0]:.4f}}}\\def\\isoAy{{{anom[1]:.4f}}}"
                f"\\def\\isoNx{{{norm_pt[0]:.4f}}}\\def\\isoNy{{{norm_pt[1]:.4f}}}"
                f"\\def\\isoAn{{{len(out['anom'])}}}\\def\\isoNn{{{len(out['norm'])}}}\n")
    # (d) anomáliatípusok idősorai
    t = np.arange(0, 200)
    s = np.sin(2 * np.pi * t / 50) + rng.normal(0, 0.12, len(t))
    s_pont = s.copy(); s_pont[60] += 2.6
    s_kont = s.copy(); s_kont[86:90] = [0.6, 0.95, 0.9, 0.55]   # értéke "normális", de a fázisban szokatlan (völgy helyett csúcs)
    s_koll = s.copy(); s_koll[130:162] = -0.2 + rng.normal(0, 0.03, 32)  # kiesett ingadozás
    pd.DataFrame({"t": t, "pont": s_pont, "kont": s_kont, "koll": s_koll}).to_csv(D / "11-tipusok.dat", sep=" ", index=False, float_format="%.4f")


if __name__ == "__main__":
    fig11(); print("ok11")


def fig12():
    a, b = ab.mini.idosor_mini()
    n = len(a)
    C = np.full((n + 1, n + 1), np.inf); C[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            C[i, j] = (a[i - 1] - b[j - 1]) ** 2 + min(C[i - 1, j], C[i, j - 1], C[i - 1, j - 1])
    # visszakövetés
    i, j, path = n, n, [(n, n)]
    while (i, j) != (1, 1):
        cand = [(i - 1, j - 1), (i - 1, j), (i, j - 1)]
        cand = [c for c in cand if c[0] >= 1 and c[1] >= 1]
        i, j = min(cand, key=lambda c: C[c])
        path.append((i, j))
    path = path[::-1]
    with open(D / "12-dtw-matrix.tex", "w") as f:
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                st = "pathcell" if (i, j) in path else "cell"
                v = C[i, j]
                f.write(f"\\node[{st}] at ({j - 1},{n - i}) {{{int(v)}}};\n")
        for k in range(n):
            f.write(f"\\node[lab] at ({k},{n - 0.35}) {{{int(b[k])}}};\n")
            f.write(f"\\node[lab] at ({-0.85},{n - 1 - k}) {{{int(a[k])}}};\n")
        pts = " -- ".join(f"({j - 1},{n - i})" for i, j in path)
        f.write(f"\\draw[pathline] {pts};\n")
    with open(D / "12-dtw-path.dat", "w") as f:
        f.write("i j\n" + "\n".join(f"{i - 1} {j - 1}" for i, j in path) + "\n")
    # PAA és SAX egy napi hűtővízáram-sorozaton
    h = ab.load_plant().hourly.set_index("ido").F_hutoviz["2025-10-20":"2025-10-22"].to_numpy()
    x = (h - h.mean()) / h.std()
    w = 12
    paa = x.reshape(w, -1).mean(axis=1)
    br = np.array([-0.6745, 0.0, 0.6745])
    sym = np.array(list("abcd"))[np.searchsorted(br, paa)]
    pd.DataFrame({"t": np.arange(len(x)), "x": x}).to_csv(D / "12-sax-x.dat", sep=" ", index=False, float_format="%.4f")
    seg = len(x) // w
    pd.DataFrame({"t0": np.arange(w) * seg, "t1": (np.arange(w) + 1) * seg - 0.0, "paa": paa, "s": sym}).to_csv(
        D / "12-sax-paa.dat", sep=" ", index=False, float_format="%.4f")
    with open(D / "12-sax-meta.tex", "w") as f:
        f.write("\\def\\saxword{" + "".join(sym) + "}\n")


if __name__ == "__main__":
    fig12(); print("ok12")


def fig13():
    docs = ab.mini.szoveg_mini()
    stop = {"a", "és", "volt"}
    toks = [[w for w in d.split() if w not in stop] for d in docs]
    terms = ["kávé", "friss", "illatos", "tea", "szállítás", "lassú", "gyors"]
    tf = np.array([[t.count(w) for w in terms] for t in toks], dtype=float)
    df = (tf > 0).sum(axis=0)
    idf = np.log(len(docs) / df)
    W = tf * idf
    mx = W.max()
    with open(D / "13-dtm.tex", "w") as f:
        for j, w in enumerate(terms):
            f.write(f"\\node[term] at ({j},1.0) {{{w}}};\n")
            idf_txt = f"{idf[j]:.2f}".replace(".", "{,}")
            f.write(f"\\node[idf] at ({j},-5.0) {{{idf_txt}}};\n")
        for i in range(len(docs)):
            f.write(f"\\node[doc] at (-1.1,{-i}) {{$d_{i + 1}$}};\n")
            for j in range(len(terms)):
                v = W[i, j]
                shade = int(round(100 * v / mx))
                txt = "" if v == 0 else f"{v:.2f}".replace(".", "{,}")
                f.write(f"\\node[cell, fill=cA!{shade}!white{', text=white' if shade > 55 else ''}] at ({j},{-i}) {{{txt}}};\n")


if __name__ == "__main__":
    fig13(); print("ok13")
