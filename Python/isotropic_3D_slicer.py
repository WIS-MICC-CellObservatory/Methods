"""
Isotropic Slicer for TIFF Z‑Stacks — UI (PyQt6 optional) + Streamlit optional + CLI (default)
--------------------------------------------------------------------------------------------

**Update:** Compression is now **always `deflate`** (lossless ZIP). It is no longer exposed
as a UI or CLI parameter; every output TIFF uses `deflate`.

Also includes **persistent preferences**: last-used settings are saved to
`~/.isotropic_slicer_prefs.json` and auto-loaded next time (PyQt6 & Streamlit UIs).

Run modes
- **CLI (default)** — no extra GUI libs required.
- **PyQt6 GUI** — desktop UI, launch with `--gui`.
- **Streamlit UI** — web-style UI, if `streamlit` is installed.

Core features
- Load 3D or 4D TIFF (channels either **before** XY or **after** XY).
- **Explicit** z- and channel-axis selection (`--z-axis`, `--c-axis`).
- Resample **Z only** to achieve isotropic voxels using `z_aspect = z_spacing / xy_spacing`.
- Export **XY / ZX / ZY** slices with suffixes `*_xy_N.tif`, `*_zx_N.tif`, `*_zy_N.tif`.
- Preserve whether channels are **before** or **after** the XY axes in the outputs.
- Built‑in self tests (`--selftest`).

Quick start (CLI)
-----------------
```bash
python this_file.py \
  --input stack.tif \
  --z-axis first \
  --c-axis none \
  --z-aspect 5.0 \
  --mode labels \
  --out-dir isotropic_slices \
  --skip-empty
```

Run the **PyQt6 GUI**
---------------------
```bash
pip install PyQt6 tifffile numpy scipy
python this_file.py --gui
```

Run the **Streamlit UI** (optional)
-----------------------------------
```bash
pip install streamlit tifffile numpy scipy
streamlit run this_file.py
```

Notes
- `mode=labels` → nearest-neighbor along Z (preserves integer IDs).
- `mode=image`  → tries linear interpolation with SciPy; falls back to nearest if SciPy missing.
- Channels **between** X and Y (e.g., Y,C,X) are rejected with a clear error; adjust as needed.
"""

from __future__ import annotations
from pathlib import Path
import io
import os
import sys
import json
import argparse
import tempfile
import traceback
import numpy as np
from tifffile import imread, imwrite, TiffFile

# -------------------------- preferences (persistent) --------------------------

PREFS_FILE_ENV = "ISOTROPIC_SLICER_PREFS"  # optional override
DEFAULT_PREFS = {
    "z_axis": "first",
    "c_axis": "none",
    "z_aspect": 1.0,
    "mode": "labels",
    "out_dir": str(Path.cwd() / "isotropic_slices"),
    "skip_empty": False,
    "last_input": "",
}

def _prefs_path(override: str | os.PathLike | None = None) -> Path:
    if override:
        return Path(override)
    env = os.environ.get(PREFS_FILE_ENV)
    if env:
        return Path(env)
    return Path.home() / ".isotropic_slicer_prefs.json"


def load_prefs(path: str | os.PathLike | None = None) -> dict:
    p = _prefs_path(path)
    try:
        data = json.loads(Path(p).read_text())
        merged = DEFAULT_PREFS | data
        if not isinstance(merged.get("z_aspect", 1.0), (int, float)):
            merged["z_aspect"] = 1.0
        return merged
    except FileNotFoundError:
        return DEFAULT_PREFS.copy()
    except Exception:
        return DEFAULT_PREFS.copy()


def save_prefs(prefs: dict, path: str | os.PathLike | None = None) -> None:
    sanitized = {k: prefs.get(k, DEFAULT_PREFS.get(k)) for k in DEFAULT_PREFS.keys()}
    for key in ("out_dir", "last_input"):
        if isinstance(sanitized.get(key), (Path,)):
            sanitized[key] = str(sanitized[key])
    _prefs_path(path).write_text(json.dumps(sanitized, indent=2))


# -------------------------- helpers --------------------------

