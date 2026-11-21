"use client";

import { FormEvent, useEffect, useState } from "react";

import { SignInForm } from "../components/sign-in-form";

const apiBaseUrl = process.env.NEXT_PUBLIC_UTS_API_BASE_URL ?? "http://localhost:8000";

type Notice = { tone: "error" | "success" | "warning"; text: string };
type ChangeSet = {
  id: string; name: string; version: number; expires_at: string;
  base_published_change_set_id: string | null;
};
type Publication = { change_set_id: string; publisher: string; published_at: string };
type Route = { route_code: string; origin: string; destination: string; direction: "RETURN" | "PICK-UP" | "" };
type Assignment = { route_code: string; bus_identifier: string };
type Departure = { route_code: string; weekday: number; departure_time: string };
type Override = Assignment & { service_date: string; operation: "add" | "remove"; departure_time: string };
type Snapshot = { routes: Route[]; buses: string[]; assignments: Assignment[]; weekly_departures: Departure[]; overrides: Override[] };
type DraftResponse = ChangeSet & { snapshot: Snapshot };
const emptySnapshot: Snapshot = { routes: [], buses: [], assignments: [], weekly_departures: [], overrides: [] };
const tabs = ["Routes", "Buses", "Assignments", "Schedule"] as const;
type Tab = typeof tabs[number];

function DataTable({ rows, columns, onRemove }: { rows: Record<string, unknown>[]; columns: string[]; onRemove: (index: number) => void }) {
  return <table className="draft-table"><thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ")}</th>)}<th><span className="sr-only">Actions</span></th></tr></thead><tbody>{rows.length ? rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{String(row[column])}</td>)}<td><button type="button" className="secondary-action" onClick={() => onRemove(index)}>Remove</button></td></tr>) : <tr><td colSpan={columns.length + 1}>No entries yet.</td></tr>}</tbody></table>;
}

function SelectPair({ value, onChange, routes, buses }: { value: Assignment; onChange: (value: Assignment) => void; routes: Route[]; buses: string[] }) {
  return <div className="editor-fields"><select aria-label="Route" value={value.route_code} onChange={(e) => onChange({ ...value, route_code: e.target.value })}><option value="">Select route</option>{routes.map((route) => <option key={route.route_code} value={route.route_code}>{route.route_code}</option>)}</select><select aria-label="Bus" value={value.bus_identifier} onChange={(e) => onChange({ ...value, bus_identifier: e.target.value })}><option value="">Select bus</option>{buses.map((bus) => <option key={bus} value={bus}>{bus}</option>)}</select></div>;
}

