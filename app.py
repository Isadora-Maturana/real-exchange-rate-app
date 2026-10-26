"""International Finance: bilateral real exchange rates from IMF monthly data."""
from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

BASE_URL = "https://api.imf.org/external/sdmx/3.0"
FIRST_MONTH = pd.Timestamp("1976-01-01")
PURPLE = "#4E2A84"
LILAC = "#A579D2"
# IMF CL_COUNTRY snapshot, refreshed from the live codelist on each cache renewal.
COUNTRY_SNAPSHOT = {'AFG': 'Afghanistan, Islamic Republic of', 'ALB': 'Albania', 'DZA': 'Algeria', 'ASM': 'American Samoa', 'AND': 'Andorra, Principality of', 'AGO': 'Angola', 'AIA': 'Anguilla, United Kingdom-British Overseas Territory', 'ATG': 'Antigua and Barbuda', 'ARG': 'Argentina', 'ARM': 'Armenia, Republic of', 'ABW': 'Aruba, Kingdom of the Netherlands', 'AUS': 'Australia', 'AUT': 'Austria', 'AZE': 'Azerbaijan, Republic of', 'BHS': 'Bahamas, The', 'BHR': 'Bahrain, Kingdom of', 'BGD': 'Bangladesh', 'BRB': 'Barbados', 'BLR': 'Belarus, Republic of', 'BEL': 'Belgium', 'BLZ': 'Belize', 'BEN': 'Benin', 'BMU': 'Bermuda', 'BTN': 'Bhutan', 'BOL': 'Bolivia', 'BIH': 'Bosnia and Herzegovina', 'BWA': 'Botswana', 'BRA': 'Brazil', 'VGB': 'British Virgin Islands', 'BRN': 'Brunei Darussalam', 'BGR': 'Bulgaria', 'BFA': 'Burkina Faso', 'BDI': 'Burundi', 'CPV': 'Cabo Verde', 'KHM': 'Cambodia', 'CMR': 'Cameroon', 'CAN': 'Canada', 'CYM': 'Cayman Islands', 'CAF': 'Central African Republic', 'TCD': 'Chad', 'CHL': 'Chile', 'CHN': "China, People's Republic of", 'COL': 'Colombia', 'COM': 'Comoros, Union of the', 'COD': 'Congo, Democratic Republic of the', 'COG': 'Congo, Republic of', 'COK': 'Cook Islands', 'CRI': 'Costa Rica', 'HRV': 'Croatia, Republic of', 'CUB': 'Cuba', 'CUW': 'Curaçao, Kingdom of the Netherlands', 'CYP': 'Cyprus', 'CZE': 'Czech Republic', 'CIV': "Côte d'Ivoire", 'DNK': 'Denmark', 'DJI': 'Djibouti', 'DMA': 'Dominica', 'DOM': 'Dominican Republic', 'ECU': 'Ecuador', 'EGY': 'Egypt, Arab Republic of', 'SLV': 'El Salvador', 'GNQ': 'Equatorial Guinea, Republic of', 'ERI': 'Eritrea, The State of', 'EST': 'Estonia, Republic of', 'SWZ': 'Eswatini, Kingdom of', 'ETH': 'Ethiopia, The Federal Democratic Republic of', 'FLK': 'Falkland Islands (Malvinas)', 'FRO': 'Faroe Islands', 'FJI': 'Fiji, Republic of', 'FIN': 'Finland', 'FRA': 'France', 'GUF': 'French Guiana', 'PYF': 'French Polynesia', 'GAB': 'Gabon', 'GMB': 'Gambia, The', 'GEO': 'Georgia', 'DEU': 'Germany', 'GHA': 'Ghana', 'GIB': 'Gibraltar', 'GRC': 'Greece', 'GRL': 'Greenland', 'GRD': 'Grenada', 'GLP': 'Guadeloupe', 'GUM': 'Guam', 'GTM': 'Guatemala', 'GGY': 'Guernsey', 'GIN': 'Guinea', 'GNB': 'Guinea-Bissau', 'GUY': 'Guyana', 'HTI': 'Haiti', 'VAT': 'Holy See', 'HND': 'Honduras', 'HKG': "Hong Kong Special Administrative Region, People's Republic of China", 'HUN': 'Hungary', 'ISL': 'Iceland', 'IND': 'India', 'IDN': 'Indonesia', 'IRN': 'Iran, Islamic Republic of', 'IRQ': 'Iraq', 'IRL': 'Ireland', 'IMN': 'Isle of Man', 'ISR': 'Israel', 'ITA': 'Italy', 'JAM': 'Jamaica', 'JPN': 'Japan', 'JEY': 'Jersey', 'JOR': 'Jordan', 'KAZ': 'Kazakhstan, Republic of', 'KEN': 'Kenya', 'KIR': 'Kiribati', 'PRK': "Korea, Democratic People's Republic of", 'KOR': 'Korea, Republic of', 'KOS': 'Kosovo, Republic of', 'KWT': 'Kuwait', 'KGZ': 'Kyrgyz Republic', 'LAO': "Lao People's Democratic Republic", 'LVA': 'Latvia, Republic of', 'LBN': 'Lebanon', 'LSO': 'Lesotho, Kingdom of', 'LBR': 'Liberia', 'LBY': 'Libya', 'LIE': 'Liechtenstein, Principality of', 'LTU': 'Lithuania, Republic of', 'LUX': 'Luxembourg', 'MAC': "Macao Special Administrative Region, People's Republic of China", 'MDG': 'Madagascar, Republic of', 'MWI': 'Malawi', 'MYS': 'Malaysia', 'MDV': 'Maldives', 'MLI': 'Mali', 'MLT': 'Malta', 'MHL': 'Marshall Islands, Republic of the', 'MTQ': 'Martinique', 'MRT': 'Mauritania, Islamic Republic of', 'MUS': 'Mauritius', 'MYT': 'Mayotte', 'MEX': 'Mexico', 'FSM': 'Micronesia, Federated States of', 'MDA': 'Moldova, Republic of', 'MCO': 'Monaco', 'MNG': 'Mongolia', 'MNE': 'Montenegro', 'MSR': 'Montserrat, United Kingdom-British Overseas Territory', 'MAR': 'Morocco', 'MOZ': 'Mozambique, Republic of', 'MMR': 'Myanmar', 'NAM': 'Namibia', 'NRU': 'Naoero, Republic of', 'NPL': 'Nepal', 'NLD': 'Netherlands, The', 'NCL': 'New Caledonia', 'NZL': 'New Zealand', 'NIC': 'Nicaragua', 'NER': 'Niger', 'NGA': 'Nigeria', 'NIU': 'Niue', 'NFK': 'Norfolk Island', 'MKD': 'North Macedonia, Republic of', 'MNP': 'Northern Mariana Islands', 'NOR': 'Norway', 'OMN': 'Oman', 'PAK': 'Pakistan', 'PLW': 'Palau, Republic of', 'PAN': 'Panama', 'PNG': 'Papua New Guinea', 'PRY': 'Paraguay', 'PER': 'Peru', 'PHL': 'Philippines', 'PCN': 'Pitcairn Islands', 'POL': 'Poland, Republic of', 'PRT': 'Portugal', 'PRI': 'Puerto Rico', 'QAT': 'Qatar', 'ROU': 'Romania', 'RUS': 'Russian Federation', 'RWA': 'Rwanda', 'REU': 'Réunion', 'WSM': 'Samoa', 'SMR': 'San Marino, Republic of', 'SAU': 'Saudi Arabia', 'SEN': 'Senegal', 'SRB': 'Serbia, Republic of', 'SYC': 'Seychelles', 'SLE': 'Sierra Leone', 'SGP': 'Singapore', 'SXM': 'Sint Maarten, Kingdom of the Netherlands', 'SVK': 'Slovak Republic', 'SVN': 'Slovenia, Republic of', 'SLB': 'Solomon Islands', 'SOM': 'Somalia', 'ZAF': 'South Africa', 'SSD': 'South Sudan, Republic of', 'ESP': 'Spain', 'LKA': 'Sri Lanka', 'SHN': 'St. Helena', 'KNA': 'St. Kitts and Nevis', 'LCA': 'St. Lucia', 'SPM': 'St. Pierre and Miquelon', 'VCT': 'St. Vincent and the Grenadines', 'SDN': 'Sudan', 'SUR': 'Suriname', 'SJM': 'Svalbard and Jan Mayen Islands', 'SWE': 'Sweden', 'CHE': 'Switzerland', 'SYR': 'Syrian Arab Republic', 'STP': 'São Tomé and Príncipe, Democratic Republic of', 'TWN': 'Taiwan Province of China', 'TJK': 'Tajikistan, Republic of', 'TZA': 'Tanzania, United Republic of', 'THA': 'Thailand', 'TLS': 'Timor-Leste, Democratic Republic of', 'TGO': 'Togo', 'TKL': 'Tokelau', 'TON': 'Tonga', 'TTO': 'Trinidad and Tobago', 'TUN': 'Tunisia', 'TKM': 'Turkmenistan', 'TCA': 'Turks and Caicos Islands', 'TUV': 'Tuvalu', 'TUR': 'Türkiye, Republic of', 'UGA': 'Uganda', 'UKR': 'Ukraine', 'ARE': 'United Arab Emirates', 'GBR': 'United Kingdom', 'USA': 'United States', 'VIR': 'United States Virgin Islands', 'URY': 'Uruguay', 'UZB': 'Uzbekistan, Republic of', 'VUT': 'Vanuatu', 'VEN': 'Venezuela, República Bolivariana de', 'VNM': 'Vietnam', 'WLF': 'Wallis and Futuna Islands', 'WBG': 'West Bank and Gaza', 'YEM': 'Yemen, Republic of', 'ZMB': 'Zambia', 'ZWE': 'Zimbabwe', 'ALA': 'Åland Islands', 'BES': 'Bonaire, Saint Eustatius and Saba', 'ATF': 'French Southern Territories', 'CWX': 'Curaçao and Sint Maarten', 'CSK': 'Czechoslovakia', 'DDR': 'German Democratic Republic', 'ANT': 'Netherlands Antilles', 'VDR': 'Vietnam, Democratic Republic of', 'SCG': 'Serbia and Montenegro', 'SUN': 'Union of Soviet Socialist Republics (USSR)', 'YAR': 'Yemen Arab Republic', 'YMD': "Yemen, People's Democratic Republic of", 'YUG': 'Yugoslavia, Socialist Federal Republic of', 'G163': 'Euro area', 'BLM': 'Saint Barthelemy', 'MAF': 'Saint Martin', 'SGS': 'South Georgia and the South Sandwich Islands', 'CXR': 'Christmas Island', 'CCK': 'Cocos Islands', 'ESH': 'Western Sahara', 'BVT': 'Bouvet Island', 'IOT': 'British Indian Ocean Territory', 'HMD': 'Heard Island and McDonald Islands', 'UMI': 'United States Minor Outlying Islands', 'AFR': 'Africa (AFR)', 'APD': 'Asia and Pacific (APD)', 'EUR': 'Europe (EUR)', 'MCD': 'Middle East and Central Asia (MCD)', 'WHD': 'Western Hemisphere (WHD)', 'SDS': 'Small Developing States (SDS)'}