def parse_axis(ax_str, ndim: int, allow_none: bool = False):
    """Parse axis spec from CLI/UI: 'first'/'last'/int (or 'none' if allow_none)."""
    if isinstance(ax_str, str):
        s = ax_str.strip().lower()
        if allow_none and s in {"none", "no", "disabled"}:
            return None
        if s in {"first", "0"}:
            return 0
        if s in {"last", "-1"}:
            return ndim - 1
        try:
            i = int(s)
            if not (-ndim <= i < ndim):
                raise ValueError
            return i
        except Exception:
            raise ValueError(f"Invalid axis spec: {ax_str}")
    if ax_str is None and allow_none:
        return None
    if isinstance(ax_str, int):
        if not (-ndim <= ax_str < ndim):
            raise ValueError(f"Axis {ax_str} out of bounds for ndim={ndim}")
        return ax_str
    raise ValueError(f"Invalid axis type: {type(ax_str)}")


def canonicalize_preserve_c_side(arr: np.ndarray, z_axis: int, c_axis: int | None):
    """
    Reorder array to one of:
      - 3D: (Z, Y, X)
      - 4D: (Z, C, Y, X) if channels BEFORE XY
            (Z, Y, X, C) if channels AFTER XY
    Returns (arr_can, cpos) where cpos ∈ {None, 'before', 'after'}.
    Keeps XY order as in the input.
    """
    ndim = arr.ndim
    za = z_axis if z_axis >= 0 else z_axis + ndim
    if c_axis is not None:
        ca = c_axis if c_axis >= 0 else c_axis + ndim

    if c_axis is None:
        if ndim != 3:
            raise ValueError(f"No channels axis but input ndim={ndim} != 3")
        others = [i for i in range(ndim) if i != za]
        perm = [za] + others  # -> (Z, Y, X)
        return arr.transpose(perm), None

    if ndim != 4:
        raise ValueError(f"Channels provided but input ndim={ndim} (expected 4)")
    if za == ca:
        raise ValueError("z_axis and c_axis refer to the same dimension.")

    others = [i for i in range(ndim) if i not in (za, ca)]  # two spatial axes in original order
    y_ax, x_ax = others[0], others[1]

    if ca < min(others):
        cpos = "before"
        perm = [za, ca, y_ax, x_ax]  # -> (Z, C, Y, X)
    elif ca > max(others):
        cpos = "after"
        perm = [za, y_ax, x_ax, ca]  # -> (Z, Y, X, C)
    else:
        raise ValueError(
            "Channel axis must be either before both XY or after both XY (not between X and Y)."
        )
    return arr.transpose(perm), cpos


def resample_z_isotropic(arr_can: np.ndarray, z_aspect: float, mode: str = "labels") -> np.ndarray:
    """Resample along the first axis (Z) to achieve isotropic voxels."""
    z_aspect = float(z_aspect)
    Z = arr_can.shape[0]
    newZ = max(1, int(round(Z * z_aspect)))
    if newZ == Z:
        return arr_can

    if mode == "image":
        try:
            from scipy.ndimage import zoom
            factors = [newZ / Z] + [1.0] * (arr_can.ndim - 1)
            return zoom(arr_can, factors, order=1, prefilter=False)
        except Exception:
            pass  # fall back to nearest

    # Nearest neighbor along Z
    src_idx = np.rint(np.linspace(0, Z - 1, newZ)).astype(int)
    src_idx = np.clip(src_idx, 0, Z - 1)
    return arr_can[src_idx, ...]


def infer_axes_metadata(file_like) -> str | None:
    """Try to infer axis string from TIFF metadata. Returns axes string or None."""
    try:
        with TiffFile(file_like) as tf:
            s = tf.series[0]
            axes = s.axes
            if axes:
                return axes
    except Exception:
        return None
    return None


# -------------------------- core writer --------------------------

