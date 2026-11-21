-- Slice 2 validation decision: retain one permanent working draft.
-- Historical named drafts are retained but no longer part of the editable workflow.
WITH selected AS (
    SELECT id FROM transport_change_sets WHERE status = 'draft'
    ORDER BY updated_at DESC, created_at DESC LIMIT 1
)
UPDATE transport_change_sets
SET name = 'Working draft', expires_at = 'infinity'::timestamptz
WHERE id IN (SELECT id FROM selected);

UPDATE transport_change_sets
SET status = 'retired', retired_at = now()
WHERE status = 'draft' AND id NOT IN (
    SELECT id FROM transport_change_sets WHERE status = 'draft' ORDER BY updated_at DESC, created_at DESC LIMIT 1
);

CREATE UNIQUE INDEX IF NOT EXISTS transport_change_sets_one_working_draft_idx
    ON transport_change_sets ((status)) WHERE status = 'draft';
