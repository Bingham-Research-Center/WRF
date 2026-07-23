# Uinta Cold-Pool Waves: How It Would Be Done

This is a concept reference, not approval to stage data or run WPS/WRF.

## Verdict

- Basin-scale seiche/internal-wave detection is feasible at `333 m`; a whole-basin
  `<100 m` grid is not required for the first test.
- A `111 m` nest is useful for canyon inflows and near-slope structure. Add a
  `37 m` canyon-mouth nest only after the `111 m` proof is stable.
- One deterministic night can reveal a candidate mode. Attribution needs repeated
  nights or sensitivity members because drainage pulses, gravity waves, forcing,
  nest boundaries, and numerical modes can share periods.

## Forcing And Domain Ladder

1. Use one extended `00/06/12/18Z` HRRR cycle, preferably initialized at least one
   daytime transition before sunset; do not splice hourly analyses.
2. In `brc-tools-2026`, inventory and retain raw HRRR GRIB for WPS. The existing
   `NWPSource("hrrr")` path is for analysis/plots, not yet a WPS forcing contract.
3. Prove the required native-atmosphere plus surface/soil/snow fields with John's
   WPS `Vtable.raphrrr`; require a manifest, contract, `met_em` field report, and
   nonzero soil levels before `real.exe`.
4. Use approximately `3 km -> 1 km -> 333 m -> 111 m`, odd 3:1 ratios, and one-way
   nesting (`feedback = 0`) at the microscale transition. Keep `333 m` over the entire
   basin and surrounding rims; a small canyon nest cannot diagnose a basin mode.
5. Keep forcing/nest boundaries far from the basin and wave-reflection region. Do
   not nudge the cold pool or the fine nest; outer-domain, above-PBL nudging is a
   separate sensitivity, not the control.

HRRR is the first source: local Herbie `2026.3.0` supports `sfc`, `prs`, `nat`, and
`subh`, and the local WPS has `Vtable.raphrrr`. RRFS remains a prototype until its
scheduled operational implementation on 2026-10-06; its products are still moving.
WoFS is a severe-weather, limited-domain experimental system, not a dependable
winter IC/LBC archive for this experiment.

## Sub-100 m WRF Gotchas

- `3 arc-sec` terrain is about one source sample per `111 m` cell in Utah and is
  upsampled at `37 m`. Use at least `1 arc-sec` terrain for a real `<100 m` claim;
  land cover, roughness, soil, and snow deserve comparable scrutiny.
- Fine unsmoothed terrain produces skew terrain-following cells, pressure-gradient
  error, grid-scale roughness, and vertical-CFL failure. Terrain smoothing is an
  experimental factor because it can remove the canyon geometry being studied.
- Near `100 m`, use an LES-style fine-domain control: no PBL scheme,
  `diff_opt = 2`, and `km_opt = 2` or `3`. A scale-aware transition closure is a
  sensitivity. Do not extend mesoscale YSU/MYJ blindly onto the finest nest.
- Target roughly `5-10 m` lowest-layer spacing and many levels in the lowest
  `0.5-1 km`. Coarse vertical spacing defeats the horizontal refinement.
- Start with the WRF `time_step ~ 6*DX(km)` ceiling (`~0.6 s` at `100 m`) and expect
  smaller values over steep winter terrain. Monitor horizontal and vertical CFL,
  not merely completion.
- Surface/snow-state imbalance can dominate the nocturnal signal. HRRR uses a
  different land system from a Noah-based WRF run; retain skin temperature, snow,
  and soil profiles, allow substantial pre-sunset spin-up, and budget the surface
  fluxes.
- A `111 m` cold-pool run is still turbulence-grey-zone science. Treat closure,
  terrain smoothing, vertical grid, and initialization time as the minimum
  sensitivity set.

## Deficit Energetics

Choose a fixed, documented reference. The current `brc-tools` convention uses
crest-level potential temperature in each column:

```text
dtheta = max(theta_crest - theta, 0)
H      = (cp/g) integral(dtheta dp)                 [J m-2]
F      = (cp/g) integral(dtheta u_h dp)             [W m-1]
Phi    = integral_gate(F dot n ds)                  [W]
```

