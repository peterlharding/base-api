
-- note sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: parent_type names the table parent_id points into, owner_id
-- and *_by_id refer to application_user 1 (admin) and 2 (plh).

INSERT INTO public.note (
    guid,
    title,
    body,
    parent_type,
    parent_id,
    is_private,
    owner_id,
    updated_by_id,
    created_by_id
) VALUES
(
    'e7c6de2f-b484-4e97-b25c-7efbed8ab87a',
    'Site visit prep',
    'Olivia wants loading dock coverage in phase 1. Bring the handheld scanner samples.',
    'account',
    1,
    false,
    2,
    2,
    2
),
(
    '36eabbd9-d7c3-4991-b696-97d307e6a644',
    'Pricing approval',
    'Fixed price approved by the Managing Director, no discount beyond 5%.',
    'opportunity',
    2,
    true,
    1,
    1,
    1
);
