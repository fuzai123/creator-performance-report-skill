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
          "order_amount_usd": 300,
          "commissionable_volume_usd": 270,
          "referrals": 12,
          "orders": 2,
          "order_audit": {
            "order_count": 2,
            "unique_order_count": 2,
            "duplicate_order_ids": 0,
            "detail_amount_mismatches": 0,
            "list_order_amount_usd": 300,
            "boundary_check_complete": true
          },
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
Order Amount and Commissionable Volume must be separately summed from every
order-detail view, regardless of commission status. Affiliate values must be
observed or explicitly confirmed zeros; never fill a missing source row with a
fabricated zero. The order audit must reconcile the visible list and detail
views: order counts agree, order IDs are unique, displayed Order Amount values
match between list and detail, the list sum equals the detail sum, and adjacent
filters have been checked for month-boundary records. Store private order IDs,
source evidence, and account mappings separately from the public skill.

Compute with raw values, then round only for display:

- `order_amount_to_fee = order_amount_usd / monthly_fee_usd`
- `target_met = order_amount_to_fee > threshold`
- `referrals_per_view = referrals / content_views` when views > 0; else null

If these three derived fields are included in a row, the validator checks
them against the source values. `target_met` must be a Boolean, and a result
equal to exactly 2.5 is false. Commissionable Volume is a separate reporting
measure and is not the target numerator. Missing derived fields are calculated
by the reporting agent and do not imply a source value was missing.

For a portfolio view rate, sum referrals only over creator-months with a
recorded positive view denominator and divide by the sum of those views.
Do not average creator rates or mix covered and uncovered populations.
