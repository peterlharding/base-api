
-- quote sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: account_id and contact_id refer to account/contact 1 and 2,
-- quoter_id and *_by_id to application_user 1 (admin) and 2 (plh).

INSERT INTO public.quote (
    quote_date,
    quote_amount,
    quoter,
    quoter_id,
    account_id,
    company,
    contact_id,
    contact,
    comment,
    description,
    order_no,
    order_date,
    order_amount,
    invoice_no,
    invoice_date,
    invoice_amount,
    status,
    doc_path,
    updated_by_id,
    created_by_id
) VALUES
(
    '2026-09-10',
    48000.00,
    'Peter Harding',
    2,
    1,
    'Southbank Logistics Pty Ltd',
    1,
    'Olivia Nguyen',
    'Revised after site visit; phase 2 optional.',
    'RFID tracking rollout, three warehouses',
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    'Active',
    'quotes/2026/Q-0001.pdf',
    2,
    2
),
(
    '2026-08-25',
    22500.00,
    'Peter Harding',
    2,
    2,
    'Harbourview Health Group',
    2,
    'James Okafor',
    '',
    'Patient booking integration, fixed price',
    'PO-77120',
    '2026-09-01',
    22500.00,
    'INV-0042',
    '2026-09-05',
    22500.00,
    'Invoiced',
    'quotes/2026/Q-0002.pdf',
    1,
    2
);
