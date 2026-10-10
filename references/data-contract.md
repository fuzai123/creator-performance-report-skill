# Private dataset contract

Keep the dataset outside the public skill/repository. The validator accepts
one UTF-8 JSON object with this structure. The sample identifiers below are
synthetic and not tied to any real account.

```json
{
  "threshold": 2.5,
  "months": ["2026-01"],
  "creators": [
    {
      "id": "creator-a",
      "name": "Creator A",
      "channel": "Channel A",
      "monthly_fee_usd": 100,
      "agreement_type": "new",
      "effective_date": "2026-01-01",
      "months": {
        "2026-01": {
          "affiliate_sales_usd": 300,
          "referrals": 12,
          "orders": 2,
          "content_views": 1000,
          "content_views_status": "recorded"
        }
      }
    }
  ]
}
```

Required statuses: `recorded`, `not_updated`, `unrecorded`. A recorded view
count is a nonnegative integer and may be zero. Non-recorded views must be
`null`, not 0. A displayed ratio is null when views are zero or not recorded.
Affiliate values must be observed or explicitly confirmed zeros; never fill a
missing source row with a fabricated zero. Store private source evidence and
account mappings separately from the public skill.

Compute with raw values, then round only for display:

- `sales_to_fee = affiliate_sales_usd / monthly_fee_usd`
- `target_met = sales_to_fee > threshold`
- `referrals_per_view = referrals / content_views` when views > 0; else null

If these three derived fields are included in a row, the validator checks
them against the source values. `target_met` must be a Boolean, and a result
equal to exactly 2.5 is false. Missing derived fields are calculated by the
reporting agent and do not imply a source value was missing.

For a portfolio view rate, sum referrals only over creator-months with a
recorded positive view denominator and divide by the sum of those views.
Do not average creator rates or mix covered and uncovered populations.
