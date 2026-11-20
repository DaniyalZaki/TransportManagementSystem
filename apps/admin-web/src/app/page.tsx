"use client";

import { FormEvent, useState } from "react";

import { SignInForm } from "../components/sign-in-form";

const apiBaseUrl = process.env.NEXT_PUBLIC_UTS_API_BASE_URL ?? "http://localhost:8000";

type Notice = { tone: "error" | "success" | "warning"; text: string };
type ChangeSet = {
  id: string; name: string; version: number; expires_at: string;
  base_published_change_set_id: string | null;
};
type Publication = { change_set_id: string; publisher: string; published_at: string };
const emptySnapshot = JSON.stringify(
  { routes: [], buses: [], assignments: [], weekly_departures: [], overrides: [] }, null, 2,
);

export default function AdminHome() {
  const [draftName, setDraftName] = useState("");
  const [notice, setNotice] = useState<Notice>();
  const [isCreating, setIsCreating] = useState(false);
  const [changeSet, setChangeSet] = useState<ChangeSet>();
  const [snapshot, setSnapshot] = useState(emptySnapshot);
  const [isSaving, setIsSaving] = useState(false);
  const [publications, setPublications] = useState<Publication[]>([]);

  function headers() {
    const token = sessionStorage.getItem("uts.access-token");
    return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : undefined;
  }

  async function createDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!headers()) {
      setNotice({ tone: "warning", text: "Sign in before creating a transport change set." });
      return;
    }
    setIsCreating(true);
    setNotice(undefined);
    const response = await fetch(`${apiBaseUrl}/api/v1/admin/transport/change-sets`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ name: draftName }),
    });
    const body = (await response.json()) as ChangeSet & { detail?: string };
    if (!response.ok) {
      setNotice({ tone: "error", text: body.detail ?? "The draft could not be created." });
    } else {
      setNotice({
        tone: "success",
        text: `${body.name} is a draft. It expires ${new Date(body.expires_at ?? "").toLocaleDateString()}.`,
      });
      setChangeSet(body);
      setSnapshot(emptySnapshot);
      setDraftName("");
    }
    setIsCreating(false);
  }

  async function requestDraft(path: string, options: RequestInit = {}) {
    if (!headers()) {
      setNotice({ tone: "warning", text: "Sign in before using transport management." });
      return undefined;
    }
    const response = await fetch(`${apiBaseUrl}/api/v1/admin/transport/${path}`, {
      ...options, headers: { ...headers(), ...(options.headers ?? {}) },
    });
    const body = await response.json() as ChangeSet & { detail?: string | { warnings?: { message: string }[] } };
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : "The request could not be completed.";
      setNotice({ tone: "error", text: detail });
      return undefined;
    }
    return body;
  }

  async function saveDraft() {
    if (!changeSet) return;
    let parsed: unknown;
    try { parsed = JSON.parse(snapshot); } catch { setNotice({ tone: "error", text: "Draft data must be valid JSON." }); return; }
    setIsSaving(true);
    const body = await requestDraft(`change-sets/${changeSet.id}`, {
      method: "PATCH", body: JSON.stringify({ ...(parsed as object), expected_version: changeSet.version }),
    });
    if (body) { setChangeSet(body); setNotice({ tone: "success", text: "Draft saved privately. Validate before publishing." }); }
    setIsSaving(false);
  }

  async function validateDraft() {
    if (!changeSet) return;
    const body = await requestDraft(`change-sets/${changeSet.id}/validate`, { method: "POST" }) as { warnings?: { message: string }[] } | undefined;
    if (body) setNotice(body.warnings?.length ? { tone: "warning", text: body.warnings.map((x) => x.message).join("; ") } : { tone: "success", text: "No schedule warnings found." });
  }

  async function publishDraft() {
    if (!changeSet) return;
    let body = await requestDraft(`change-sets/${changeSet.id}/publish`, { method: "POST", body: JSON.stringify({ expected_base_published_change_set_id: changeSet.base_published_change_set_id, publish_anyway: false }) });
    if (!body && window.confirm("Warnings may exist. Publish anyway?")) {
      body = await requestDraft(`change-sets/${changeSet.id}/publish`, { method: "POST", body: JSON.stringify({ expected_base_published_change_set_id: changeSet.base_published_change_set_id, publish_anyway: true }) });
    }
    if (body) { setChangeSet(body); setNotice({ tone: "success", text: "Published atomically; the public cache was refreshed." }); }
  }

  async function loadPublications() {
    const response = await fetch(`${apiBaseUrl}/api/v1/admin/transport/publications`, { headers: headers() });
    if (response.ok) setPublications((await response.json() as { publications: Publication[] }).publications);
  }

  async function recover(changeSetId: string) {
    const body = await requestDraft(`publications/${changeSetId}/recover`, { method: "POST" });
    if (body) { setNotice({ tone: "success", text: "The published change set was recovered as the active transport data." }); await loadPublications(); }
  }

  return (
    <main className="admin-shell">
      <header className="admin-header">
        <div>
          <p className="eyebrow">Uzair Transport Service</p>
          <h1>Transport management</h1>
        </div>
        <span className="environment-label">Privileged workspace</span>
      </header>
      <div className="admin-grid">
        <section className="admin-card sign-in-card" aria-labelledby="sign-in-heading">
          <h2 id="sign-in-heading">Transport Management sign in</h2>
          <p>Authentication is provided by self-hosted Supabase Auth.</p>
          <SignInForm />
        </section>
        {changeSet ? <section className="admin-card workflow-card" aria-labelledby="editor-heading">
          <p className="eyebrow">Draft editor</p>
          <h2 id="editor-heading">{changeSet.name}</h2>
          <p className="muted-copy">Version {changeSet.version}. Edit the complete private snapshot below. PKT weekday values use Monday = 0.</p>
          <label htmlFor="snapshot">Routes, buses, assignments, schedules, and date overrides</label>
          <textarea id="snapshot" className="draft-json" value={snapshot} onChange={(event) => setSnapshot(event.target.value)} />
          <div className="action-row">
            <button type="button" onClick={saveDraft} disabled={isSaving}>{isSaving ? "Saving…" : "Save draft"}</button>
            <button type="button" className="secondary-action" onClick={validateDraft}>Validate</button>
            <button type="button" onClick={publishDraft}>Publish</button>
          </div>
        </section> : null}
        <section className="admin-card workflow-card" aria-labelledby="history-heading">
          <div className="section-heading"><div><p className="eyebrow">Audit</p><h2 id="history-heading">Publication history</h2></div><button type="button" className="secondary-action" onClick={loadPublications}>Load history</button></div>
          <p className="muted-copy">Publication records retain only publisher and publication time for 30 days. Recovery publishes a whole historical snapshot.</p>
          {publications.map((publication) => <div className="publication" key={publication.change_set_id}><span>{new Date(publication.published_at).toLocaleString()}</span><span>{publication.publisher}</span><button type="button" className="secondary-action" onClick={() => recover(publication.change_set_id)}>Recover</button></div>)}
        </section>
        <section className="admin-card" aria-labelledby="draft-heading">
          <div className="section-heading">
            <div><p className="eyebrow">Change sets</p><h2 id="draft-heading">Start a draft</h2></div>
            <span className="status-pill">Drafts expire after 30 days</span>
          </div>
          <p className="muted-copy">A draft starts from the current published timetable. It remains private until an authorized user reviews warnings and separately publishes it.</p>
          <form className="draft-form" onSubmit={createDraft}>
            <label htmlFor="change-set-name">Change-set name</label>
            <input id="change-set-name" maxLength={160} onChange={(event) => setDraftName(event.target.value)} placeholder="e.g. Spring timetable" required value={draftName} />
            <button disabled={isCreating} type="submit">{isCreating ? "Creating draft…" : "Create draft"}</button>
          </form>
          {notice ? <p className={`notice notice-${notice.tone}`} role="status">{notice.text}</p> : null}
        </section>
        <section className="admin-card workflow-card" aria-labelledby="publish-heading">
          <p className="eyebrow">Protected publication</p>
          <h2 id="publish-heading">Review before publishing</h2>
          <ol>
            <li>Save routes, buses, assignments, and PKT schedule changes to the draft.</li>
            <li>Validate; incomplete or conflicting entries are warnings, not silent changes.</li>
            <li>Use the separate publish confirmation only when the correct baseline is current.</li>
          </ol>
          <p className="muted-copy">If another change set publishes first, this workspace requires a rebase. Published transport data is never changed by saving a draft.</p>
        </section>
      </div>
    </main>
  );
}