def save_isotropic_slices(
    tif_path,
    out_dir="isotropic_slices",
    z_aspect=1.0,      # z_spacing / xy_spacing
    z_axis="first",   # 'first' | 'last' | int
    c_axis="none",    # 'none' | 'first' | 'last' | int
    mode="labels",    # 'labels' or 'image'
    skip_empty=False,
    progress_cb=None,  # optional callback: progress_cb(done:int, total:int, note:str)
):
    """
    Read a 3D/4D TIFF, explicitly using z_axis and c_axis, resample Z to isotropic,
    and write per-slice TIFFs with suffixes:
      *_xy_N.tif  (XY planes)   -> (Y,X) | (C,Y,X) | (Y,X,C)
      *_zx_N.tif  (ZX along Y)  -> (Z,X) | (C,Z,X) | (Z,X,C)
      *_zy_N.tif  (ZY along X)  -> (Z,Y) | (C,Z,Y) | (Z,Y,C)

    Compression is always 'deflate' (lossless ZIP).
    If channels are BEFORE XY in the input, outputs keep channels BEFORE (planar).
    If channels are AFTER XY, outputs keep channels AFTER (interleaved).
    """
    tif_path = Path(tif_path) if isinstance(tif_path, (str, os.PathLike)) else tif_path
    arr = imread(tif_path)
    ndim = arr.ndim

    za = parse_axis(z_axis, ndim, allow_none=False)
    ca = parse_axis(c_axis, ndim, allow_none=True)

    # Canonicalize while preserving channel side w.r.t. XY
    arr_can, cpos = canonicalize_preserve_c_side(arr, za, ca)

    # Resample Z to isotropic
    arr_iso = resample_z_isotropic(arr_can, z_aspect=float(z_aspect), mode=mode)

    # Shapes
    if arr_iso.ndim == 3:
        Z, Y, X = arr_iso.shape
        C = None
    else:
        if cpos == "before":   # (Z, C, Y, X)
            Z, C, Y, X = arr_iso.shape
        else:                   # (Z, Y, X, C)
            Z, Y, X, C = arr_iso.shape


    stem = Path(tif_path).stem if not isinstance(tif_path, io.BytesIO) else "stack"
    if mode == "labels":
        cp_mask_suffix = "_cp_masks" 
        image_stem = stem[:-len(cp_mask_suffix)] if stem.endswith(cp_mask_suffix) else stem
        out_base = Path(out_dir) / image_stem
    else:
        out_base = Path(out_dir) / stem

    (out_base / "xy").mkdir(parents=True, exist_ok=True)
    (out_base / "zx").mkdir(parents=True, exist_ok=True)
    (out_base / "zy").mkdir(parents=True, exist_ok=True)

    compression = "deflate"  # fixed per request

    def pc_for(before):
        return "separate" if before else "contig"

    total = Z + Y + X
    done = 0

    def report(note):
        nonlocal done
        done += 1
        if progress_cb:
            try:
                progress_cb(done, total, note)
            except Exception:
                pass

    # ---------------- XY slices ----------------
    for z in range(Z):
        if C is None:
            tile = arr_iso[z]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "xy" / f"{stem}_xy_{z:04d}.tif",
                        tile, compression=compression, metadata={"axes": "YX"})
        elif cpos == "before":
            tile = arr_iso[z]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "xy" / f"{stem}_xy_{z:04d}.tif",
                        tile, compression=compression, planarconfig=pc_for(True), metadata={"axes": "CYX"})
        else:
            tile = arr_iso[z]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "xy" / f"{stem}_xy_{z:04d}.tif",
                        tile, compression=compression, planarconfig=pc_for(False), metadata={"axes": "YXC"})
        report(f"xy {z+1}/{Z}")

    # ---------------- ZX (iterate Y) ----------------
    for y in range(Y):
        if C is None:
            tile = arr_iso[:, y, :]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "zx" / f"{stem}_zx_{y:04d}.tif",
                        tile, compression=compression, metadata={"axes": "ZX"})
        elif cpos == "before":
            tile = np.swapaxes(arr_iso[:, :, y, :], 0, 1)  # (C, Z, X)
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "zx" / f"{stem}_zx_{y:04d}.tif",
                        tile, compression=compression, planarconfig=pc_for(True), metadata={"axes": "CZX"})
        else:
            tile = arr_iso[:, y, :, :]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "zx" / f"{stem}_zx_{y:04d}.tif",
                        tile, compression=compression, planarconfig=pc_for(False), metadata={"axes": "ZXC"})
        report(f"zx {y+1}/{Y}")

    # ---------------- ZY (iterate X) ----------------
    for x in range(X):
        if C is None:
            tile = arr_iso[:, :, x]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "zy" / f"{stem}_zy_{x:04d}.tif",
                        tile, compression=compression, metadata={"axes": "ZY"})
        elif cpos == "before":
            tile = np.swapaxes(arr_iso[:, :, :, x], 0, 1)  # (C, Z, Y)
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "zy" / f"{stem}_zy_{x:04d}.tif",
                        tile, compression=compression, planarconfig=pc_for(True), metadata={"axes": "CZY"})
        else:
            tile = arr_iso[:, :, x, :]
            if not (skip_empty and np.max(tile) == 0):
                imwrite(out_base / "zy" / f"{stem}_zy_{x:04d}.tif",
                        tile, compression=compression, planarconfig=pc_for(False), metadata={"axes": "ZYC"})
        report(f"zy {x+1}/{X}")

    return {
        "Z": Z, "Y": Y, "X": X, "C": C,
        "out_dir": str(out_base.resolve()),
        "cpos": ("none" if C is None else cpos),
        "mode": mode,
    }


