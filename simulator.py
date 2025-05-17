
import statistics
from collections import defaultdict
import pandas as pd

def run_irp_simulation_with_interventions(
    initial_prices,
    volumes,
    irp_policies,
    interventions=None,
    years=10,
    start_year=2025,
    start_month=1
):
    def compute_irp_price(prices_by_country, basket, rule, year_month):
        prices = [
            prices_by_country[c].get(year_month)
            for c in basket
            if year_month in prices_by_country[c]
        ]
        prices = [p for p in prices if p is not None]
        if not prices:
            return None
        if rule == "min":
            return min(prices)
        elif rule == "average":
            return sum(prices) / len(prices)
        elif rule == "median":
            return statistics.median(prices)
        return None

    def month_index(year, month):
        return (year - start_year) * 12 + (month - start_month)

    price_series = defaultdict(lambda: defaultdict(dict))
    irp_events = defaultdict(lambda: defaultdict(dict))
    total_months = years * 12

    # Initialize month mapping
    month_map = [(start_year + (m // 12), (m % 12) + 1) for m in range(total_months + 1)]

    for drug, countries in initial_prices.items():
        for country, price in countries.items():
            price_series[drug][country][0] = price

    # Propagate initial prices
    for m in range(1, total_months + 1):
        for drug in initial_prices:
            for country in initial_prices[drug]:
                prev_price = price_series[drug][country].get(m - 1)
                if prev_price is not None:
                    price_series[drug][country][m] = prev_price

        # IRP logic
        for drug in initial_prices:
            for country, policy in irp_policies.items():
                freq = policy.get("frequency", 12)
                delay = policy.get("enforcement_delay", 0)
                rule = policy.get("rule", "average")
                basket = policy.get("basket", [])

                if (m - delay) >= 0 and (m - delay) % freq == 0:
                    collected_at = m - delay
                    irp_price = compute_irp_price(price_series[drug], basket, rule, collected_at)
                    enforced_at = collected_at + delay
                    if enforced_at <= total_months:
                        irp_events[drug][country][enforced_at] = irp_price

        # Apply IRP events
        for drug in irp_events:
            for country in irp_events[drug]:
                if m in irp_events[drug][country]:
                    price_series[drug][country][m] = round(irp_events[drug][country][m], 2)

        # Apply interventions
        if interventions:
            for event in interventions:
                event_month = month_index(event["year"], event["month"])
                if event["drug"] in price_series and event["country"] in price_series[event["drug"]]:
                    if event_month == m:
                        current_price = price_series[event["drug"]][event["country"]][m]
                        if event["mode"] == "percent":
                            new_price = round(current_price * (1 - event["value"] / 100), 2)
                        else:
                            new_price = round(event["value"], 2)
                        price_series[event["drug"]][event["country"]][m] = new_price

    output_rows = []
    for drug in price_series:
        for country in price_series[drug]:
            for m in range(total_months + 1):
                year, month = month_map[m]
                price = price_series[drug][country].get(m)
                volume = volumes.get(drug, {}).get(country, {}).get(m, 0)
                revenue = round(price * volume, 2) if price is not None else None
                output_rows.append({
                    "Drug": drug,
                    "Country": country,
                    "Year": year,
                    "Month": month,
                    "Price": price,
                    "Volume": volume,
                    "Revenue": revenue
                })

    return pd.DataFrame(output_rows)
