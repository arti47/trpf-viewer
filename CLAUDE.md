# TRPF #134 View Simulator — CLAUDE.md

Single-file HTML app (`trpf-view-sim-v4.html`, ~1.6 MB, data inlined). Live artifact: https://claude.ai/artifact/KnU43WCpnCdH9urKJHWkp8
Purpose: physically-based view from Tanjong Rhu Parc Front (TRPF) Blk 32A #134 toward Marina East / Marina Bay, now vs future build-out.

## Working rules
- Terse, technical. Edit in place (str_replace-style), no full rewrites. No verification output unless asked.
- Progress reporting: do not narrate work; report only progress percentages (5%, 10%, … 100%). Final reply = "100%" + minimal result.
- Every change must keep the app faithful to these rules/spec (physics, data, defaults above).
- Git: after committing on the working branch, always merge into `main` and push `main` (owner standing instruction).
- Batch changes per request. Keep this file current after every change (enforced by Stop hook `.claude/hooks/spec-sync.sh`: blocks finishing if the HTML is newer than this file).

## Coordinate frame
- Local metres: origin = TRPF URA parcel centroid (1.29682N, 103.87826E); x = East, z = North, y = up.
- x = (lon−103.87826)·111291, z = (lat−1.29682)·110574.
- Site plan (1284×1009 px) ↔ world: s = 0.225 m/px, th ≈ −0.29°, tx = 670, ty = 470 (`GEO.site`); fitted to the URA parcel (IoU 0.92).

## Data (inlined as `const GEO = {...}`)
- `lu`: URA Master Plan 2025 land use, merged per class (0 water, 1 road, 2 park, 3 residential, 4 commercial/other, 5 reserve, 6 utility). Region x −5200..2600, z −4200..1800.
- `b`: buildings `[h, est, name, flatXZ]` — OSM (3,660; height/levels; est=1 if from parcel GPR: res storeys ≈ GPR×8) + MP2025 HDB footprints not in OSM (457). Manual CBD overrides (Guoco 290, UOB/Republic 280, Sail 245…). MBS SkyPark added as elevated prism (base 191, top 200).
- `parcels`: future-development polygons: N, S (Marina East "SDP" residential, 16.3/18.6 ha), RE (106 ha), RS (38 ha) reserves, R1..R9 reserves ≤700 m (R2 duplicate of RE excluded via area<50 ha), + E1/E2 (GPR 3.7/3.5, east of TRPF, appended in JS).
- `blocks`: TRPF blocks as rotated boxes (0.5 m raster of HDB floor plans, 11.75 px/m): 31A, 32A, 33A (exact), 31B (traced from site plan), MSCP (top = 12th storey, 37.0 m), ESS (7 m). `gapFitted` 20.1 m (31A–32A, default).
- `spots`: #134 windows (living, br3, br2, mbrS; all face 170.3°). No east window (owner-confirmed).
- `roads`: OSM at-grade ribbons `[cls, width, pts]`; `decks`: bridge/viaduct pieces `[name, base, top, quad]` (7.5 m per OSM layer; Benjamin Sheares Bridge 16/28 m); `piers`. Tunnels (KPE/MCE) omitted.
- Site plan image base64 (`SITE_IMG_SRC`).

## Geometry / physics
- Everything is a prism (plan polygon CCW, base..h). Spatial grid 40 m + DDA (`candidates`), `planIntervals`, `prismHit` (curvature-apparent heights).
- Earth curvature + refraction k=0.13 (R_eff = R/(1−k)); sea-horizon dip; Koschmieder haze T = e^(−3.912 d/V); NOAA solar position + Bennett refraction; Lambert shading; sun shadows.
- Storey: 2.8 m f2f, void deck 3.5 m; roof(30F) = 87.5 m. Eye = slab + posture eye offset.
- Metrics: gaze ray hit, ground dead-zone, frame-blocked % (raster mask: new / TRPF / existing+roads), landmark 7-sample visibility, binding roofline + floors-to-clear.

## Future development defaults (`state.groups`)
- N, S: plot-ratio driven — GPR 5.6, net 70%, high-rise 25–30F, frontage low-rise 10F (edge ≤45 m facing water ≤160 m / park ≤70 m). Sliders unclamped (GPR 1–10, net 30–100%, floors 5–60). Basis: Marina South GLS (Marina Gardens Lane GPR 5.6, 30F high-rise / 10F low-rise; Crescent 4.2).
- EA (E1/E2): on, 28–32F, tower count from GPR.
- RE, RS, RT: off, grid at spacing slider. Typology chips: HDB 34 m/100 m, Condo 30 m/100 m, Dense 34 m/75 m.
- Scenarios: movein (end-2029, all new off, date 2029-12-15), base, today, tall, low, top (30F), allres.

## Viewer / rendering
- Room bar: Living / Bedroom 3 / Bedroom 2 / Master (S); posture Standing 1.55 m·0.5 m, Sofa 1.2 m·3.5 m (living), Bed 0.9 m·2.5 m (bedrooms). Stand-back slider.
- Room interior (toggle): window wall w/ opening (W1: 0.55 m parapet, 2.2 m head), reveals, charcoal casement frame (mullions ~0.7 m, transom 1.8 m), clear glass, side walls, 2.6 m ceiling, floor. Off → hatched wall + dashed jamb lines.
- Trees (~15k, visual only): parks 22 m grid, roadside 16 m, TRPF lawn 14 m. Fixed cumulus field. Facade colour variation + window grid; night warm lines.
- Panes: section along gaze (2/4/6 km), 3D view (Expand ⤢, Esc), plan (site plan / area vector), sidebar.

## Open items / ideas
- Real Marina East layout when URA publishes plot ratios / GLS sites.
- Actual flyover clearances (ECP/KPE interchange).
- Night lighting (lit windows, streetlights), facade details (air-con ledges).
- Calibrate against a real photo from #134 after move-in (end-2029).
- Founders' Memorial / Bay East Garden expansion (low-rise) not modelled.

## Key timeline facts (as of Oct 2026)
- Marina East N/S: no GLS release; first sale before 2030 ≈20–30% (judgement); full build-out late 2030s+.
- Owner move-in: end-2029.