# -------------------------- Streamlit UI (optional) --------------------------

def streamlit_main():
    """Run the Streamlit UI if Streamlit is installed. Persists prefs across runs."""
    try:
        import streamlit as st  # imported only when UI is requested/available
    except Exception as e:
        print("Streamlit not available. Use the CLI (python this_file.py --help) or PyQt6 GUI (--gui).")
        return

    prefs = load_prefs()

    st.set_page_config(page_title="Isotropic Slicer", page_icon="🧩", layout="wide")
    st.title("🧩 Isotropic Slicer for TIFF Z-Stacks")
    st.markdown("Configure parameters, then generate XY/ZX/ZY slices with preserved channel placement. Compression is always **deflate**.")

    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        upl = st.file_uploader("Upload 3D/4D TIFF", type=["tif", "tiff"], accept_multiple_files=False)
        meta_axes = None
        arr = None

        if upl is not None:
            tiff_buf = io.BytesIO(upl.read())
            meta_axes = infer_axes_metadata(io.BytesIO(tiff_buf.getbuffer()))
            arr = imread(io.BytesIO(tiff_buf.getbuffer()))
            st.success(f"Loaded image: shape={arr.shape}; dtype={arr.dtype}")
            if meta_axes:
                st.info(f"Detected axes from metadata: **{meta_axes}**")
            else:
                st.warning("Could not detect axis order from metadata; please set axes manually.")

        st.subheader("Axes configuration")
        if arr is not None:
            ndim = arr.ndim
            st.caption(f"Input dimensions (ndim={ndim}). Provide explicit Z and Channel axes.")

            z_axis_str = st.text_input(
                "Z axis (index or 'first'/'last')",
                value=str(prefs.get("z_axis", DEFAULT_PREFS["z_axis"]))
            )
            c_axis_str = st.text_input(
                "Channel axis (index, 'first'/'last', or 'none')",
                value=str(prefs.get("c_axis", DEFAULT_PREFS["c_axis"]))
            )

        st.subheader("Resampling & Output")
        z_aspect = st.number_input(
            "z_aspect = z_spacing / xy_spacing",
            min_value=0.01, max_value=100.0,
            value=float(prefs.get("z_aspect", DEFAULT_PREFS["z_aspect"])), step=0.01,
        )
        mode = st.radio(
            "Interpolation mode", options=["labels", "image"],
            index=0 if prefs.get("mode", DEFAULT_PREFS["mode"]) == "labels" else 1,
            horizontal=True,
        )
        out_dir = st.text_input(
            "Output directory", value=str(prefs.get("out_dir", DEFAULT_PREFS["out_dir"]))
        )
        skip_empty = st.checkbox(
            "Skip empty slices (all zeros)", value=bool(prefs.get("skip_empty", DEFAULT_PREFS["skip_empty"]))
        )
        run_btn = st.button("Run", type="primary", use_container_width=True)

    with col_right:
        st.subheader("Preview & Notes")
        st.markdown(
            "- XY slices are one per Z plane.\n"
            "- ZX slices iterate along Y; Z runs vertically.\n"
            "- ZY slices iterate along X; Z runs vertically.\n"
            "- If channels are BEFORE XY in input, outputs keep channels BEFORE (planar).\n"
            "- If channels are AFTER XY, outputs keep channels AFTER (interleaved).\n"
            "- **Compression is always deflate (lossless).**"
        )
        if arr is not None:
            st.write("Middle XY slice preview (no resampling):")
            try:
                mid = arr.shape[0] // 2 if arr.ndim >= 3 else 0
                if arr.ndim == 3:
                    st.image(arr[mid, ...], clamp=True)
                elif arr.ndim == 4:
                    ax = (meta_axes or "").replace("S", "C") if meta_axes else None
                    if ax and "C" in ax:
                        cidx = ax.index("C")
                    else:
                        cidx = -1
                    disp = np.moveaxis(arr, cidx, -1)
                    chans = disp.shape[-1]
                    sl = slice(0, min(chans, 3))
                    st.image(disp[mid, ..., sl], clamp=True)
            except Exception as e:
                st.caption(f"Preview unavailable: {e}")

    if run_btn:
        if upl is None:
            st.error("Please upload a TIFF first.")
            st.stop()
        try:
            ndim = arr.ndim
            z_axis = parse_axis(z_axis_str, ndim, allow_none=False)
            c_axis = parse_axis(c_axis_str, ndim, allow_none=True)

            prog = st.progress(0.0, text="Writing slices…")
            def cb(done, total, note):
                prog.progress(done/total, text=f"{note}")

            result = save_isotropic_slices(
                tif_path=io.BytesIO(tiff_buf.getbuffer()),
                out_dir=out_dir,
                z_aspect=z_aspect,
                z_axis=z_axis,
                c_axis=c_axis,
                mode=mode,
                skip_empty=skip_empty,
                progress_cb=cb,
            )

            # persist prefs (no compression key anymore)
            prefs.update({
                "z_axis": z_axis_str,
                "c_axis": c_axis_str,
                "z_aspect": float(z_aspect),
                "mode": mode,
                "out_dir": out_dir,
                "skip_empty": bool(skip_empty),
                "last_input": upl.name,
            })
            save_prefs(prefs)

            st.success(
                f"Done. Saved XY/ZX/ZY slices to {result['out_dir']}\n"
                f"Z={result['Z']}, Y={result['Y']}, X={result['X']}{', C='+str(result['C']) if result['C'] is not None else ''}; "
                f"channels={result['cpos']}; mode={result['mode']} (compression=deflate)"
            )
        except Exception as e:
            st.error(f"Error: {e}")
            st.exception(e)


