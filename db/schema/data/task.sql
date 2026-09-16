
-- task sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: who_id refers to contact 1 and 2, what_id to opportunity 1
-- and 2, account_id to account 1 and 2, owner_id and *_by_id to
-- application_user 1 (admin) and 2 (plh).

INSERT INTO public.task (
    guid,
    subject,
    description,
    type,
    status,
    priority,
    who_type,
    who_id,
    what_type,
    what_id,
    is_closed,
    owner_id,
    account_id,
    activity_date,
    call_duration_in_seconds,
    call_type,
    call_disposition,
    is_reminder_set,
    reminder_datetime,
    updated_by_id,
    created_by_id
) VALUES
(
    '303268ab-8eaf-4266-9dc5-6527bf463c92',
    'Follow up on revised quote',
    'Confirm whether phase 2 stays in scope.',
    'Call',
    'Not Started',
    'High',
    'Contact',
    1,
    'Opportunity',
    1,
    false,
    2,
    1,
    '2026-09-17 10:00:00+10',
    0,
    'Outbound',
    NULL,
    true,
    '2026-09-17 09:45:00+10',
    2,
    2
),
(
    '69bdd840-be01-478e-be7c-1f7bcd0bcd4e',
    'Kick-off call',
    'Walked through the integration timeline.',
    'Call',
    'Completed',
    'Normal',
    'Contact',
    2,
    'Opportunity',
    2,
    true,
    2,
    2,
    '2026-09-02 09:30:00+10',
    1740,
    'Outbound',
    'Agreed timeline, sent recap email',
    false,
    '2026-09-02 09:30:00+10',
    2,
    2
);
