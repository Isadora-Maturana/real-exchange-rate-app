# Real Exchange Rate Lab

An English Streamlit app for an International Finance class, with a white and purple design inspired by Kellogg. Compare two IMF economies, explore monthly real and nominal exchange rates, and download the selected observations and calculations.

## Publish without installing Python

The repository needs these three files at its top level:

```text
app.py
requirements.txt
README.md
```

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Choose **Create app → Yup, I have an app** (the wording may vary).
3. Select **Isadora-Maturana/real-exchange-rate-app**, branch **main**, and main file **app.py**.
4. In **Advanced settings**, select **Python 3.12**. Initially leave **Secrets** empty: this app uses the public IMF endpoint without an API key.
5. Click **Deploy**. Save the resulting `https://...streamlit.app` link for the assignment.

See the [official Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). If the IMF service is temporarily unavailable, the app reports the problem; it does not substitute simulated or non-IMF observations.

## Use the app

- Choose **Country 1** and **Country 2**, including **Euro area**.
- Set inclusive **start** and **end** months, beginning as early as January 1976. The initial comparison is United States → Chile, from January 2000 to the last completed month.
- Select **Real**, **Nominal**, or **Both**. Hover to inspect observations, drag to zoom, and double-click to reset. **Both** uses separate axes.
- Select **Download sample CSV** to export every month in the chosen period, including gaps, source inputs, flags, scale exponents, retrieval timestamps, and calculations.
- Open the economics and data expanders to inspect formulas, coverage and sources. Use **Refresh IMF data** to request updated series.

## Economic definitions

For country i, let Eᵢ(t) be IMF local-currency units per US dollar. Define:

```text
S(t) = E₂(t) / E₁(t)
     = units of Country 2 currency per 1 unit of Country 1 currency

RER(t) = S(t) × P₁(t) / P₂(t)

RER* = arithmetic average of RER(t) over valid months in the selected sample

Real Index(t) = 100 × RER(t) / RER*
```

P₁ and P₂ are monthly headline all-items CPIs. The mean is recalculated **after** filtering the selected dates. The real index therefore averages 100 over its valid selected months. Its numerical level in a given month can change when the benchmark sample changes.

Nominal S(t) remains in actual currency units. It is never normalized. For example, with Country 1 = United States and Country 2 = Chile, S is Chilean pesos per US dollar. If E₁ = 1 and E₂ = 900, S = 900. If P₁ = 120 and P₂ = 150, RER = 720. If the sample's RER* is 600, the real index is 120.

Under this convention, a rising RER means a **real appreciation of Country 1's currency** and a **real depreciation of Country 2's currency**: Country 1 goods become relatively more expensive. An index above 100 is above the selected historical average. It is **not proof of overvaluation**, and the sample mean is not an estimated equilibrium rate.

CPIs have arbitrary national bases. Constant CPI rebasing cancels in the normalized real index; raw RER and RER* are base-dependent. Relative PPP suggests a stable real exchange rate over longer horizons under its assumptions. This application does not test a forecasting model, estimate absolute PPP, or guarantee reversion to the sample mean.

## IMF data and limitations

