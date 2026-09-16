
-- user_role sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: *_id columns refer to application_user 1 (admin) and 2 (plh).

INSERT INTO public.user_role (
    guid,
    name,
    parent_role_id,
    rollup_description,
    opportunity_access_for_account_owner,
    case_access_for_account_owner,
    contact_access_for_account_owner,
    forecast_user_id,
    portal_type,
    updated_by_id,
    created_by_id
) VALUES
(
    '5b82b0f0-0db7-45a9-8e14-e24ec063dd73',
    'Managing Director',
    NULL,
    'Managing Director',
    'Edit',
    'Edit',
    'Edit',
    1,
    'None',
    1,
    1
),
(
    'af5e9adf-4f90-4b9f-9a50-68f94742fe70',
    'Sales Manager',
    1,
    'Sales Manager',
    'Edit',
    'Edit',
    'Read',
    2,
    'None',
    1,
    1
);