# -------------------------- PyQt6 GUI (optional) --------------------------

def qt_main():
    try:
        from PyQt6 import QtCore, QtWidgets
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QCheckBox,
            QProgressBar, QTextEdit
        )
    except Exception:
        print("PyQt6 not available. Install with: pip install PyQt6")
        return 1

    prefs = load_prefs()

    class Worker(QtCore.QObject):
        progress = QtCore.pyqtSignal(int, int, str)
        finished = QtCore.pyqtSignal(dict)
        failed = QtCore.pyqtSignal(str)

        def __init__(self, params):
            super().__init__()
            self.params = params

        @QtCore.pyqtSlot()
        def run(self):
            try:
                def cb(done, total, note):
                    self.progress.emit(done, total, note)
                result = save_isotropic_slices(progress_cb=cb, **self.params)
                self.finished.emit(result)
            except Exception as e:
                self.failed.emit(f"{e}\n\n{traceback.format_exc()}")

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Isotropic Slicer (PyQt6)")
            self.resize(800, 600)

            central = QWidget(); self.setCentralWidget(central)
            v = QVBoxLayout(central)

            # --- Input file ---
            h1 = QHBoxLayout(); v.addLayout(h1)
            h1.addWidget(QLabel("Input TIFF:"))
            self.in_edit = QLineEdit(prefs.get("last_input", "")); h1.addWidget(self.in_edit)
            b_browse = QPushButton("Browse…"); h1.addWidget(b_browse)
            b_browse.clicked.connect(self.browse_input)

            # Shape / metadata
            self.shape_label = QLabel("shape: –  |  axes: –")
            v.addWidget(self.shape_label)

            # --- Axes ---
            h2 = QHBoxLayout(); v.addLayout(h2)
            h2.addWidget(QLabel("Z axis:"))
            self.z_combo = QComboBox(); self.z_combo.addItems(["first", "last", "0", "1", "2", "3"]) ; h2.addWidget(self.z_combo)
            self.z_combo.setCurrentText(str(prefs.get("z_axis", DEFAULT_PREFS["z_axis"])))

            h2.addWidget(QLabel("Channel axis:"))
            self.c_combo = QComboBox(); self.c_combo.addItems(["none", "first", "last", "0", "1", "2", "3"]) ; h2.addWidget(self.c_combo)
            self.c_combo.setCurrentText(str(prefs.get("c_axis", DEFAULT_PREFS["c_axis"])))

            # --- Resampling ---
            h3 = QHBoxLayout(); v.addLayout(h3)
            h3.addWidget(QLabel("z_aspect:"))
            self.z_spin = QDoubleSpinBox(); self.z_spin.setRange(0.01, 100.0); self.z_spin.setSingleStep(0.01); self.z_spin.setValue(float(prefs.get("z_aspect", DEFAULT_PREFS["z_aspect"]))); h3.addWidget(self.z_spin)
            h3.addWidget(QLabel("mode:"))
            self.mode_combo = QComboBox(); self.mode_combo.addItems(["labels", "image"]) ; h3.addWidget(self.mode_combo)
            self.mode_combo.setCurrentText(str(prefs.get("mode", DEFAULT_PREFS["mode"])))

            # --- Output ---
            h4 = QHBoxLayout(); v.addLayout(h4)
            h4.addWidget(QLabel("Out dir:"))
            self.out_edit = QLineEdit(str(prefs.get("out_dir", DEFAULT_PREFS["out_dir"]))); h4.addWidget(self.out_edit)
            b_out = QPushButton("Choose…"); h4.addWidget(b_out)
            b_out.clicked.connect(self.choose_outdir)

            # --- Options ---
            h5 = QHBoxLayout(); v.addLayout(h5)
            self.skip_chk = QCheckBox("skip empty slices"); self.skip_chk.setChecked(bool(prefs.get("skip_empty", DEFAULT_PREFS["skip_empty"]))); h5.addWidget(self.skip_chk)

            # --- Progress / run ---
            self.run_btn = QPushButton("Run")
            v.addWidget(self.run_btn)
            self.run_btn.clicked.connect(self.run_job)

            self.pbar = QProgressBar(); self.pbar.setRange(0, 100); v.addWidget(self.pbar)
            self.log = QTextEdit(); self.log.setReadOnly(True); v.addWidget(self.log)

        def browse_input(self):
            path, _ = QFileDialog.getOpenFileName(self, "Select TIFF", str(Path.cwd()), "TIFF Files (*.tif *.tiff)")
            if not path:
                return
            self.in_edit.setText(path)
            self.update_metadata_preview(path)

        def update_metadata_preview(self, path: str):
            try:
                with TiffFile(path) as tf:
                    s = tf.series[0]
                    shp = s.shape
                    axes = (s.axes or "").replace("S", "C")
                self.shape_label.setText(f"shape: {shp}  |  axes: {axes or '–'}")
                if axes:
                    self.log.append(f"Metadata axes: {axes}")
            except Exception as e:
                self.log.append(f"Failed to read metadata: {e}")

        def choose_outdir(self):
            path = QFileDialog.getExistingDirectory(self, "Select Output Directory", str(Path.cwd()))
            if path:
                self.out_edit.setText(path)

        def current_prefs(self) -> dict:
            return {
                "z_axis": self.z_combo.currentText(),
                "c_axis": self.c_combo.currentText(),
                "z_aspect": float(self.z_spin.value()),
                "mode": self.mode_combo.currentText(),
                "out_dir": self.out_edit.text().strip(),
                "skip_empty": bool(self.skip_chk.isChecked()),
                "last_input": self.in_edit.text().strip(),
            }

        def run_job(self):
            in_path = self.in_edit.text().strip()
            if not in_path:
                self.log.append("Please choose an input TIFF.")
                return
            try:
                with TiffFile(in_path) as tf:
                    ndim = len(tf.series[0].shape)
            except Exception as e:
                self.log.append(f"Cannot open TIFF: {e}")
                return

            try:
                z_axis = parse_axis(self.z_combo.currentText(), ndim, allow_none=False)
                c_axis = parse_axis(self.c_combo.currentText(), ndim, allow_none=True)
            except Exception as e:
                self.log.append(f"Axis error: {e}")
                return

            params = dict(
                tif_path=in_path,
                out_dir=self.out_edit.text().strip(),
                z_aspect=float(self.z_spin.value()),
                z_axis=z_axis,
                c_axis=c_axis,
                mode=self.mode_combo.currentText(),
                skip_empty=self.skip_chk.isChecked(),
            )

            self.run_btn.setEnabled(False)
            self.log.append("Starting… (compression=deflate)")
            self.pbar.setValue(0)

            self.thread = QtCore.QThread(self)
            self.worker = Worker(params)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.on_progress)
            self.worker.finished.connect(self.on_finished)
            self.worker.failed.connect(self.on_failed)
            self.worker.finished.connect(self.thread.quit)
            self.worker.failed.connect(self.thread.quit)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

        def on_progress(self, done, total, note):
            pct = int(100 * done / max(1, total))
            self.pbar.setValue(pct)
            self.log.append(note)

        def on_finished(self, result: dict):
            self.run_btn.setEnabled(True)
            self.pbar.setValue(100)
            self.log.append(
                f"Done. Saved to {result['out_dir']} | Z={result['Z']}, Y={result['Y']}, X={result['X']}{', C='+str(result['C']) if result['C'] is not None else ''}; "
                f"channels={result['cpos']} (compression=deflate)"
            )
            save_prefs(self.current_prefs())

        def on_failed(self, msg: str):
            self.run_btn.setEnabled(True)
            self.log.append("ERROR:\n" + msg)

    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    return app.exec()


