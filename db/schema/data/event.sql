
-- event sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared. This table keeps its Salesforce-style varchar(18) references:
-- guid and who_ref hold 18 character ids (who_ref matches contact.guid), and
-- account_id and owner_id hold account and application_user ids as text.

INSERT INTO public.event (
    guid,
    who_ref,
    subject,
    description,
    location,
    type,
    show_as,
    activity_date,
    activity_datetime,
    is_all_day_event,
    duration_in_minutes,
    account_id,
    owner_id,
    is_reminder_set,
    reminder_datetime,
    updated_by_id,
    created_by_id
) VALUES
(
    '00U5g00000B7c8dEAA',
    '0035g00000A1b2cAAA',
    'Warehouse site visit',
    'Walk the Southbank warehouse with the operations team.',
    'Southbank warehouse',
    'Meeting',
    'Busy',
    '2026-09-22',
    '2026-09-22 13:00:00+10',
    false,
    120,
    '1',
    '2',
    true,
    '2026-09-22 12:00:00+10',
    2,
    2
),
(
    '00U5g00000B7c8eEAA',
    '0035g00000A1b2dAAA',
    'Go-live planning workshop',
    'Full day workshop with clinic managers.',
    'Harbourview Sydney',
    'Meeting',
    'Out of Office',
    '2026-10-06',
    '2026-10-06 09:00:00+11',
    true,
    480,
    '2',
    '2',
    false,
    '2026-10-06 09:00:00+11',
    1,
    2
);
