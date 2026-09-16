
-- document sample data
--
-- Loaded into an empty table, so the rows get ids 1 and 2. No foreign keys
-- are declared: author_id and *_by_id refer to application_user 1 (admin)
-- and 2 (plh).

INSERT INTO public.document (
    guid,
    name,
    content_type,
    type,
    url,
    description,
    keywords,
    body_length,
    body_length_compressed,
    author_id,
    author_details,
    is_public,
    is_internal_use_only,
    updated_by_id,
    created_by_id
) VALUES
(
    'a1300b7a-8a33-48df-aad5-6d8d1aa4180b',
    'Standard Terms and Conditions 2026',
    'application/pdf',
    'pdf',
    'https://docs.example.com/terms-2026.pdf',
    'Terms attached to every quote issued in 2026.',
    'terms, legal, quote',
    184320,
    151040,
    1,
    'Admin User',
    true,
    false,
    1,
    1
),
(
    '690b6c09-1594-4b18-92f2-99aef5c59558',
    'Sales Playbook',
    'text/markdown',
    'md',
    'https://docs.example.com/internal/sales-playbook.md',
    'Qualification checklist and discount rules.',
    'sales, process',
    20480,
    8192,
    2,
    'Peter Harding',
    false,
    true,
    2,
    2
);
