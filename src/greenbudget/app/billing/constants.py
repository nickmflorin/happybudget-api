class StripeSubscriptionStatus:
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELLED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class BillingStatus:
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "canceled"