export default function AdminHome() {
  const [draftName, setDraftName] = useState("");
  const [notice, setNotice] = useState<Notice>();
  const [isCreating, setIsCreating] = useState(false);
  const [changeSet, setChangeSet] = useState<ChangeSet>();
  const [snapshot, setSnapshot] = useState<Snapshot>(emptySnapshot);
  const [isSaving, setIsSaving] = useState(false);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [draftMatches, setDraftMatches] = useState<ChangeSet[]>([]);
  const [signedIn, setSignedIn] = useState(false);
  const [tab, setTab] = useState<Tab>("Routes");
  const [route, setRoute] = useState<Route>({ route_code: "", origin: "", destination: "", direction: "" });
  const [bus, setBus] = useState("");
  const [assignment, setAssignment] = useState<Assignment>({ route_code: "", bus_identifier: "" });
  const [departure, setDeparture] = useState<Departure>({ route_code: "", weekday: 1, departure_time: "" });
  const [override, setOverride] = useState<Override>({ route_code: "", bus_identifier: "", service_date: "", operation: "add", departure_time: "" });

  useEffect(() => {
    const token = sessionStorage.getItem("uts.access-token");
    if (!token) return;
    void fetch(`${apiBaseUrl}/auth/session`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => {
        if (!response.ok) throw new Error("Session is no longer valid");
        setSignedIn(true);
      })
      .catch(() => sessionStorage.removeItem("uts.access-token"));
  }, []);

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
    try {
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
        const draft = await fetch(`${apiBaseUrl}/api/v1/admin/transport/change-sets/${body.id}`, { headers: headers() });
        const loaded = (await draft.json()) as DraftResponse;
        setChangeSet(loaded);
        setSnapshot(loaded.snapshot);
        setTab("Routes");
        setDraftName("");
      }
    } catch {
      setNotice({ tone: "error", text: "The draft could not be created. Check the backend connection and try again." });
    } finally {
      setIsCreating(false);
    }
  }

  async function requestDraft(path: string, options: RequestInit = {}) {
    if (!headers()) {
      setNotice({ tone: "warning", text: "Sign in before using transport management." });
      return undefined;
    }
    try {
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
    } catch {
      setNotice({ tone: "error", text: "The request could not reach the backend. Check the connection and try again." });
      return undefined;
    }
  }

  async function saveDraft() {
    if (!changeSet) return;
    setIsSaving(true);
    const body = await requestDraft(`change-sets/${changeSet.id}`, {
      method: "PATCH", body: JSON.stringify({ ...snapshot, expected_version: changeSet.version }),
    });
    if (body) { setChangeSet(body); setNotice({ tone: "success", text: "Draft saved privately. Publish when the route assignments are complete." }); }
    setIsSaving(false);
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
    if (!headers()) {
      setNotice({ tone: "warning", text: "Sign in before loading publication history." });
      return;
    }
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/admin/transport/publications`, { headers: headers() });
      if (!response.ok) {
        setNotice({ tone: "error", text: `Publication history could not be loaded (HTTP ${response.status}).` });
        return;
      }
      setPublications((await response.json() as { publications: Publication[] }).publications);
    } catch {
      setNotice({ tone: "error", text: "Publication history could not be loaded. Check the backend connection and try again." });
    }
  }

  async function recover(changeSetId: string) {
    const body = await requestDraft(`publications/${changeSetId}/recover`, { method: "POST" });
    if (body) { setNotice({ tone: "success", text: "The published change set was recovered as the active transport data." }); await loadPublications(); }
  }

  async function searchDrafts() {
    const body = await requestDraft(`change-sets?query=${encodeURIComponent(draftName)}`) as { change_sets?: ChangeSet[] } | undefined;
    if (body) setDraftMatches(body.change_sets ?? []);
  }

  async function openDraft(changeSetId: string) {
    const body = await requestDraft(`change-sets/${changeSetId}`) as DraftResponse | undefined;
    if (body) { setChangeSet(body); setSnapshot(body.snapshot); setTab("Routes"); setDraftMatches([]); setNotice({ tone: "success", text: `${body.name} was loaded for editing.` }); }
  }

  function addRoute() {
    if (!Object.values(route).every(Boolean)) return setNotice({ tone: "warning", text: "Complete every route field before adding it." });
    setSnapshot((current) => ({ ...current, routes: [...current.routes, route] }));
    setRoute({ route_code: "", origin: "", destination: "", direction: "" });
  }
  function addBus() {
    if (!bus.trim()) return;
    setSnapshot((current) => ({ ...current, buses: [...new Set([...current.buses, bus.trim()])] }));
    setBus("");
  }
  function addAssignment() {
    if (!assignment.route_code || !assignment.bus_identifier) return;
    setSnapshot((current) => ({ ...current, assignments: [...current.assignments, assignment] }));
  }
  function addDeparture() {
    if (!departure.route_code || !/^\d{2}:\d{2}$/.test(departure.departure_time)) {
      setNotice({ tone: "warning", text: "Select a route and enter a departure time in HH:MM format before adding a schedule entry." });
      return;
    }
    setSnapshot((current) => ({ ...current, weekly_departures: [...current.weekly_departures, departure] }));
  }
  function addOverride() {
    if (!override.route_code || !override.bus_identifier || !override.service_date || !override.departure_time) return;
    setSnapshot((current) => ({ ...current, overrides: [...current.overrides, override] }));
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
        {!signedIn ? <section className="admin-card sign-in-card" aria-labelledby="sign-in-heading">
          <h2 id="sign-in-heading">Transport Management sign in</h2>
          <p>Authentication is provided by self-hosted Supabase Auth.</p>
          <SignInForm onSignedIn={() => setSignedIn(true)} />
        </section> : null}
        {signedIn ? <>
        {changeSet ? <section className="admin-card workflow-card" aria-labelledby="editor-heading">
          <p className="eyebrow">Draft editor</p>
          <h2 id="editor-heading">{changeSet.name}</h2>
          <p className="muted-copy">Version {changeSet.version}. Save changes privately before validating or publishing.</p>
          <div className="workspace-tabs" role="tablist" aria-label="Draft data sections">
            {tabs.map((item) => <button key={item} type="button" role="tab" aria-selected={tab === item} className={tab === item ? "active-tab" : "secondary-action"} onClick={() => setTab(item)}>{item}</button>)}
          </div>
          {tab === "Routes" ? <div className="editor-panel"><div className="editor-fields"><input aria-label="Route code" value={route.route_code} placeholder="Route code" onChange={(e) => setRoute({ ...route, route_code: e.target.value })} /><input aria-label="Route origin" value={route.origin} placeholder="Origin" onChange={(e) => setRoute({ ...route, origin: e.target.value })} /><input aria-label="Route destination" value={route.destination} placeholder="Destination" onChange={(e) => setRoute({ ...route, destination: e.target.value })} /><select aria-label="Route direction" value={route.direction} onChange={(e) => setRoute({ ...route, direction: e.target.value as Route["direction"] })}><option value="">Select direction</option><option value="RETURN">RETURN</option><option value="PICK-UP">PICK-UP</option></select></div><button type="button" onClick={addRoute}>Add route</button><DataTable rows={snapshot.routes} columns={["route_code", "origin", "destination", "direction"]} onRemove={(i) => setSnapshot((s) => ({ ...s, routes: s.routes.filter((_, index) => index !== i) }))} /></div> : null}
          {tab === "Buses" ? <div className="editor-panel"><div className="editor-fields"><input aria-label="Bus identifier" value={bus} placeholder="Bus/service identifier" onChange={(e) => setBus(e.target.value)} /></div><button type="button" onClick={addBus}>Add bus</button><DataTable rows={snapshot.buses.map((bus_identifier) => ({ bus_identifier }))} columns={["bus_identifier"]} onRemove={(i) => setSnapshot((s) => ({ ...s, buses: s.buses.filter((_, index) => index !== i) }))} /></div> : null}
          {tab === "Assignments" ? <div className="editor-panel"><SelectPair value={assignment} onChange={setAssignment} routes={snapshot.routes} buses={snapshot.buses} /><button type="button" onClick={addAssignment}>Add assignment</button><DataTable rows={snapshot.assignments} columns={["route_code", "bus_identifier"]} onRemove={(i) => setSnapshot((s) => ({ ...s, assignments: s.assignments.filter((_, index) => index !== i) }))} /></div> : null}
          {tab === "Schedule" ? <div className="editor-panel"><div className="editor-fields"><select aria-label="Route" value={departure.route_code} onChange={(e) => setDeparture((current) => ({ ...current, route_code: e.target.value }))}><option value="">Select route</option>{snapshot.routes.map((item) => <option key={item.route_code} value={item.route_code}>{item.route_code}</option>)}</select><select aria-label="Weekday" value={departure.weekday} onChange={(e) => setDeparture((current) => ({ ...current, weekday: Number(e.target.value) }))}>{["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map((day, i) => <option key={day} value={i + 1}>{i + 1} — {day}</option>)}</select><input aria-label="Departure time" inputMode="numeric" pattern="[0-9]{2}:[0-9]{2}" placeholder="HH:MM" value={departure.departure_time} onChange={(e) => setDeparture((current) => ({ ...current, departure_time: e.target.value }))} /></div><p className="assignment-summary">Assigned buses: {snapshot.assignments.filter((item) => item.route_code === departure.route_code).map((item) => item.bus_identifier).join(", ") || "No buses assigned to this route yet."}</p><button type="button" onClick={addDeparture}>Add recurring departure</button><DataTable rows={snapshot.weekly_departures.map((item) => ({ ...item, buses: snapshot.assignments.filter((assignment) => assignment.route_code === item.route_code).map((assignment) => assignment.bus_identifier).join(", ") || "No buses assigned" }))} columns={["weekday", "route_code", "buses", "departure_time"]} onRemove={(i) => setSnapshot((s) => ({ ...s, weekly_departures: s.weekly_departures.filter((_, index) => index !== i) }))} /></div> : null}
          <div className="action-row">
            <button type="button" onClick={saveDraft} disabled={isSaving}>{isSaving ? "Saving…" : "Save draft"}</button>
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
            <div className="draft-actions"><button disabled={isCreating} type="submit">{isCreating ? "Creating draft…" : "Create draft"}</button><button type="button" className="secondary-action" onClick={searchDrafts}>Search drafts</button></div>
          </form>
          {draftMatches.length ? <ul className="draft-results" aria-label="Matching drafts">{draftMatches.map((draft) => <li key={draft.id}><span><strong>{draft.name}</strong><small>Version {draft.version} · expires {new Date(draft.expires_at).toLocaleDateString()}</small></span><button type="button" className="secondary-action" onClick={() => openDraft(draft.id)}>Open</button></li>)}</ul> : null}
          {notice ? <p className={`notice notice-${notice.tone}`} role="status">{notice.text}</p> : null}
        </section>
        <section className="admin-card workflow-card" aria-labelledby="publish-heading">
          <p className="eyebrow">Protected publication</p>
          <h2 id="publish-heading">Review before publishing</h2>
          <ol>
            <li>Save routes, buses, assignments, and PKT schedule changes to the draft.</li>
            <li>Publishing surfaces any incomplete-assignment warning and requires confirmation.</li>
            <li>Use the separate publish confirmation only when the correct baseline is current.</li>
          </ol>
          <p className="muted-copy">If another change set publishes first, this workspace requires a rebase. Published transport data is never changed by saving a draft.</p>
        </section>
        </> : null}
      </div>
    </main>
  );
}
