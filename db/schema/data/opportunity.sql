
-- opportunity sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: account_id refers to account 1 and 2, owner_id and *_by_id to
-- application_user 1 (admin) and 2 (plh). Opportunity 2 came from converting
-- lead 2 and has been won.

INSERT INTO public.opportunity (
    guid,
    name,
    description,
    stage_name,
    amount,
    probability,
    expected_revenue,
    total_opportunity_quantity,
    type,
    next_step,
    account_id,
    owner_id,
    lead_source,
    is_closed,
    is_won,
    forecast_category,
    has_opportunity_line_item,
    close_date,
    last_activity_date,
    fiscal_year,
    fiscal_quarter,
    updated_by_id,
    created_by_id
) VALUES
(
    'ed704a0a-5617-497b-95f5-7be1b058447b',
    'Southbank - Warehouse Tracking Rollout',
    'RFID tracking for three warehouses, phased over two quarters.',
    'Proposal/Price Quote',
    '48000.00',
    '60',
    '28800.00',
    '3',
    'Existing Business',
    'Send revised quote',
    1,
    2,
    'Trade Show',
    false,
    false,
    'Pipeline',
    true,
    '2026-11-28 17:00:00+11',
    '2026-09-10 14:00:00+10',
    '2026',
    'Q4',
    2,
    2
),
(
    '8e878d87-9ec3-4363-9485-cc9332d90afd',
    'Harbourview - Patient Booking Integration',
    'Integrate clinic booking system with the CRM contact records.',
    'Closed Won',
    '22500.00',
    '100',
    '22500.00',
    '1',
    'New Business',
    'Kick-off meeting',
    2,
    2,
    'Web',
    true,
    true,
    'Closed',
    false,
    '2026-09-01 12:00:00+10',
    '2026-09-02 09:30:00+10',
    '2026',
    'Q3',
    1,
    2
);
