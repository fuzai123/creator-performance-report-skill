#!/usr/bin/env python3
"""Validate a private creator-month dataset without writing or exporting data."""

import argparse
import datetime as dt
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


def decimal(value, label, errors, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        errors.append(f"{label}: expected a number")
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        errors.append(f"{label}: invalid number")
        return None
    if not result.is_finite() or result < 0 or (positive and result == 0):
        errors.append(f"{label}: expected {'positive' if positive else 'nonnegative'} finite number")
        return None
    return result


def nonnegative_int(value, label, errors):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{label}: expected nonnegative integer")
        return None
    return value


def check_derived(row, label, order_amount, fee, threshold, referrals, views, errors):
    if order_amount is not None and fee is not None and threshold is not None:
        multiple = order_amount / fee
        if "order_amount_to_fee" in row:
            reported = decimal(row["order_amount_to_fee"], f"{label}.order_amount_to_fee", errors)
            if reported is not None and abs(reported - multiple) > Decimal("0.000001"):
                errors.append(f"{label}.order_amount_to_fee: disagrees with source values")
        if "target_met" in row and row["target_met"] is not (multiple > threshold):
            errors.append(f"{label}.target_met: must use strict greater-than threshold")
    if "referrals_per_view" in row and referrals is not None:
        expected = Decimal(referrals) / Decimal(views) if isinstance(views, int) and views > 0 else None
        reported = row["referrals_per_view"]
        if expected is None:
            if reported is not None:
                errors.append(f"{label}.referrals_per_view: must be null without positive recorded views")
        else:
            reported = decimal(reported, f"{label}.referrals_per_view", errors)
            if reported is not None and abs(reported - expected) > Decimal("0.000001"):
                errors.append(f"{label}.referrals_per_view: disagrees with source values")


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["root: expected object"]
    threshold = decimal(data.get("threshold"), "threshold", errors, positive=True)
    if threshold is not None and threshold != Decimal("2.5"):
        errors.append("threshold: this workflow requires 2.5")
    months = data.get("months")
    if not isinstance(months, list) or not months or any(not isinstance(m, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", m) for m in months):
        return errors + ["months: expected nonempty YYYY-MM array"]
    if months != sorted(set(months)):
        errors.append("months: must be sorted and unique")
    creators = data.get("creators")
    if not isinstance(creators, list) or not creators:
        return errors + ["creators: expected nonempty array"]
    seen = set()
    for index, creator in enumerate(creators):
        label = f"creators[{index}]"
        if not isinstance(creator, dict):
            errors.append(f"{label}: expected object")
            continue
        creator_id = creator.get("id")
        if not isinstance(creator_id, str) or not creator_id.strip() or creator_id in seen:
            errors.append(f"{label}.id: expected unique nonempty string")
        seen.add(creator_id)
        for field in ("name", "channel"):
            if not isinstance(creator.get(field), str) or not creator[field].strip():
                errors.append(f"{label}.{field}: expected nonempty string")
        fee = decimal(creator.get("monthly_fee_usd"), f"{label}.monthly_fee_usd", errors, positive=True)
        if creator.get("agreement_type") not in ("new", "renewal"):
            errors.append(f"{label}.agreement_type: expected new or renewal")
        try:
            dt.date.fromisoformat(creator["effective_date"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{label}.effective_date: expected ISO date")
        rows = creator.get("months")
        if not isinstance(rows, dict) or set(rows) != set(months):
            errors.append(f"{label}.months: must include each reporting month exactly once")
            continue
        for month in months:
            row_label = f"{label}.months[{month}]"
            row = rows[month]
            if not isinstance(row, dict):
                errors.append(f"{row_label}: expected object")
                continue
            order_amount = decimal(row.get("order_amount_usd"), f"{row_label}.order_amount_usd", errors)
            decimal(row.get("commissionable_volume_usd"), f"{row_label}.commissionable_volume_usd", errors)
            referrals = nonnegative_int(row.get("referrals"), f"{row_label}.referrals", errors)
            orders = nonnegative_int(row.get("orders"), f"{row_label}.orders", errors)
            audit = row.get("order_audit")
            if not isinstance(audit, dict):
                errors.append(f"{row_label}.order_audit: expected object")
            else:
                audit_count = nonnegative_int(audit.get("order_count"), f"{row_label}.order_audit.order_count", errors)
                unique_count = nonnegative_int(audit.get("unique_order_count"), f"{row_label}.order_audit.unique_order_count", errors)
                duplicates = nonnegative_int(audit.get("duplicate_order_ids"), f"{row_label}.order_audit.duplicate_order_ids", errors)
                mismatches = nonnegative_int(audit.get("detail_amount_mismatches"), f"{row_label}.order_audit.detail_amount_mismatches", errors)
                list_amount = decimal(audit.get("list_order_amount_usd"), f"{row_label}.order_audit.list_order_amount_usd", errors)
                if orders is not None and audit_count is not None and audit_count != orders:
                    errors.append(f"{row_label}.order_audit.order_count: must equal orders")
                if orders is not None and unique_count is not None and unique_count != orders:
                    errors.append(f"{row_label}.order_audit.unique_order_count: must equal orders")
                if duplicates is not None and duplicates != 0:
                    errors.append(f"{row_label}.order_audit.duplicate_order_ids: must be zero")
                if mismatches is not None and mismatches != 0:
                    errors.append(f"{row_label}.order_audit.detail_amount_mismatches: must be zero")
                if order_amount is not None and list_amount is not None and list_amount != order_amount:
                    errors.append(f"{row_label}.order_audit.list_order_amount_usd: must equal order_amount_usd")
                if audit.get("boundary_check_complete") is not True:
                    errors.append(f"{row_label}.order_audit.boundary_check_complete: must be true")
            status = row.get("content_views_status")
            views = row.get("content_views")
            if status == "recorded":
                views = nonnegative_int(views, f"{row_label}.content_views", errors)
            elif status in ("not_updated", "unrecorded"):
                if views is not None:
                    errors.append(f"{row_label}.content_views: must be null when not recorded")
            else:
                errors.append(f"{row_label}.content_views_status: invalid status")
            check_derived(row, row_label, order_amount, fee, threshold, referrals, views, errors)
    return errors


def self_test():
    row = {"order_amount_usd": 300, "commissionable_volume_usd": 270,
           "referrals": 12, "orders": 2,
           "order_audit": {"order_count": 2, "unique_order_count": 2,
                           "duplicate_order_ids": 0, "detail_amount_mismatches": 0,
                           "list_order_amount_usd": 300, "boundary_check_complete": True},
           "content_views": 1000, "content_views_status": "recorded"}
    sample = {"threshold": 2.5, "months": ["2026-01"], "creators": [{
        "id": "creator-a", "name": "Creator A", "channel": "Channel A",
        "monthly_fee_usd": 100, "agreement_type": "new",
        "effective_date": "2026-01-01", "months": {"2026-01": row}}]}
    assert not validate(sample)
    row.update({"order_amount_to_fee": 3, "target_met": True, "referrals_per_view": 0.012})
    assert not validate(sample)
    row.update({"order_amount_usd": 250, "order_amount_to_fee": 2.5, "target_met": False})
    row["order_audit"]["list_order_amount_usd"] = 250
    assert not validate(sample)
    row["target_met"] = True
    assert validate(sample)
    row["target_met"] = False
    row["content_views"] = 0
    row["referrals_per_view"] = None
    assert not validate(sample)
    row["referrals_per_view"] = 0
    assert validate(sample)
    row["referrals_per_view"] = None
    row["content_views_status"] = "not_updated"
    assert validate(sample)
    row["content_views"] = None
    row["order_audit"]["duplicate_order_ids"] = 1
    assert validate(sample)
    row["order_audit"]["duplicate_order_ids"] = 0
    row["order_audit"]["boundary_check_complete"] = False
    assert validate(sample)
    print("Self-test passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", nargs="?", help="Private local JSON dataset")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.dataset:
        parser.error("provide a dataset or --self-test")
    try:
        data = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read dataset: {error}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        print("Validation failed:\n" + "\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Validated {len(data['creators'])} creators across {len(data['months'])} months; no data values printed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
