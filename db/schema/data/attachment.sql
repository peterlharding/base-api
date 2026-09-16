
-- attachment sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: parent_id refers to opportunity 1 and 2, owner_id and *_by_id
-- to application_user 1 (admin) and 2 (plh).

INSERT INTO public.attachment (
    guid,
    name,
    content_type,
    body_length,
    body_length_compressed,
    parent_id,
    owner_id,
    is_private,
    updated_by_id,
    created_by_id
) VALUES
(
    '21e0b831-4be2-4a8f-9521-0aa8853d8316',
    'warehouse-floor-plan.png',
    'image/png',
    512000,
    498000,
    1,
    2,
    false,
    2,
    2
),
(
    'bfa8c83b-88f2-46d1-9960-b376dcc23b1e',
    'signed-purchase-order.pdf',
    'application/pdf',
    96000,
    81000,
    2,
    2,
    true,
    1,
    2
);
