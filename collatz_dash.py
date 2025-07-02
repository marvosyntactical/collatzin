#!/usr/bin/env python3
"""
collatz_dash.py – A self‑contained Dash app for exploring 3‑D Collatz shrubs
============================================================================

* Launches a **browser‑based** UI (Plotly Dash) with live‑editable controls:
    - `LEFT_DEG`, `RIGHT_DEG` – turtle turn angles in degrees
    - `Z_STEP`               – vertical rise per iteration
    - `N_STARTS`             – number of random starting integers sampled
    - `MAX_START`            – exclusive upper bound on the sample
    - rule selector          – classic binary vs experimental ternary map
    - **Run** button         – generate / regenerate the figure
* Displays an interactive 3‑D plot (`dcc.Graph`) you can rotate/zoom/export.
* Contains a Markdown panel that renders **MathJax**, ready for you to flesh
  out a rigorous description of the model.  A terse starter explanation is
  provided below the controls.

Deployment on Fly.io
--------------------
1. **requirements.txt** – include: dash, plotly, numpy
2. **Procfile**
       web: gunicorn collatz_dash:server
3. ``fly launch``  → accept defaults, then ``fly deploy``.
   Fly will detect the *web* process via Procfile and bind the Dash server.

Local run for dev
-----------------
    $ python collatz_dash.py  # opens http://127.0.0.1:8080

"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context

# ───────────────────────────────────────────────────────────────────────────────
# Pure maths: Collatz path generator (same core as collatz3.py)
# ───────────────────────────────────────────────────────────────────────────────

def next_n(n: int, scheme: str = "binary") -> int:
    if scheme == "binary":
        return n // 2 if n % 2 == 0 else 3 * n + 1
    if scheme == "ternary":
        r = n % 3
        if r == 0:
            return n // 3
        if r == 1:
            return (4 * n + 1) // 3
        return (2 * n + 1) // 3
    raise ValueError("scheme must be 'binary' or 'ternary'")


def collatz_path_3d(start: int,
                    left_deg: float,
                    right_deg: float,
                    z_step: float,
                    scheme: str = "binary") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return arrays (x, y, z) for a single start value."""
    left_rad, right_rad = math.radians(left_deg), math.radians(right_deg)
    angle = math.radians(-75.0)  # init heading – tweakable if desired

    x = y = z = 0.0
    xs, ys, zs = [x], [y], [z]
    step_no = 0
    n = start
    while n != 1:
        nxt = next_n(n, scheme)
        # turn according to *current* residue
        if scheme == "binary":
            angle += left_rad if n % 2 == 0 else -right_rad
        else:
            r = n % 3
            angle += left_rad if r == 0 else (-right_rad if r == 1 else 0.5 * left_rad)
        step_len = 1.0 / math.log(nxt + 1.0)
        x += step_len * math.cos(angle)
        y += step_len * math.sin(angle)
        step_no += 1
        z = step_no * z_step
        xs.append(x); ys.append(y); zs.append(z)
        n = nxt
    return np.array(xs), np.array(ys), np.array(zs)


# ───────────────────────────────────────────────────────────────────────────────
# Helper for colour mapping – constant hue per trajectory (HSV rainbow)
# ───────────────────────────────────────────────────────────────────────────────

def colour_for(start: int, max_start: int) -> str:
    norm = (start - 2) / (max_start - 2)
    h = int(360 * norm)
    return f'hsl({h},80%,50%)'


# ───────────────────────────────────────────────────────────────────────────────
# Dash app layout
# ───────────────────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "Collatzin'"
server = app.server  # for gunicorn / Fly.io

