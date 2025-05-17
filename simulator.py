
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
    rationale_map = {}
    YEARS = range(0, years + 1)
    total_months = years * 12
    month_map = [(start_year + (m // 12), (m % 12) + 1) for m in range(total_months + 1)]

    # Initialize with starting prices
    for drug, countries in initial_prices.items():
        for country, price in countries.items():
            price_series[drug][country][0] = price

    for m in range(1, total_months + 1):
        year, month = month_map[m]

        for drug in initial_prices:
            # Carry forward previous price
            for country in initial_prices[drug]:
                prev_price = price_series[drug][country].get(m - 1)
                if prev_price is not None:
                    price_series[drug][country][m] = prev_price

            # Apply interventions first
            if interventions:
                for event in interventions:
                    if (event["year"], event["month"]) == (year, month) and event["drug"] == drug:
                        current_price = price_series[drug][event["country"]][m]
                        if event["mode"] == "percent":
                            new_price = round(current_price * (1 - event["value"] / 100), 2)
                        else:
                            new_price = round(event["value"], 2)
                        price_series[drug][event["country"]][m] = new_price
                        rationale_map[(drug, event["country"], year, month)] = (
                            f"Intervention: {'-' if event['mode'] == 'percent' else ''}{event['value']} {'%' if event['mode'] == 'percent' else '€'}"
                        )

            # Apply IRP logic after intervention
            for country, policy in irp_policies.items():
                freq = policy.get("frequency", 12)
                delay = policy.get("enforcement_delay", 0)
                rule = policy.get("rule", "average")
                basket = policy.get("basket", [])
                allow_increase = policy.get("allow_increase", False)

                if (m - delay) >= 0 and (m - delay) % freq == 0:
                    collected_at = m - delay
                    enforced_at = collected_at + delay
                    if enforced_at > total_months:
                        continue
                    irp_price = compute_irp_price(price_series[drug], basket, rule, collected_at)
                    if irp_price is None:
                        continue
                    current_price = price_series[drug][country].get(enforced_at)
                    if current_price is None:
                        continue
                    if allow_increase or irp_price < current_price:
                        price_series[drug][country][enforced_at] = round(irp_price, 2)
                        rationale_map[(drug, country, *month_map[enforced_at])] = (
                            f"IRP Event: Rule={rule}, Basket={', '.join([f'{c}: {price_series[drug][c].get(collected_at, 'N/A')}' for c in basket])}"
                        )

    output_rows = []
    for drug in price_series:
        for country in price_series[drug]:
            for m in range(total_months + 1):
                year, month = month_map[m]
                price = price_series[drug][country].get(m)
                volume = volumes.get(drug, {}).get(country, {}).get(m, 0)
                revenue = round(price * volume, 2) if price is not None else None
                rationale = rationale_map.get((drug, country, year, month), "Carry-forward")
                output_rows.append({
                    "Drug": drug,
                    "Country": country,
                    "Year": year,
                    "Month": month,
                    "Price": price,
                    "Volume": volume,
                    "Revenue": revenue,
                    "Rationale": rationale
                })

    return pd.DataFrame(output_rows)
