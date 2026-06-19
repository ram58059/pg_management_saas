MONTHLY_DUE_DAY = 7


def monthly_due_date(billing_month):
    """Return the standard payment due date (7th) for a billing month."""
    return billing_month.replace(day=MONTHLY_DUE_DAY)