- [IMF API information](https://data.imf.org/en/Resource-Pages/IMF-API)
- Base: `https://api.imf.org/external/sdmx/3.0`
- [CPI dataset](https://data.imf.org/en/datasets/IMF.STA:CPI): `data/dataflow/IMF.STA/CPI/~/{ISO3}.CPI._T.IX.M`
- [Exchange-rate dataset](https://data.imf.org/en/datasets/IMF.STA:ER): `data/dataflow/IMF.STA/ER/~/{ISO3}.XDC_USD.PA_RT.M`
- Country metadata: `structure/codelist/IMF/CL_COUNTRY/~`. Include alphabetic three-letter IMF country/economy codes and **G163** for the euro area. A metadata snapshot from **October 26, 2026** is embedded for temporary country-list outages; observations always come from live IMF downloads or their six-hour cache.
- The `~` version selector requests the latest dataflow. CSV downloads are filtered locally to the requested months because server-side date filtering can vary. The parser handles IMF `YYYY-MMM` monthly labels, such as `2024-M01`, and applies the reported `10^SCALE` multiplier.
- USD/USD is exactly 1 by currency identity, including when the IMF does not provide a US dollar exchange-rate series. This derivation is labeled in the app and CSV.
- Only positive, finite inputs produce a valid real-rate observation. There is no interpolation, forward fill, extrapolation, or imputation of missing IMF observations. A month's nominal rate can remain available when its CPI is missing. Zero valid real months results in an explanatory message, while available data remain downloadable.
- Coverage and reporting lags differ. Some countries and the euro area cannot support the full history from 1976. The country list describes possible economies, not a guarantee that every economy has all four required series.
- On October 26, 2026, the supplied **G163 CPI key returned no observations**. The app reports that limitation and still displays available euro-area nominal rates. It does not silently replace CPI with another series. Euro-area real charts become available if the specified IMF series becomes available.
- National currency changes, redenominations, euro adoption and unlinked CPI-base changes can create breaks. The app preserves the IMF series as supplied and does not splice currencies or independently repair breaks.
- Ratios of monthly average USD rates can differ from monthly averages of daily bilateral rates.
- Source observation status codes are retained for inspection; provisional observations can be revised. Conflicting values returned for the same country-series/month raise a data error instead of being averaged silently.
- Public IMF API requests can time out or be rate-limited. Requests have bounded timeouts, retries, and caching. No API key is embedded.

## AI assistance record

- **Date:** October 26, 2026 (America/Chicago).
- **Assistant/model:** OpenAI Codex, based on GPT-6. A more specific model variant was not exposed to the assistant; no unverified variant is claimed.
- **Purpose:** The student provides the requirements and checks the economics; the LLM prepares the code. The student's previous chat, **HW International Finance**, was consulted for class context.
- **Student review:** Verify the exchange-rate direction, economic interpretation, data coverage, chosen sample, and published app before submission.

### Student's initial request (verbatim excerpts; original wording retained)

> I need to build a real exchange rate app for my International Finance Class. We've been working in this, and all the other assigments are in the chat call HW International Finance, so you can have that as a reference. It could be similar to the website that I was sharing screenshots to understand the variables. But I want the app with white and purple colors (like Kellogg). It must to be in englush.

The same request supplied these professor requirements (recorded here in full for the application specification):

> Allow users to choose Country 1 and Country 2 from IMF countries and the Euro area. Retrieve monthly IMF CPI and exchange-rate data from January 1976 where available.
>
> Define S(t) as units of Country 2 currency per one unit of Country 1 currency; let P1(t) and P2(t) be the respective monthly CPIs. Calculate RER(t) = S(t) × P1(t) / P2(t).
>
> Over the user-selected start and end months, calculate RER* = average of RER(t) over valid months; plot Real Index(t) = 100 × RER(t) / RER*. Recalculate RER* if dates change. Plot nominal S(t) in actual currency units—do not normalize it.
>
> Let users select Real, Nominal, or Both in interactive charts (use separate axes for Both) and provide a CSV download button of all observations and calculations within the selected sample period.
>
> Data hints: IMF API fetch is https://api.imf.org/external/sdmx/3.0; monthly CPI key {ISO3}.CPI._T.IX.M ; exchange-rate key {ISO3}.XDC_USD.PA_RT.M, where ISO3 is the country code. The IMF uses G163 for the Euro area. IMF exchange rates are local-currency units per USD, so convert them to the stated S(t) direction. Ask your LLM for complete three files: app.py, requirements.txt, and README.md files compatible with Python 3.12. IMF data may have gaps or limited coverage.

Follow-up supplied by the student:

> https://github.com/Isadora-Maturana/real-exchange-rate-app

The complete conversational prompt remains in the originating Codex chat. This README records the original app request and specification, not a reconstructed prompt presented as a new student message.

## Optional development

Deployment through Streamlit Community Cloud needs no local Python installation. For developers who already use Python 3.12:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The application has no paid services, embedded credentials, or persistent user data.

## Verification record

Verified on Python 3.12 on October 26, 2026. Calculation and parser checks cover the quotation direction, arithmetic sample mean, recalculation after date changes, CPI rebasing, missing months, same-country identity, scale multipliers, conflicting duplicates and separate chart axes. Live API checks covered United States, Chile, United Kingdom and euro-area availability. Streamlit interaction checks covered the default view, all three chart modes, changed dates, the same-country case, unavailable euro-area CPI and reversed date order. Dependency versions are pinned in `requirements.txt`.