# -------------------------- CLI --------------------------

def cli_main(argv=None):
    p = argparse.ArgumentParser(description="Isotropic slicing of TIFF z-stacks (GUI/CLI)")
    p.add_argument("--gui", action="store_true", help="Launch the PyQt6 GUI")
    p.add_argument("--input", required=False, help="Path to input TIFF (CLI mode)")
    p.add_argument("--z-axis", required=False, default=None, help="Z axis: 'first'|'last'|int (CLI mode)")
    p.add_argument("--c-axis", required=False, default="none", help="Channel axis: 'none'|'first'|'last'|int")
    p.add_argument("--z-aspect", type=float, required=False, default=1.0, help="z_spacing / xy_spacing (e.g., 5.0)")
    p.add_argument("--mode", choices=["labels", "image"], default="labels", help="Interpolation along Z")
    p.add_argument("--out-dir", default="isotropic_slices", help="Output directory")
    p.add_argument("--skip-empty", action="store_true", help="Skip all-zero tiles")
    p.add_argument("--infer-axes", action="store_true", help="Infer axes from metadata if available")
    p.add_argument("--selftest", action="store_true", help="Run built-in tests and exit")

    args = p.parse_args(argv)

    if args.gui:
        return qt_main()

    if args.selftest:
        run_self_tests()
        return 0

    if not args.input:
        p.print_help(sys.stderr)
        print("\nNo --input provided. Use --gui for the desktop UI, or install streamlit and run:\n  streamlit run this_file.py\n", file=sys.stderr)
        return 2

    with TiffFile(args.input) as tf:
        arr_shape = tf.series[0].shape
        axes = tf.series[0].axes or ""
    ndim = len(arr_shape)

    z_axis = args.z_axis
    c_axis = args.c_axis

    if args.infer_axes and (z_axis is None or c_axis is None):
        meta_axes = infer_axes_metadata(args.input) or ""
        if z_axis is None and "Z" in meta_axes:
            z_axis = str(meta_axes.index("Z"))
        if c_axis in (None, "none"):
            c_axis = str(meta_axes.index("C")) if "C" in meta_axes else "none"

    if z_axis is None:
        raise SystemExit("Please provide --z-axis (or use --infer-axes if metadata is present).")

    result = save_isotropic_slices(
        tif_path=args.input,
        out_dir=args.out_dir,
        z_aspect=args.z_aspect,
        z_axis=z_axis,
        c_axis=c_axis,
        mode=args.mode,
        skip_empty=args.skip_empty,
    )

    print(
        f"Done. Saved XY/ZX/ZY slices to {result['out_dir']}\n"
        f"Z={result['Z']}, Y={result['Y']}, X={result['X']}{', C='+str(result['C']) if result['C'] is not None else ''}; "
        f"channels={result['cpos']}; mode={result['mode']} (compression=deflate)"
    )
    return 0