app.layout = html.Div([
    html.H2("3‑D Collatz Shrub Explorer"),
    html.Div([
        html.Div([
            html.Label("Left turn (deg, even step)"),
            dcc.Input(id='left-deg', type='number', value=8.65, step=0.1),

            html.Label("Right turn (deg, odd step)", style={'marginTop': '0.5em'}),
            dcc.Input(id='right-deg', type='number', value=16.0, step=0.1),

            html.Label("Vertical z‑step per iteration", style={'marginTop': '0.5em'}),
            dcc.Input(id='z-step', type='number', value=0.2, step=0.05),

            html.Label("Number of trajectories", style={'marginTop': '0.5em'}),
            dcc.Input(id='n-starts', type='number', value=500, step=100, min=1),

            html.Label("Max starting integer (exclusive)", style={'marginTop': '0.5em'}),
            dcc.Input(id='max-start', type='number', value=1_000_000, step=10_000, min=10),

            html.Label("Iteration scheme", style={'marginTop': '0.5em'}),
            dcc.Dropdown(id='scheme', options=[
                {'label': 'Binary 3n+1', 'value': 'binary'},
                {'label': 'Ternary variant', 'value': 'ternary'}],
                value='binary'),

            html.Button('Run / Refresh', id='run-btn', n_clicks=0,
                        style={'marginTop': '1em', 'width': '100%'})
        ], style={'flex': '0 0 230px', 'display': 'flex', 'flexDirection': 'column'}),

        html.Div([
            dcc.Graph(id='shrub-plot', style={'height': '80vh'}),
            dcc.Markdown(id='explanation-md', mathjax=True,
                style={'borderTop': '1px solid #ccc', 'paddingTop': '0.5em'})
        ], style={'flex': '1 1 auto', 'paddingLeft': '1em'})
    ], style={'display': 'flex'}),
])


# ───────────────────────────────────────────────────────────────────────────────
# Callback – build the figure when the Run button is pressed
# ───────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output('shrub-plot', 'figure'),
    Output('explanation-md', 'children'),
    Input('run-btn', 'n_clicks'),
    State('left-deg', 'value'),
    State('right-deg', 'value'),
    State('z-step', 'value'),
    State('n-starts', 'value'),
    State('max-start', 'value'),
    State('scheme', 'value')
)
def update_shrub(_, left_deg, right_deg, z_step, n_starts, max_start, scheme):
    # Guard: inputs may be None when the app first loads
    left_deg  = left_deg or 8.65
    right_deg = right_deg or 16.0
    z_step    = z_step or 0.2
    n_starts  = max(1, int(n_starts or 1000))
    max_start = max(10, int(max_start or 1_000_000))

    random.seed(42)
    # Deal with the case n_starts >= max_start-2
    population = range(2, max_start)
    starts = random.sample(population, min(n_starts, len(population)))

    fig = go.Figure()
    for s in starts:
        xs, ys, zs = collatz_path_3d(s, left_deg, right_deg, z_step, scheme)
        # fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs,
        #                            mode='lines',
        stride = 10                      # draw every 10th label → tweak to taste
        labels = [f"n={v}" if (i % stride == 0 or i == len(vals)-1) else ""
          for i, v in enumerate(vals)]

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='lines+text',           # show the numbers, too
            text=labels,
            textposition="top center",
            textfont=dict(size=8, color=colour),
            line=dict(width=1, color=colour_for(s, max_start)),
            opacity=0.3,
            hoverinfo='skip')
        )

    # Highlight the record trajectory for reference
    hero = 837_799 if scheme == 'binary' else 91
    if hero < max_start:
        xs, ys, zs = collatz_path_3d(hero, left_deg, right_deg, z_step, scheme)
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs,
                                   mode='lines',
                                   line=dict(width=4, color='black'),
                                   name=f'Hero {hero}'))
    fig.update_layout(showlegend=False,
                      scene=dict(xaxis=dict(visible=False),
                                 yaxis=dict(visible=False),
                                 zaxis=dict(visible=False)),
                      margin=dict(l=0, r=0, t=0, b=0))

    md = r"""
### Model sketch
Let $C(n)$ be the *Collatz map*
$$
C(n)=\begin{cases}
\tfrac{n}{2}, & n\equiv0\pmod2,\\[4pt]
3n+1, & n\equiv1\pmod2.
\end{cases}
$$
For a chosen start $n_0$, we iterate $n_{k+1}=C(n_k)$ until reaching $1$.

* **2‑D turtle rule** — at each step the heading rotates by $\pm\theta$ and
  the step length scales like $1/\ln(n_{k+1})$.
* **Vertical axis** — climbs a constant $\Delta z$ each iteration, so overall
  height encodes the *stopping time*.

"""

    return fig, md


# ───────────────────────────────────────────────────────────────────────────────
# Main – run the dev server
# ───────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # app.run_server(debug=True)
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)