class IMFError(RuntimeError):
    """A useful data-service error that can be shown to the user."""


def http_get(url: str, accept: str) -> requests.Response:
    retry = Retry(total=2, backoff_factor=0.6,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"], respect_retry_after_header=False)
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))
        try:
            response = session.get(url, headers={"Accept": accept}, timeout=(10, 35))
            response.raise_for_status()
        except requests.RequestException as exc:
            raise IMFError("The IMF service could not complete this request. Try refreshing in a moment.") from exc
    return response


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def load_countries() -> tuple[dict[str, str], bool]:
    try:
        payload = http_get(f"{BASE_URL}/structure/codelist/IMF/CL_COUNTRY/~",
                           "application/json").json()
        lists = payload.get("data", {}).get("codelists", [])
        codes = next(c["codes"] for c in lists if c["id"] == "CL_COUNTRY")
        countries = {c["id"]: c.get("names", {}).get("en", c.get("name", c["id"]))
                     for c in codes if re.fullmatch(r"[A-Z]{3}", c["id"]) or c["id"] == "G163"}
        if not {"USA", "CHL", "G163"}.issubset(countries):
            raise ValueError("Incomplete country list")
        countries["G163"] = "Euro area"
        return countries, True
    except (IMFError, ValueError, KeyError, StopIteration, TypeError):
        return COUNTRY_SNAPSHOT.copy(), False


