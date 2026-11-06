"""
Coastal Zone Explorer page.
Lets the user choose any of the 5 coastal divisions (or all-India) and get
a fully scoped cyclone risk report: track, cities, impact, alerts, history.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.data_generator import (
    COASTAL_ZONES, ALL_ZONES_KEY,
    get_zone_cities, generate_zone_track, generate_zone_impact,
    generate_historical_cyclones, generate_meteorological_data,
    get_intensity_label,
)


RISK_COLORS = {
    "CRITICAL": ("#2D0A0A", "#FF8A80"),
    "HIGH":     ("#2D1200", "#FFAB40"),
    "MODERATE": ("#2D2500", "#FFD740"),
    "LOW":      ("#0A2D0A", "#69F0AE"),
}


def render():
    st.markdown("## 🗺️ Coastal Zone Explorer")
    st.markdown(
        '<p style="color:#8B949E">Select any coastal division to get a focused cyclone risk report '
        '— tracks, city-level impact, alerts, evacuation readiness, and historical records.</p>',
        unsafe_allow_html=True,
    )

    # ── Zone selector ────────────────────────────────────────────
    zone_options = [ALL_ZONES_KEY] + list(COASTAL_ZONES.keys())
    selected_zone = st.session_state.get("selected_zone", ALL_ZONES_KEY)

    # Visual zone picker cards
    st.markdown("### 🧭 Choose Your Coastal Zone")
    card_cols = st.columns(6)

    # All India
    with card_cols[0]:
        is_sel = selected_zone == ALL_ZONES_KEY
        if st.button(
            "🌏\nAll India", key="zone_all",
            use_container_width=True,
            type="primary" if is_sel else "secondary",
        ):
            st.session_state["selected_zone"] = ALL_ZONES_KEY
            st.rerun()

    for i, (zkey, z) in enumerate(COASTAL_ZONES.items()):
        with card_cols[i + 1]:
            is_sel = selected_zone == zkey
            short  = z["label"].replace(" Coast","").replace(" Territories","")
            if st.button(
                f"{z['emoji']}\n{short}", key=f"zone_{z['id']}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state["selected_zone"] = zkey
                st.rerun()

    selected_zone = st.session_state.get("selected_zone", ALL_ZONES_KEY)

    st.divider()

    # ── Zone info banner ─────────────────────────────────────────
    if selected_zone == ALL_ZONES_KEY:
        _render_all_india()
    else:
        _render_zone(selected_zone, COASTAL_ZONES[selected_zone])


# ──────────────────────────────────────────────────────────────────
# All-India overview
# ──────────────────────────────────────────────────────────────────
def _render_all_india():
    st.markdown("### 🌏 All India Coastal Risk Overview")

    # Summary KPIs
    total_cities   = sum(len(z["cities"]) for z in COASTAL_ZONES.values())
    total_shelters = sum(z["shelters"]    for z in COASTAL_ZONES.values())
    total_ndrf     = sum(z["ndrf_teams"]  for z in COASTAL_ZONES.values())
    total_km       = 7516

    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi(c1, "Coastline Length", f"{total_km:,} km",   "#4FC3F7")
    _kpi(c2, "Coastal Zones",    "5",                   "#E6EDF3")
    _kpi(c3, "Monitored Cities", str(total_cities),     "#E6EDF3")
    _kpi(c4, "Cyclone Shelters", f"{total_shelters:,}", "#81C784")
    _kpi(c5, "NDRF Teams",       str(total_ndrf),       "#FFB74D")

    st.markdown("")

    col_map, col_zones = st.columns([1.5, 1])

    with col_map:
        st.markdown("#### 🗺️ India Coastline — Zone Map")
        fig = go.Figure()

        all_cities = get_zone_cities(ALL_ZONES_KEY)
        for zkey, z in COASTAL_ZONES.items():
            z_cities = [c for c in all_cities if c["zone"] == z["label"]]
            if not z_cities:
                continue
            lats = [c["lat"] for c in z_cities]
            lons = [c["lon"] for c in z_cities]
            names = [c["name"] for c in z_cities]
            pops  = [c.get("pop_M", 0.1) for c in z_cities]

            fig.add_trace(go.Scattergeo(
                lat=lats, lon=lons,
                mode="markers+text",
                marker=dict(
                    size=[max(8, p * 2.5 + 6) for p in pops],
                    color=z["color"], opacity=0.85,
                    line=dict(color="#E6EDF3", width=1),
                ),
                text=names, textposition="top right",
                textfont=dict(size=9, color=z["color"]),
                name=f"{z['emoji']} {z['label']}",
                hovertemplate="<b>%{text}</b><br>Zone: " + z["label"] + "<extra></extra>",
            ))

        fig.update_geos(
            scope="asia", center=dict(lat=15, lon=80), projection_scale=3.8,
            showland=True, landcolor="#1A1F2E",
            showocean=True, oceancolor="#0A1628",
            showcoastlines=True, coastlinecolor="#E84545",
            showcountries=True, countrycolor="#30363D",
        )
        fig.update_layout(
            paper_bgcolor="#0D1117", margin=dict(l=0, r=0, t=0, b=0), height=460,
            legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3"), x=0.01, y=0.99),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_zones:
        st.markdown("#### 📋 Zone Summary")
        for zkey, z in COASTAL_ZONES.items():
            risk_badge_color = (
                "#FF8A80" if "Very High" in z["risk_profile"] or "Critical" in z["risk_profile"]
                else "#FFAB40" if "High" in z["risk_profile"]
                else "#FFD740" if "Moderate" in z["risk_profile"]
                else "#69F0AE"
            )
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-left:4px solid {z["color"]};'
                f'border-radius:8px;padding:12px 14px;margin-bottom:8px;cursor:pointer">'
                f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span style="font-weight:600;color:#E6EDF3;font-size:0.95rem">{z["emoji"]} {z["label"]}</span>'
                f'<span style="font-size:0.72rem;background:#21262D;color:{z["color"]};'
                f'padding:2px 8px;border-radius:10px">{z["sea"]}</span></div>'
                f'<div style="font-size:0.78rem;color:#8B949E;margin-top:4px">'
                f'{"  ·  ".join(z["states"])}</div>'
                f'<div style="font-size:0.75rem;color:{risk_badge_color};margin-top:3px">'
                f'⚠️ {z["risk_profile"][:55]}{"..." if len(z["risk_profile"]) > 55 else ""}</div>'
                f'<div style="font-size:0.72rem;color:#8B949E;margin-top:4px">'
                f'🏠 {z["shelters"]} shelters &nbsp;·&nbsp; 🚑 {z["ndrf_teams"]} NDRF teams &nbsp;·&nbsp; '
                f'📅 Season: {z["peak_season"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # Historical cyclone frequency by zone
    st.markdown("#### 📊 Historical Cyclone Frequency by Zone")
    freq_data = {z["label"]: len(z["historical_hits"]) for z in COASTAL_ZONES.values()}
    freq_colors = [z["color"] for z in COASTAL_ZONES.values()]
    fig_freq = go.Figure(go.Bar(
        x=list(freq_data.keys()),
        y=list(freq_data.values()),
        marker_color=freq_colors,
        text=list(freq_data.values()),
        textposition="outside",
        textfont=dict(color="#E6EDF3"),
    ))
    fig_freq.update_layout(
        paper_bgcolor="#161B22", plot_bgcolor="#161B22",
        height=240, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(color="#8B949E"),
        yaxis=dict(title="Major Cyclones (2007–2023)", color="#8B949E", gridcolor="#30363D"),
    )
    st.plotly_chart(fig_freq, use_container_width=True)


# ──────────────────────────────────────────────────────────────────
# Single zone view
# ──────────────────────────────────────────────────────────────────
def _render_zone(zkey: str, z: dict):
    # Header banner
    st.markdown(
        f'<div style="background:#161B22;border:2px solid {z["color"]};border-radius:12px;'
        f'padding:16px 22px;margin-bottom:16px">'
        f'<h2 style="color:{z["color"]};margin:0">{z["emoji"]} {z["label"]}</h2>'
        f'<p style="color:#8B949E;margin:4px 0 0">'
        f'🌊 {z["sea"]} &nbsp;·&nbsp; States: {"  ·  ".join(z["states"])} &nbsp;·&nbsp; '
        f'Peak Season: {z["peak_season"]}</p>'
        f'<p style="color:#E6EDF3;font-size:0.85rem;margin-top:6px">⚠️ {z["risk_profile"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # KPIs
    cities     = z["cities"]
    total_pop  = sum(c.get("pop_M", 0) for c in cities)
    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi(c1, "Monitored Cities", str(len(cities)),       z["color"])
    _kpi(c2, "Population",       f"{total_pop:.1f} M",   "#E6EDF3")
    _kpi(c3, "Cyclone Shelters", str(z["shelters"]),      "#81C784")
    _kpi(c4, "NDRF Teams",       str(z["ndrf_teams"]),    "#FFB74D")
    _kpi(c5, "Cyclone Freq.",    z["cyclone_freq"][:18],  "#E84545")

    st.markdown("")

    # ── Tab layout ────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Zone Map & Track",
        "📊 City Risk Dashboard",
        "🚨 Alerts & Preparedness",
        "📜 Historical Cyclones",
    ])

    # ── TAB 1: Map ────────────────────────────────────────────────
    with tab1:
        col_map, col_info = st.columns([1.6, 1])

        with col_map:
            track_df = generate_zone_track(zkey, n_points=20)
            past_df  = track_df[~track_df["is_forecast"]]
            fore_df  = track_df[track_df["is_forecast"]]
            city_df  = pd.DataFrame(cities)

            fig = go.Figure()

            # Zone bounding box shading
            fig.add_trace(go.Scattergeo(
                lat=[z["lat_min"], z["lat_min"], z["lat_max"], z["lat_max"], z["lat_min"]],
                lon=[z["lon_min"], z["lon_max"], z["lon_max"], z["lon_min"], z["lon_min"]],
                mode="lines", fill="toself",
                fillcolor=z["color"].replace("#","rgba(") + ",0.08)",
                line=dict(color=z["color"], width=1.5, dash="dot"),
                name=f"{z['label']} Zone",
                showlegend=True,
            ))

            # Past track
            if not past_df.empty:
                fig.add_trace(go.Scattergeo(
                    lat=past_df["lat"], lon=past_df["lon"],
                    mode="lines+markers",
                    line=dict(color="#8B949E", width=2, dash="dot"),
                    marker=dict(size=7, color="#8B949E"),
                    name="Observed Track",
                ))

            # Forecast track
            fig.add_trace(go.Scattergeo(
                lat=fore_df["lat"], lon=fore_df["lon"],
                mode="lines+markers",
                line=dict(color="#E84545", width=3),
                marker=dict(
                    size=10,
                    color=fore_df["color"],
                    line=dict(color="#E6EDF3", width=1.5),
                ),
                name="Forecast Track",
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} kts · +%{customdata[2]}h<extra></extra>",
                customdata=list(zip(fore_df["intensity"], fore_df["wind_speed_kts"], fore_df["hours_offset"])),
            ))

            # Zone cities — sized by population
            fig.add_trace(go.Scattergeo(
                lat=city_df["lat"], lon=city_df["lon"],
                mode="markers+text",
                marker=dict(
                    size=[max(9, c.get("pop_M", 0.1) * 3 + 8) for c in cities],
                    color=z["color"], opacity=0.9,
                    line=dict(color="#E6EDF3", width=1.2),
                ),
                text=city_df["name"], textposition="top center",
                textfont=dict(size=10, color="#E6EDF3"),
                name="Zone Cities",
                hovertemplate="<b>%{text}</b><extra></extra>",
            ))

            center_lat = (z["lat_min"] + z["lat_max"]) / 2
            center_lon = (z["lon_min"] + z["lon_max"]) / 2
            fig.update_geos(
                scope="asia",
                center=dict(lat=center_lat, lon=center_lon),
                projection_scale=z["zoom"],
                showland=True,    landcolor="#1A1F2E",
                showocean=True,   oceancolor="#0A1628",
                showcoastlines=True, coastlinecolor="#E84545",
                showcountries=True, countrycolor="#30363D",
            )
            fig.update_layout(
                paper_bgcolor="#0D1117", margin=dict(l=0, r=0, t=0, b=0), height=450,
                legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3"), x=0.01, y=0.99),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            st.markdown(f"#### 🌀 Active Cyclone Track in {z['label']}")

            # Current system
            cur = track_df.loc[track_df["hours_offset"].abs().idxmin()]
            near_coast = track_df[track_df["hours_offset"] >= 0].head(3)

            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:14px">'
                f'<div style="color:#E84545;font-weight:700;font-size:1.05rem">⚠️ CYCLONE VARUNA</div>'
                f'<div style="margin-top:8px;font-size:0.85rem;color:#E6EDF3">'
                f'<b>Current Position:</b> {cur["lat"]}°N, {cur["lon"]}°E<br>'
                f'<b>Intensity:</b> {cur["intensity"]}<br>'
                f'<b>Wind Speed:</b> {cur["wind_speed_kts"]} kts<br>'
                f'<b>Pressure:</b> {cur["pressure_hpa"]} hPa<br>'
                f'<b>Tracking toward:</b> {z["label"]}'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            # Forecast steps
            st.markdown("**📍 Forecast Positions**")
            for _, row in near_coast.iterrows():
                eta_h = int(row["hours_offset"])
                st.markdown(
                    f'<div style="background:#0D1117;border-left:3px solid {row["color"]};'
                    f'border-radius:4px;padding:8px 12px;margin-bottom:5px;font-size:0.82rem">'
                    f'<b style="color:#E6EDF3">+{eta_h}h</b> &nbsp; '
                    f'{row["lat"]}°N, {row["lon"]}°E &nbsp;·&nbsp; '
                    f'<span style="color:{row["color"]}">{row["intensity"]}</span> &nbsp;·&nbsp; '
                    f'{row["wind_speed_kts"]} kts'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")
            st.markdown("**🏔️ Terrain Risk**")
            st.markdown(
                f'<div style="background:#2D1500;border-radius:6px;padding:10px 14px;'
                f'font-size:0.82rem;color:#FFD740">{z["elevation_risk"]}</div>',
                unsafe_allow_html=True,
            )

    # ── TAB 2: City Risk ──────────────────────────────────────────
    with tab2:
        st.markdown(f"#### 📊 District & City Risk Assessment — {z['label']}")
        impacts = generate_zone_impact(zkey)
        imp_df  = pd.DataFrame(impacts)

        # Risk cards
        risk_cols = st.columns(min(len(impacts), 4))
        for i, imp in enumerate(impacts[:4]):
            bg, tc = RISK_COLORS.get(imp["risk_level"], ("#161B22", "#E6EDF3"))
            with risk_cols[i]:
                st.markdown(
                    f'<div style="background:{bg};border-radius:10px;padding:14px;text-align:center;margin-bottom:8px">'
                    f'<div style="font-size:1.1rem;font-weight:700;color:{tc}">{imp["overall_risk"]:.0f}%</div>'
                    f'<div style="font-size:0.95rem;font-weight:600;color:#E6EDF3;margin:4px 0">{imp["city"]}</div>'
                    f'<div style="font-size:0.72rem;color:#8B949E">{imp.get("district","")}</div>'
                    f'<div style="font-size:0.72rem;color:{tc};font-weight:600;margin-top:4px">{imp["risk_level"]}</div>'
                    f'<div style="font-size:0.72rem;color:#8B949E;margin-top:2px">Pop: {imp["pop_M"]:.1f}M</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("")
        col_chart, col_table = st.columns([1.2, 1])

        with col_chart:
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Bar(
                x=imp_df["city"], y=imp_df["wind_risk"],  name="Wind",  marker_color="#E84545"))
            fig_risk.add_trace(go.Bar(
                x=imp_df["city"], y=imp_df["surge_risk"], name="Surge", marker_color="#FF7043"))
            fig_risk.add_trace(go.Bar(
                x=imp_df["city"], y=imp_df["flood_risk"], name="Flood", marker_color="#4FC3F7"))
            fig_risk.update_layout(
                barmode="group",
                paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                height=300, margin=dict(l=0, r=0, t=20, b=0),
                xaxis=dict(color="#8B949E", tickangle=25, tickfont=dict(size=9)),
                yaxis=dict(title="Risk %", color="#8B949E", gridcolor="#30363D", range=[0, 110]),
                legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3")),
                title=dict(text="Risk Breakdown by City", font=dict(color="#E6EDF3")),
            )
            st.plotly_chart(fig_risk, use_container_width=True)

            # Population at risk donut
            risk_pop = imp_df.groupby("risk_level")["pop_M"].sum().reset_index()
            rc = {"CRITICAL":"#880E4F","HIGH":"#E53935","MODERATE":"#FF6F00","LOW":"#43A047"}
            fig_pop = go.Figure(go.Pie(
                labels=risk_pop["risk_level"], values=risk_pop["pop_M"].round(2),
                marker_colors=[rc.get(r, "#8B949E") for r in risk_pop["risk_level"]],
                hole=0.5,
                hovertemplate="%{label}: %{value:.2f}M people<extra></extra>",
            ))
            fig_pop.update_layout(
                paper_bgcolor="#161B22", height=220,
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(color="#E6EDF3"),
                legend=dict(bgcolor="#161B22"),
                title=dict(text="Population at Risk by Level", font=dict(color="#E6EDF3")),
            )
            st.plotly_chart(fig_pop, use_container_width=True)

        with col_table:
            st.markdown("**📋 Full City Risk Table**")
            display_df = imp_df[["city","district","pop_M","dist_km","wind_risk",
                                  "surge_risk","flood_risk","overall_risk","risk_level"]].rename(columns={
                "city":"City","district":"District","pop_M":"Pop (M)",
                "dist_km":"Distance (km)","wind_risk":"Wind%",
                "surge_risk":"Surge%","flood_risk":"Flood%",
                "overall_risk":"Overall%","risk_level":"Risk"
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=530)

    # ── TAB 3: Alerts ────────────────────────────────────────────
    with tab3:
        st.markdown(f"#### 🚨 Alerts & Preparedness — {z['label']}")
        impacts = generate_zone_impact(zkey)

        # Overall zone alert
        top = impacts[0]
        top_level = top["risk_level"]
        alert_map = {
            "CRITICAL": ("🔴 RED ALERT",    "red",
                         "IMMEDIATE EVACUATION of all coastal areas within 10 km. All ports closed. Schools & offices shut."),
            "HIGH":     ("🟠 ORANGE ALERT", "orange",
                         "Prepare for evacuation. Fishermen must return to shore. Stock emergency supplies."),
            "MODERATE": ("🟡 YELLOW ALERT", "yellow",
                         "Stay alert. Monitor IMD updates. Identify nearest cyclone shelter."),
            "LOW":      ("🟢 GREEN ADVISORY","green",
                         "No immediate threat. Continue routine monitoring."),
        }
        label, color, action = alert_map.get(top_level, alert_map["MODERATE"])
        st.markdown(
            f'<div class="alert-{color}">'
            f'<strong>{label} — {z["label"]}</strong><br>'
            f'{action}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        col_al, col_prep = st.columns(2)

        with col_al:
            st.markdown("**📍 City-Level Alert Status**")
            for imp in impacts:
                bg, tc = RISK_COLORS.get(imp["risk_level"], ("#161B22", "#E6EDF3"))
                icon_map = {"CRITICAL":"🔴","HIGH":"🟠","MODERATE":"🟡","LOW":"🟢"}
                icon = icon_map.get(imp["risk_level"], "⚪")
                st.markdown(
                    f'<div style="background:{bg};border-radius:7px;padding:9px 14px;'
                    f'margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">'
                    f'<div><span style="font-weight:600;color:#E6EDF3">{icon} {imp["city"]}</span>'
                    f'<br><span style="font-size:0.75rem;color:#8B949E">{imp.get("district","")}</span></div>'
                    f'<div style="text-align:right">'
                    f'<span style="color:{tc};font-weight:700;font-size:0.82rem">{imp["risk_level"]}</span><br>'
                    f'<span style="font-size:0.72rem;color:#8B949E">Risk: {imp["overall_risk"]:.0f}%</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        with col_prep:
            st.markdown("**🛡️ Preparedness Checklist**")
            timeline_items = [
                ("🔴 Now (0–6h)",   [
                    "Activate State EOC and NDRF pre-positioning",
                    "Issue public warning via All India Radio & TV",
                    "Recall all fishing vessels from sea",
                    f"Open {z['shelters']} cyclone shelters across zone",
                ]),
                ("🟠 6–24h",       [
                    "Begin phased evacuation of vulnerable coastal hamlets",
                    "Pre-position relief material at staging areas",
                    f"Deploy {z['ndrf_teams']} NDRF teams to district HQs",
                    "Secure critical infrastructure (power, water, hospitals)",
                ]),
                ("🟡 24–48h",      [
                    "Complete evacuation of 10 km coastal strip",
                    "Activate emergency food & water distribution",
                    "Place Coast Guard and Navy on SAR alert",
                    "Coordinate with Railways for special evacuation trains",
                ]),
                ("🟢 Post-Landfall",[
                    "Deploy SAR teams for rescue operations",
                    "Establish medical camps in affected districts",
                    "Restore roads, power, and communication",
                    "Initiate damage assessment and relief distribution",
                ]),
            ]
            for phase, items in timeline_items:
                st.markdown(f'<div style="font-weight:600;color:#E6EDF3;margin:10px 0 4px">{phase}</div>',
                            unsafe_allow_html=True)
                for item in items:
                    st.markdown(
                        f'<div style="font-size:0.82rem;color:#8B949E;padding:3px 0 3px 12px;'
                        f'border-left:2px solid #30363D">✓ {item}</div>',
                        unsafe_allow_html=True,
                    )

    # ── TAB 4: Historical ────────────────────────────────────────
    with tab4:
        st.markdown(f"#### 📜 Historical Cyclones affecting {z['label']}")

        # Zone-specific historical hits
        st.markdown("**Major Cyclones (Recent History)**")
        for hit in z["historical_hits"]:
            st.markdown(
                f'<div style="background:#161B22;border-left:3px solid {z["color"]};'
                f'border-radius:4px;padding:8px 14px;margin-bottom:5px;font-size:0.85rem;color:#E6EDF3">'
                f'🌀 {hit}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")

        # Filter historical data to this zone's states
        hist_df = generate_historical_cyclones()
        zone_states = z["states"]
        zone_hist   = hist_df[hist_df["landfall"].apply(
            lambda lf: any(s.lower() in lf.lower() for s in zone_states)
        )]

        if not zone_hist.empty:
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                fig_h = go.Figure(go.Bar(
                    x=zone_hist["name"] + "\n" + zone_hist["year"].astype(str),
                    y=zone_hist["peak_ws"],
                    marker_color=[
                        "#880E4F" if v >= 120 else "#E53935" if v >= 90 else
                        "#FF7043" if v >= 64 else "#FFB74D"
                        for v in zone_hist["peak_ws"]
                    ],
                    text=zone_hist["peak_ws"].astype(str) + " kts",
                    textposition="outside",
                    textfont=dict(size=9, color="#8B949E"),
                ))
                fig_h.update_layout(
                    paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                    height=280, margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(color="#8B949E", tickangle=30, tickfont=dict(size=8)),
                    yaxis=dict(title="Peak Wind (kts)", color="#8B949E", gridcolor="#30363D"),
                    title=dict(text=f"Peak Intensity — {z['label']}", font=dict(color="#E6EDF3")),
                )
                st.plotly_chart(fig_h, use_container_width=True)

            with col_h2:
                st.dataframe(
                    zone_hist[["name","year","peak_cat","deaths","damage_crore","landfall"]].rename(columns={
                        "name":"Cyclone","year":"Year","peak_cat":"Category",
                        "deaths":"Deaths","damage_crore":"Damage (₹Cr)","landfall":"Landfall"
                    }),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info(f"No historical landfall records specifically for {z['label']} in the dataset — check All-India view.")


# ── Helper ───────────────────────────────────────────────────────

def _kpi(col, label, value, color):
    with col:
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;'
            f'padding:13px 8px;text-align:center;margin-bottom:8px">'
            f'<div style="font-size:1.4rem;font-weight:700;color:{color}">{value}</div>'
            f'<div style="font-size:0.72rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.05em;margin-top:3px">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