Equivalently, `rho*cp*dtheta` is a potential-temperature deficit density in
`J m-3`, and its resolved advective flux through a canyon plane is in watts.
Gigawatts are dimensionally and physically plausible for a broad, deep, cold
drainage layer. Call this **heat-deficit transport**, not literal negative internal
energy. For an enthalpy-temperature deficit, include the Exner conversion from
`dtheta` to `dT`.

`Phi` is not by itself the canyon's causal contribution to basin cooling. Close as
much of the volume budget as possible:

```text
d/dt integral_volume(rho cp dtheta dV)
    = net resolved boundary transport + surface/diabatic terms
      + subgrid/vertical/reference-motion/numerical residual.
```

The clean `brc-tools` branch `jrl/x8-deficit-diagnostics` already has `H`, `F`,
`-div(F)`, canyon-gate `Phi` in GW, bulk depth/speed/Froude proxies, and an explicitly
labelled unresolved budget. Reuse it; do not recode these diagnostics in `ub-wx`.

## What Would Establish A Seiche

Track the deficit-weighted centroid, cold-pool top/isentrope displacement, total
deficit, and along-basin velocity. A seiche candidate has:

- a narrow, repeatable spectral peak and basin-wide coherence;
- standing-mode nodes/antinodes and phase reversal across the basin;
- near-quadrature between interface displacement and along-basin velocity;
- oscillating centroid/redistribution with much less oscillation in total deficit.

Use `T1 ~ 2L/sqrt(g' h)`, `g' = g*dtheta/theta0`, only as a mode-period prior.
Whole-basin modes will likely be hours; canyon/cold-lake pulses can be tens of
minutes. One-minute sampling is ample for both, but one night may contain too few
whole-basin cycles for a defensible spectrum.

## Output And Visual Story

- Full science state every `10-30 min`, restarts every `1-3 h`, and a reduced
  auxiliary stream every `1 min` on the analysis nests. Do not write full WRF
  history every minute.
- Reduced 3-D stream: `U,V,W,T,P,PB,PH,PHB` plus water/TKE fields needed by the
  chosen closure. Reduced surface stream: `T2,U10,V10,TSK,HFX,LH,GLW,SWDOWN` and
  snow diagnostics. Use runtime I/O/auxhist and benchmark I/O quilting.
- `ub-wx`: assemble frames/animations and keep case-specific storytelling.
  `brc-tools`: own reusable WRF extraction, deficit, sections, and rendering.
- Primary animation: translucent 3-D `dtheta` or `rho cp dtheta` volume above the
  terrain, deficit isosurfaces, and drainage streamlines.
- Companion panels: `H` with `F` arrows and canyon gates; theta/wind sections;
  gate `Phi(t)` in GW; total deficit and `dE/dt`; deficit centroid; Hovmoller and
  modal spectrum/phase.

## Evidence Links

- [WRF guidance for approximately 100 m real-data LES](https://www2.mmm.ucar.edu/wrf/users/wrf_users_guide/build/html/physics/pbl.html)
- [WRF nesting and time-step guidance](https://www2.mmm.ucar.edu/wrf/site/documentation/users_guide/running_wrf.html)
- [WRF reduced/auxiliary output controls](https://www2.mmm.ucar.edu/wrf/site/users_guide/output.html)
- [Herbie HRRR products](https://herbie.readthedocs.io/en/stable/user_guide/background/model-info/hrrr.html)
- [NWS RRFS/REFS implementation notice, updated 2026-07-06](https://www.weather.gov/media/notification/pdf_2026/scn26-048_RRFS_and_REFS_Implementation.aab.pdf)
- [NOAA WoFS scope and availability](https://www.nssl.noaa.gov/projects/wof/)
- [Observed cold-air-lake waves and oscillating drainage](https://doi.org/10.2151/jmsj1965.74.2_247)
- [A 111 m WRF stable-valley case study](https://doi.org/10.3390/atmos12081063)