def series_url(country: str, kind: str) -> str:
    flow, key = ("CPI", f"{country}.CPI._T.IX.M") if kind == "cpi" else (
        "ER", f"{country}.XDC_USD.PA_RT.M")
    # The complete monthly series is small. Filter locally because IMF's
    # date-query syntax/support can vary across dataflows and server versions.
    return f"{BASE_URL}/data/dataflow/IMF.STA/{flow}/~/{key}"


def parse_series(text: str, country: str, kind: str) -> pd.DataFrame:
    """Read SDMX-CSV, preserving missing months, scale and observation flags."""
    empty = pd.DataFrame(columns=["value", "status", "scale"],
                         index=pd.DatetimeIndex([], name="month"))
    if not text.strip():
        return empty
    try:
        raw = pd.read_csv(StringIO(text), dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise IMFError("The IMF response was not a readable SDMX CSV file.") from exc
    if not {"TIME_PERIOD", "OBS_VALUE"}.issubset(raw.columns):
        raise IMFError("The IMF response did not contain monthly observation columns.")
    expected = {"COUNTRY": country, "FREQUENCY": "M", "TYPE_OF_TRANSFORMATION": "IX" if kind == "cpi" else "PA_RT"}
    expected.update({"INDEX_TYPE": "CPI", "COICOP_1999": "_T"} if kind == "cpi" else {"INDICATOR": "XDC_USD"})
    for col, value in expected.items():
        if col in raw.columns:
            raw = raw.loc[raw[col] == value]
    if raw.empty:
        return empty
    dates = raw["TIME_PERIOD"].str.replace(r"^(\d{4})-M(\d{2})$", r"\1-\2", regex=True)
    months = pd.to_datetime(dates, format="%Y-%m", errors="coerce")
    scales = pd.to_numeric(raw.get("SCALE", pd.Series("0", index=raw.index)).replace("", "0"), errors="coerce")
    values = pd.to_numeric(raw["OBS_VALUE"], errors="coerce") * np.power(10.0, scales)
    values = values.where(np.isfinite(values) & (values > 0))
    # CPI base years are arbitrary, but competing observations must not be
    # averaged or selected silently. A constant rebasing cancels in Real Index.
    frame = pd.DataFrame({"month": months, "value": values,
                          "status": raw.get("STATUS", pd.Series("", index=raw.index)),
                          "scale": scales})
    frame = frame.loc[frame["month"].notna() & (frame["month"] >= FIRST_MONTH)]
    if frame.groupby("month")["value"].nunique().gt(1).any():
        raise IMFError("IMF returned conflicting observations for one month. Review the source before calculating.")
    return frame.drop_duplicates("month").set_index("month").sort_index()


@st.cache_data(ttl=6 * 3600, show_spinner=False, max_entries=512)
def load_series(country: str, kind: str) -> tuple[pd.DataFrame, str]:
    url = series_url(country, kind)
    response = http_get(url, "text/csv")
    if response.status_code == 204:
        frame = parse_series("", country, kind)
    else:
        frame = parse_series(response.text, country, kind)
    return frame, datetime.now(timezone.utc).isoformat(timespec="seconds")


def calculate_sample(inputs: pd.DataFrame, start: str, end: str,
                     same_country: bool = False) -> tuple[pd.DataFrame, float]:
    """Pure economics: filter first, then calculate the sample-specific mean."""
    index = pd.date_range(start, end, freq="MS", name="month")
    sample = inputs.reindex(index).copy()
    for col in ["P1_CPI", "P2_CPI", "E1_LCU_per_USD", "E2_LCU_per_USD"]:
        sample[col] = pd.to_numeric(sample[col], errors="coerce")
        sample[col] = sample[col].where(np.isfinite(sample[col]) & (sample[col] > 0))
    sample["S_C2_per_C1"] = 1.0 if same_country else sample["E2_LCU_per_USD"] / sample["E1_LCU_per_USD"]
    sample["S_C2_per_C1"] = sample["S_C2_per_C1"].where(np.isfinite(sample["S_C2_per_C1"]) & (sample["S_C2_per_C1"] > 0))
    sample["RER"] = sample["S_C2_per_C1"] * sample["P1_CPI"] / sample["P2_CPI"]
    sample["RER"] = sample["RER"].where(np.isfinite(sample["RER"]) & (sample["RER"] > 0))
    sample["valid_RER"] = sample["RER"].notna()
    rer_star = float(sample.loc[sample["valid_RER"], "RER"].mean())
    sample["RER_star_sample_mean"] = rer_star
    sample["Real_Index"] = 100.0 * sample["RER"] / rer_star
    sample["deviation_from_sample_mean_pct"] = sample["Real_Index"] - 100.0
    return sample, rer_star


def make_chart(sample: pd.DataFrame, mode: str, units: str) -> go.Figure:
    both = mode == "Both"
    fig = make_subplots(specs=[[{"secondary_y": both}]])
    if mode in ("Real", "Both"):
        fig.add_trace(go.Scatter(x=sample.index, y=sample["Real_Index"],
                                name="Real index", mode="lines", connectgaps=False,
                                line={"color": PURPLE, "width": 3},
                                hovertemplate="%{x|%b %Y}<br>Real index: %{y:.2f}<extra></extra>"), secondary_y=False)
        fig.add_hline(y=100, line_dash="dot", line_color="#9A8BAE", secondary_y=False)
        fig.update_yaxes(title_text="Real index · sample mean = 100", secondary_y=False)
    if mode in ("Nominal", "Both"):
        trace = go.Scatter(x=sample.index, y=sample["S_C2_per_C1"],
                           name="Nominal exchange rate", mode="lines", connectgaps=False,
                           line={"color": LILAC if both else PURPLE, "width": 2.5},
                           hovertemplate="%{x|%b %Y}<br>S(t): %{y:,.6g}<extra></extra>")
        fig.add_trace(trace, secondary_y=both)
        fig.update_yaxes(title_text=units, secondary_y=both, tickformat=",.6g")
    fig.update_layout(height=480, template="plotly_white", paper_bgcolor="white",
                      plot_bgcolor="white", font={"family": "Arial, sans-serif", "color": "#342348"},
                      margin={"l": 16, "r": 16, "t": 22, "b": 16},
                      legend={"orientation": "h", "y": 1.10, "x": 0},
                      hovermode="x unified", dragmode="zoom")
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(gridcolor="#F0ECF5", zeroline=False)
    if both:
        fig.update_yaxes(showgrid=False, secondary_y=True)
    return fig


STYLE = """
<style>
:root { --primary-color: #4E2A84; --background-color: #FFFFFF;
 --secondary-background-color: #F6F2FA; --text-color: #2C2238; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
 background: #FFFFFF !important; color: #2C2238 !important; color-scheme: light; }
[data-testid="stSidebar"] { background: #F6F2FA !important; border-right: 1px solid #E8DFF2; }
[data-testid="stSidebar"] * { color: #342348; }
h1,h2,h3 { color: #4E2A84 !important; letter-spacing: -0.025em; }
.block-container { padding-top: 4rem; max-width: 1280px; }
.eyebrow { color: #7956A1; font-size: .76rem; letter-spacing: .16em; font-weight: 700; }
.intro { color: #766781; font-size: 1.05rem; margin-bottom: 1.6rem; }
[data-testid="stMetric"] { background: #FAF8FD; border: 1px solid #E9E0F1;
 border-radius: 12px; padding: 17px 20px; }
[data-testid="stMetricValue"] { color: #4E2A84 !important; }
[data-testid="stMetricLabel"] { color: #766781 !important; }
[data-testid="stBaseButton-primary"], [data-testid="stDownloadButton"] button {
 background: #4E2A84 !important; color: #FFFFFF !important; border-color: #4E2A84 !important; }
[data-testid="stBaseButton-primary"] *, [data-testid="stDownloadButton"] button * { color: white !important; }
[data-baseweb="select"] > div { background: white; color: #342348; border-color: #DCD0E8; }
[data-baseweb="input"] { background: white; }
[data-testid="stRadio"] label { color: #4E2A84 !important; }
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child {
 background-color: #4E2A84 !important; border-color: #4E2A84 !important; }
.note { padding: 17px 20px; background: #F6F2FA; border-left: 3px solid #A579D2;
 border-radius: 4px 10px 10px 4px; color: #503E64; font-size: .92rem; }
.footer { color: #8A7A99; font-size: .78rem; margin-top: 1.5rem; }
</style>
"""


def main() -> None:
    st.set_page_config(page_title="Real Exchange Rate Lab", page_icon="◈", layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">INTERNATIONAL FINANCE · IMF DATA</div>', unsafe_allow_html=True)
    st.title("Real Exchange Rate Lab")
    st.markdown('<div class="intro">Explore how currencies and prices move together.</div>', unsafe_allow_html=True)

    countries, live_list = load_countries()
    codes = sorted(countries, key=lambda c: countries[c])
    with st.sidebar:
        st.markdown("### Your comparison")
        st.caption("Choose two economies and a monthly sample.")
        c1 = st.selectbox("Country 1", codes, index=codes.index("USA"),
                          format_func=lambda c: countries[c])
        c2 = st.selectbox("Country 2", codes, index=codes.index("CHL"),
                          format_func=lambda c: countries[c])
        now = pd.Timestamp.now(tz="UTC").tz_localize(None).to_period("M").to_timestamp()
        months = pd.date_range(FIRST_MONTH, now, freq="MS").strftime("%Y-%m").tolist()
        date_cols = st.columns(2)
        start = date_cols[0].selectbox("Start month", months, index=months.index("2000-01"))
        end = date_cols[1].selectbox("End month", months, index=max(0, len(months)-2))
        st.caption("Monthly data from January 1976, where available.")
        refresh = st.button("Refresh IMF data", width="stretch")
        st.divider()
        st.markdown("**Exchange-rate direction**")
        st.caption(f"Units of {countries[c2]} currency per 1 unit of {countries[c1]} currency.")
        st.caption("White & purple · Inspired by Kellogg")
    if refresh:
        load_countries.clear()
        load_series.clear()
        st.rerun()
    if not live_list:
        st.info("Country metadata is temporarily unavailable. Using the IMF country-list snapshot saved on October 26, 2026.")
    if start > end:
        st.error("Choose a start month on or before the end month.")
        st.stop()

    requests_needed = {(c, kind) for c in (c1, c2) for kind in ("cpi", "fx")
                       if not (c == "USA" and kind == "fx")}
    fetched, timestamps, errors = {}, {}, []
    with st.spinner("Retrieving monthly CPI and exchange rates from the IMF…"):
        # Keep Streamlit cache calls on the main thread; fetch each distinct
        # country-series once. Cached date/chart changes make no HTTP requests.
        for c, kind in sorted(requests_needed):
            try:
                frame, retrieved = load_series(c, kind)
                fetched[c, kind] = frame
                timestamps[c, kind] = retrieved
                if frame.empty:
                    errors.append(f"{countries[c]}: no monthly {'CPI' if kind == 'cpi' else 'exchange-rate'} observations returned.")
            except IMFError as exc:
                fetched[c, kind] = pd.DataFrame(columns=["value", "status", "scale"])
                errors.append(f"{countries[c]} {'CPI' if kind == 'cpi' else 'exchange rate'}: {exc}")

    full = pd.DataFrame(index=pd.date_range(FIRST_MONTH, now, freq="MS", name="month"))
    source_rows = []
    for side, country in [(1, c1), (2, c2)]:
        for kind in ("cpi", "fx"):
            name = f"P{side}_CPI" if kind == "cpi" else f"E{side}_LCU_per_USD"
            if country == "USA" and kind == "fx":
                full[name] = 1.0
                full[f"{name}_status"] = "USD/USD identity"
                full[f"{name}_scale"] = 0
                full[f"{name}_retrieved_utc"] = ""
                source_rows.append({"Country": countries[country], "Series": "USD/USD = 1 (identity)",
                                    "First month": "1976-01", "Last month": now.strftime("%Y-%m"), "Source": "Currency identity"})
            else:
                frame = fetched[country, kind]
                full[name] = frame["value"]
                full[f"{name}_status"] = frame["status"]
                full[f"{name}_scale"] = frame["scale"]
                full[f"{name}_retrieved_utc"] = timestamps.get((country, kind), "")
                valid = frame.dropna(subset=["value"])
                source_rows.append({"Country": countries[country], "Series": kind.upper(),
                                    "First month": valid.index.min().strftime("%Y-%m") if not valid.empty else "—",
                                    "Last month": valid.index.max().strftime("%Y-%m") if not valid.empty else "—",
                                    "Source": series_url(country, kind)})
    sample, rer_star = calculate_sample(full, start, end, c1 == c2)
    sample["country_1"] = c1
    sample["country_2"] = c2
    sample["sample_start"] = start
    sample["sample_end"] = end
    for message in errors:
        st.warning(message)

    st.subheader(f"{countries[c1]} → {countries[c2]}")
    units = f"{countries[c2]} currency / 1 {countries[c1]} currency"
    mode = st.radio("Chart view", ["Real", "Nominal", "Both"], horizontal=True,
                    help="Real is indexed to the sample average. Nominal uses actual currency units. Both uses separate axes.")
    valid = sample.dropna(subset=["Real_Index"])
    nominal = sample.dropna(subset=["S_C2_per_C1"])
    cols = st.columns(3)
    cols[0].metric("Latest real index", f"{valid['Real_Index'].iloc[-1]:,.2f}" if not valid.empty else "—")
    cols[0].caption(valid.index[-1].strftime("%B %Y") if not valid.empty else "No valid real observations")
    cols[1].metric("Latest nominal rate", f"{nominal['S_C2_per_C1'].iloc[-1]:,.6g}" if not nominal.empty else "—")
    cols[1].caption(nominal.index[-1].strftime("%B %Y") if not nominal.empty else "No valid nominal observations")
    cols[2].metric("Valid real months", f"{len(valid)} / {len(sample)}")
    cols[2].caption(f"{start} through {end}")
    st.plotly_chart(make_chart(sample, mode, units), width="stretch",
                    config={"displaylogo": False, "scrollZoom": False}, theme=None)
    if mode == "Both":
        st.caption("Left axis: real index. Right axis: nominal currency units. The two axes have independent scales.")
    if valid.empty:
        st.warning("No months contain all inputs needed for the real index in this sample. Change the countries or dates. Available nominal observations remain downloadable.")
    else:
        last = float(valid["Real_Index"].iloc[-1])
        position = "above" if last >= 100 else "below"
        st.markdown(f'<div class="note">In {valid.index[-1]:%B %Y}, the real index was <b>{abs(last-100):.2f}% {position}</b> '
                    'its selected-period average. A rise means a real appreciation of Country 1’s currency '
                    '(and a real depreciation of Country 2’s currency) under this quotation.</div>', unsafe_allow_html=True)
    missing = len(sample) - len(valid)
    if missing:
        st.caption(f"{missing} selected months lack at least one valid real-rate input. Gaps are not filled or interpolated.")
    if c1 == c2:
        st.info("The same country is selected on both sides: S(t) = 1, and the real index is 100 whenever CPI is available.")
    st.caption("100 is a historical sample benchmark. It does not establish equilibrium value or prove overvaluation or undervaluation.")
    export = sample.reset_index()
    export["month"] = export["month"].dt.strftime("%Y-%m")
    st.download_button("Download sample CSV", export.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"real_exchange_rate_{c1}_{c2}_{start}_{end}.csv", mime="text/csv")
    with st.expander("How the economics works"):
        st.markdown("Let **E₁** and **E₂** be each country's IMF monthly average exchange rate, in local-currency units per USD.")
        st.latex(r"S(t)=\frac{E_2(t)}{E_1(t)}, \qquad RER(t)=S(t)\frac{P_1(t)}{P_2(t)}")
        st.latex(r"RER^*=\frac{1}{N}\sum_{t\in\text{valid selected months}}RER(t), \qquad \text{Real Index}(t)=100\frac{RER(t)}{RER^*}")
        st.markdown(f"**RER\\* in this sample:** {rer_star:,.6g}" if not valid.empty else "**RER\\*:** unavailable (no valid months).")
        st.markdown("The arithmetic mean is recalculated whenever dates or countries change. Only months with positive, finite CPI and exchange-rate inputs enter the real-rate mean. Nominal observations can still appear when CPI is missing.")
        st.markdown("CPI is a national price index, not a common-currency price level. Different constant CPI base years cancel in the normalized real index. This app illustrates relative purchasing power parity; it does not estimate an absolute PPP rate or forecast exchange rates.")
        st.markdown("Cross rates are ratios of monthly average USD rates, which can differ from averages of daily bilateral rates. Currency redenominations, euro adoption, methodological changes and unlinked CPI rebasing can cause breaks. IMF coverage varies; a euro-area series may have a shorter history. Review the source before interpreting long samples.")
    with st.expander("Data, coverage & observations"):
        st.caption("Source: IMF SDMX 3.0 · CPI headline all-items index · Exchange rates, period average · Euro area code G163.")
        st.dataframe(pd.DataFrame(source_rows), hide_index=True, width="stretch",
                      column_config={"Source": st.column_config.LinkColumn("Source")})
        st.caption("Values include the IMF SCALE multiplier. The CSV preserves source status codes, scale exponents, retrieval timestamps, all selected months, and sample calculations. Status flags do not automatically imply invalid data; missing or nonpositive values are excluded.")
        st.dataframe(export, hide_index=True, width="stretch")
        st.markdown(f"[IMF API documentation](https://data.imf.org/en/Resource-Pages/IMF-API) · [IMF CPI dataset](https://data.imf.org/en/datasets/IMF.STA:CPI) · [IMF exchange rates](https://data.imf.org/en/datasets/IMF.STA:ER)")
    st.markdown('<div class="footer">Built for International Finance · IMF data may be revised · Educational use</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
