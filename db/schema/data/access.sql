
-- access sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: reference_type names the table reference_id points into,
-- owner_id and user_id refer to application_user 1 (admin) and 2 (plh).

INSERT INTO public.access (
    access_type,
    reference_name,
    reference_type,
    reference_id,
    owner_id,
    user_id,
    last_referenced_date
) VALUES
(
    'View',
    'Southbank Logistics Pty Ltd',
    'account',
    1,
    2,
    1,
    '2026-09-11 08:15:00+10'
),
(
    'Update',
    'Southbank - Warehouse Tracking Rollout',
    'opportunity',
    1,
    2,
    2,
    '2026-09-14 16:40:00+10'
);
