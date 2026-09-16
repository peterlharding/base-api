
-- contact sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: account_id refers to account 1 and 2, owner_id and *_by_id to
-- application_user 1 (admin) and 2 (plh). guid holds an 18 character
-- Salesforce-style id, matching the column's varchar(18).

INSERT INTO public.contact (
    guid,
    salutation,
    first_name,
    last_name,
    title,
    department,
    account_id,
    description,
    mailing_street,
    mailing_city,
    mailing_state,
    mailing_postal_code,
    mailing_country,
    phone,
    mobile_phone,
    email,
    assistant_name,
    owner_id,
    lead_source,
    has_opted_out_of_email,
    created_by_id,
    updated_by_id
) VALUES
(
    '0035g00000A1b2cAAA',
    'Ms.',
    'Olivia',
    'Nguyen',
    'Operations Director',
    'Operations',
    1,
    'Main decision maker for the warehouse tracking rollout.',
    '12 Wharf Road',
    'Southbank',
    'VIC',
    '3006',
    'Australia',
    '+61 3 9555 0101',
    '+61 400 555 101',
    'olivia.nguyen@southbank-logistics.example.com',
    'Sam Patel',
    2,
    'Trade Show',
    false,
    1,
    1
),
(
    '0035g00000A1b2dAAA',
    'Dr.',
    'James',
    'Okafor',
    'Chief Medical Officer',
    'Clinical Services',
    2,
    'Converted from lead 2.',
    '88 Circular Quay',
    'Sydney',
    'NSW',
    '2000',
    'Australia',
    '+61 2 9555 0143',
    '+61 400 555 143',
    'james.okafor@harbourview-health.example.com',
    NULL,
    2,
    'Web',
    true,
    2,
    2
);