# -------------------------- tests --------------------------

def run_self_tests():
    print("Running self tests…")

    # --- Test 1: 3D no channels ---
    arr = np.arange(3*4*5, dtype=np.uint16).reshape(3,4,5)
    arr_can, cpos = canonicalize_preserve_c_side(arr, z_axis=0, c_axis=None)
    assert cpos is None
    out = resample_z_isotropic(arr_can, z_aspect=2.0, mode="labels")
    assert out.shape[0] == 6, f"Expected Z=6, got {out.shape[0]}"

    # Synthetic ZX/ZY tile shapes
    Z, Y, X = out.shape
    zx_tile = out[:, 0, :]  # (Z,X)
    zy_tile = out[:, :, 0]  # (Z,Y)
    assert zx_tile.shape == (6,5)
    assert zy_tile.shape == (6,4)

    # --- Test 2: 4D channels BEFORE XY (Z, C, Y, X) ---
    arr4 = np.zeros((5,3,4,6), dtype=np.uint8)
    arr_can, cpos = canonicalize_preserve_c_side(arr4, z_axis=0, c_axis=1)
    assert cpos == "before" and arr_can.shape == (5,3,4,6)
    out = resample_z_isotropic(arr_can, z_aspect=1.5, mode="labels")
    assert out.shape[0] == 8  # round(5*1.5)=8
    # ZX tile at y=0 -> (C,Z,X)
    tile_czx = np.swapaxes(out[:, :, 0, :], 0, 1)
    assert tile_czx.shape == (3, 8, 6)

    # --- Test 3: 4D channels AFTER XY (Z, Y, X, C) ---
    arr4_after = np.zeros((7,9,11,2), dtype=np.uint8)
    arr_can, cpos = canonicalize_preserve_c_side(arr4_after, z_axis=0, c_axis=3)
    assert cpos == "after" and arr_can.shape == (7,9,11,2)
    out = resample_z_isotropic(arr_can, z_aspect=2.0, mode="image")  # try image path
    assert out.shape[0] == 14
    # ZY tile at x=0 -> (Z,Y,C)
    tile_zyc = out[:, :, 0, :]
    assert tile_zyc.shape == (14, 9, 2)

    # --- Test 4: channel between X and Y raises ---
    try:
        _ = canonicalize_preserve_c_side(np.zeros((4,5,6,3)), z_axis=0, c_axis=2)  # pretend C between
        raise AssertionError("Expected ValueError for channels between X and Y")
    except ValueError:
        pass

    # --- Test 5: I/O roundtrip to temp dir ---
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tmp_tif = td / "test.tif"
        imwrite(tmp_tif, np.zeros((4,5,6), dtype=np.uint16))
        result = save_isotropic_slices(
            tif_path=tmp_tif,
            out_dir=td / "out",
            z_aspect=2.0,
            z_axis="first",
            c_axis="none",
            mode="labels",
            skip_empty=False,
        )
        assert Path(result["out_dir"]).exists()
        xy_files = list((td/"out"/"xy").glob("*_xy_*.tif"))
        assert len(xy_files) == 8  # newZ = round(4*2)=8

    # --- Test 6: preferences roundtrip ---
    with tempfile.TemporaryDirectory() as td:
        cfg = Path(td) / "prefs.json"
        p0 = load_prefs(cfg)
        assert isinstance(p0, dict) and "z_axis" in p0
        p0["z_axis"] = "last"; p0["c_axis"] = "first"; p0["z_aspect"] = 3.14
        save_prefs(p0, cfg)
        p1 = load_prefs(cfg)
        assert p1["z_axis"] == "last" and p1["c_axis"] == "first" and abs(p1["z_aspect"] - 3.14) < 1e-9

    print("All tests passed ✔")


# -------------------------- entrypoint --------------------------
if __name__ == "__main__":
    # If launched by Streamlit, run Streamlit UI; otherwise respect --gui, else CLI
    if os.environ.get("STREAMLIT_SERVER_PORT") or os.environ.get("STREAMLIT_RUNTIME"):
        streamlit_main()
    else:
        sys.exit(cli_main())