"use client";

import { useEffect, useState } from "react";

import { SignInForm } from "../components/sign-in-form";

const apiBaseUrl = process.env.NEXT_PUBLIC_UTS_API_BASE_URL ?? "http://localhost:8000";

type Notice = { tone: "error" | "success" | "warning"; text: string };
type ChangeSet = {
  id: string; name: string; version: number; operation_order?: number | null;
  base_published_change_set_id: string | null;
};
type Publication = { change_set_id: string; publisher: string; published_at: string };
type Route = { route_code: string; origin: string; destination: string; direction: "RETURN" | "PICK-UP" | "" };
type Assignment = { route_code: string; bus_identifier: string };
type Departure = { route_code: string; weekday: number; departure_time: string };
type Override = Assignment & { service_date: string; operation: "add" | "remove"; departure_time: string };
type Snapshot = { routes: Route[]; buses: string[]; assignments: Assignment[]; weekly_departures: Departure[]; overrides: Override[] };
type DraftResponse = ChangeSet & { snapshot: Snapshot; has_published_changes: boolean };
type PublishedAnnouncement = { id: string; title: string; content: string; published_at?: string; expires_at: string | null };
type PublishedBanner = { id: string; announcement_id?: string; title?: string; content?: string; created_at?: string };
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
  const [notice, setNotice] = useState<Notice>();
  const [changeSet, setChangeSet] = useState<ChangeSet>();
  const [snapshot, setSnapshot] = useState<Snapshot>(emptySnapshot);
  const [savedSnapshot, setSavedSnapshot] = useState<Snapshot>(emptySnapshot);
  const [isSaving, setIsSaving] = useState(false);
  const [hasPublishedChanges, setHasPublishedChanges] = useState(false);
  const [editorExpanded, setEditorExpanded] = useState(false);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [tab, setTab] = useState<Tab>("Routes");
  const [route, setRoute] = useState<Route>({ route_code: "", origin: "", destination: "", direction: "" });
  const [bus, setBus] = useState("");
  const [assignment, setAssignment] = useState<Assignment>({ route_code: "", bus_identifier: "" });
  const [departure, setDeparture] = useState<Departure>({ route_code: "", weekday: 1, departure_time: "" });
  const [override, setOverride] = useState<Override>({ route_code: "", bus_identifier: "", service_date: "", operation: "add", departure_time: "" });
  const [announcementTitle, setAnnouncementTitle] = useState("");
  const [announcementContent, setAnnouncementContent] = useState("");
  const [announcementUrgent, setAnnouncementUrgent] = useState(false);
  const [announcementExpiry, setAnnouncementExpiry] = useState("");
  const [showAnnouncementEditor, setShowAnnouncementEditor] = useState(false);
  const [currentAnnouncements, setCurrentAnnouncements] = useState<PublishedAnnouncement[]>([]);
  const [currentBanners, setCurrentBanners] = useState<PublishedBanner[]>([]);
  const [lifecycleExpanded, setLifecycleExpanded] = useState(false);

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

  async function openDraft() {
    if (!headers()) {
      setNotice({ tone: "warning", text: "Sign in before opening the working draft." });
      return;
    }
    setNotice(undefined);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/admin/transport/draft`, { headers: headers() });
      const body = (await response.json()) as DraftResponse & { detail?: string };
      if (!response.ok) {
        setNotice({ tone: "error", text: body.detail ?? "The working draft could not be opened." });
      } else {
        setNotice({ tone: "success", text: "Working draft opened. Changes remain private until published." });
        setChangeSet(body);
        setSnapshot(body.snapshot);
        setSavedSnapshot(body.snapshot);
        setHasPublishedChanges(body.has_published_changes);
        setEditorExpanded(true);
        setTab("Routes");
      }
    } catch {
      setNotice({ tone: "error", text: "The working draft could not be opened. Check the backend connection and try again." });
    }
  }

  function toggleDraftEditor() {
    if (changeSet) {
      setEditorExpanded((expanded) => !expanded);
      return;
    }
    void openDraft();
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
      const body = await response.json() as ChangeSet & { has_published_changes?: boolean; detail?: string | { warnings?: { message: string }[] } };
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
    const body = await requestDraft("draft", {
      method: "PATCH", body: JSON.stringify({ ...snapshot, expected_version: changeSet.version }),
    });
    if (body) {
      setChangeSet(body);
      setSavedSnapshot(snapshot);
      setHasPublishedChanges(Boolean(body.has_published_changes));
      setNotice({ tone: "success", text: `Draft saved privately (operation ${body.operation_order}).` });
    }
    setIsSaving(false);
  }

  async function publishDraft() {
    if (!changeSet) return;
    const publish = async (publishAnyway: boolean) => {
      const response = await fetch(`${apiBaseUrl}/api/v1/admin/transport/draft/publish`, {
        method: "POST", headers: headers(),
        body: JSON.stringify({ publish_anyway: publishAnyway }),
      });
      return { response, body: await response.json() as ChangeSet & { detail?: string | { code?: string; warnings?: { message: string }[] } } };
    };
    try {
      let { response, body } = await publish(false);
      if (!response.ok && typeof body.detail === "object" && body.detail?.code === "publish_confirmation_required") {
        const summary = body.detail.warnings?.map((warning) => warning.message).join("\n") ?? "A route is missing from the schedule.";
        if (window.confirm(`${summary}\n\nPublish anyway?`)) ({ response, body } = await publish(true));
      }
      if (!response.ok) {
        setNotice({ tone: "error", text: typeof body.detail === "string" ? body.detail : "The draft could not be published." });
        return;
      }
      setChangeSet(body);
      setNotice({ tone: "success", text: `Published atomically (operation ${body.operation_order}); the public cache was refreshed.` });
    } catch {
      setNotice({ tone: "error", text: "The publish request could not reach the backend. Check the connection and try again." });
    }
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
      setHistoryExpanded(true);
    } catch {
      setNotice({ tone: "error", text: "Publication history could not be loaded. Check the backend connection and try again." });
    }
  }

  async function recover(changeSetId: string) {
    const body = await requestDraft(`publications/${changeSetId}/recover`, { method: "POST" });
    if (body) { setNotice({ tone: "success", text: "The published change set was recovered as the active transport data." }); await loadPublications(); }
  }

  async function publishAnnouncement() {
    if (!headers()) return setNotice({ tone: "warning", text: "Sign in before publishing an announcement." });
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/admin/announcements`, { method: "POST", headers: headers(), body: JSON.stringify({ title: announcementTitle, content: announcementContent, expires_at: announcementExpiry ? `${announcementExpiry}:00+05:00` : null, urgent: announcementUrgent }) });
      const body = await response.json() as { detail?: string; announcement?: PublishedAnnouncement; banner?: PublishedBanner | null };
      if (!response.ok) return setNotice({ tone: "error", text: body.detail ?? "The announcement could not be published." });
      if (body.announcement) setCurrentAnnouncements((items) => [body.announcement!, ...items.filter((item) => item.id !== body.announcement!.id)]);
      if (body.banner) setCurrentBanners((items) => [body.banner!, ...items.filter((item) => item.id !== body.banner!.id)]);
      setLifecycleExpanded(true);
      setNotice({ tone: "success", text: body.banner ? "Urgent announcement and persistent banner published." : "Announcement published." });
      setAnnouncementTitle(""); setAnnouncementContent(""); setAnnouncementExpiry(""); setAnnouncementUrgent(false);
    } catch { setNotice({ tone: "error", text: "The announcement could not reach the backend." }); }
  }

  async function lifecycleAction(path: string, success: string) {
    if (!headers()) return;
    const response = await fetch(`${apiBaseUrl}/api/v1/admin/${path}`, { method: "POST", headers: headers() });
    if (!response.ok) return setNotice({ tone: "error", text: "The lifecycle action could not be completed." });
    setNotice({ tone: "success", text: success });
    const parts = path.split("/");
    const identifier = parts[1];
    if (path.startsWith("announcements/")) setCurrentAnnouncements((items) => items.filter((item) => item.id !== identifier));
    if (path.startsWith("urgent-banners/")) setCurrentBanners((items) => items.filter((item) => item.id !== identifier));
  }

  async function loadCurrentAnnouncements() {
    if (!headers()) return setNotice({ tone: "warning", text: "Sign in before loading announcements." });
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/admin/announcements/current`, { headers: headers() });
      const body = await response.json() as { announcements?: PublishedAnnouncement[]; banners?: PublishedBanner[]; detail?: string };
      if (!response.ok) return setNotice({ tone: "error", text: body.detail ?? "Current announcements could not be loaded." });
      setCurrentAnnouncements(body.announcements ?? []);
      setCurrentBanners(body.banners ?? []);
      setLifecycleExpanded(true);
    } catch { setNotice({ tone: "error", text: "Current announcements could not be loaded. Check the connection and try again." }); }
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

  const hasUnsavedChanges = JSON.stringify(snapshot) !== JSON.stringify(savedSnapshot);
  const publishDisabled = hasUnsavedChanges || isSaving || !hasPublishedChanges;

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
        <section className="admin-card workflow-card workspace-card" aria-labelledby="editor-heading">
          <div className="section-heading"><div><p className="eyebrow">Draft editor</p><h2 id="editor-heading">{changeSet?.name ?? "Shared draft"}</h2></div><button type="button" className="secondary-action action-button" aria-expanded={Boolean(changeSet && editorExpanded)} aria-controls="draft-editor-content" onClick={toggleDraftEditor}>{changeSet && editorExpanded ? "Collapse draft" : "Expand draft"}</button></div>
          <p className="muted-copy">Save changes privately before publishing. Saves and publications are processed one at a time.</p>
          {notice ? <p className={`notice notice-${notice.tone}`} role="status">{notice.text}</p> : null}
          {changeSet && editorExpanded ? <div id="draft-editor-content">
          <div className="workspace-tabs" role="tablist" aria-label="Draft data sections">
            {tabs.map((item) => <button key={item} type="button" role="tab" aria-selected={tab === item} className={tab === item ? "active-tab" : "secondary-action"} onClick={() => setTab(item)}>{item}</button>)}
          </div>
          {tab === "Routes" ? <div className="editor-panel"><div className="editor-fields"><input aria-label="Route code" value={route.route_code} placeholder="Route code" onChange={(e) => setRoute({ ...route, route_code: e.target.value })} /><input aria-label="Route origin" value={route.origin} placeholder="Origin" onChange={(e) => setRoute({ ...route, origin: e.target.value })} /><input aria-label="Route destination" value={route.destination} placeholder="Destination" onChange={(e) => setRoute({ ...route, destination: e.target.value })} /><select aria-label="Route direction" value={route.direction} onChange={(e) => setRoute({ ...route, direction: e.target.value as Route["direction"] })}><option value="">Select direction</option><option value="RETURN">RETURN</option><option value="PICK-UP">PICK-UP</option></select></div><button type="button" onClick={addRoute}>Add route</button><DataTable rows={snapshot.routes} columns={["route_code", "origin", "destination", "direction"]} onRemove={(i) => setSnapshot((s) => ({ ...s, routes: s.routes.filter((_, index) => index !== i) }))} /></div> : null}
          {tab === "Buses" ? <div className="editor-panel"><div className="editor-fields"><input aria-label="Bus identifier" value={bus} placeholder="Bus/service identifier" onChange={(e) => setBus(e.target.value)} /></div><button type="button" onClick={addBus}>Add bus</button><DataTable rows={snapshot.buses.map((bus_identifier) => ({ bus_identifier }))} columns={["bus_identifier"]} onRemove={(i) => setSnapshot((s) => ({ ...s, buses: s.buses.filter((_, index) => index !== i) }))} /></div> : null}
          {tab === "Assignments" ? <div className="editor-panel"><SelectPair value={assignment} onChange={setAssignment} routes={snapshot.routes} buses={snapshot.buses} /><button type="button" onClick={addAssignment}>Add assignment</button><DataTable rows={snapshot.assignments} columns={["route_code", "bus_identifier"]} onRemove={(i) => setSnapshot((s) => ({ ...s, assignments: s.assignments.filter((_, index) => index !== i) }))} /></div> : null}
          {tab === "Schedule" ? <div className="editor-panel"><div className="editor-fields"><select aria-label="Route" value={departure.route_code} onChange={(e) => setDeparture((current) => ({ ...current, route_code: e.target.value }))}><option value="">Select route</option>{snapshot.routes.map((item) => <option key={item.route_code} value={item.route_code}>{item.route_code}</option>)}</select><select aria-label="Weekday" value={departure.weekday} onChange={(e) => setDeparture((current) => ({ ...current, weekday: Number(e.target.value) }))}>{["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map((day, i) => <option key={day} value={i + 1}>{i + 1} — {day}</option>)}</select><input aria-label="Departure time" inputMode="numeric" pattern="[0-9]{2}:[0-9]{2}" placeholder="HH:MM" value={departure.departure_time} onChange={(e) => setDeparture((current) => ({ ...current, departure_time: e.target.value }))} /></div><p className="assignment-summary">Assigned buses: {snapshot.assignments.filter((item) => item.route_code === departure.route_code).map((item) => item.bus_identifier).join(", ") || "No buses assigned to this route yet."}</p><button type="button" onClick={addDeparture}>Add recurring departure</button><DataTable rows={snapshot.weekly_departures.map((item) => ({ ...item, buses: snapshot.assignments.filter((assignment) => assignment.route_code === item.route_code).map((assignment) => assignment.bus_identifier).join(", ") || "No buses assigned" }))} columns={["weekday", "route_code", "buses", "departure_time"]} onRemove={(i) => setSnapshot((s) => ({ ...s, weekly_departures: s.weekly_departures.filter((_, index) => index !== i) }))} /></div> : null}
          <div className="action-row">
            <button type="button" onClick={saveDraft} disabled={isSaving || !hasUnsavedChanges}>{isSaving ? "Saving…" : "Save draft"}</button>
            <button type="button" onClick={publishDraft} disabled={publishDisabled} title={hasUnsavedChanges ? "Save Draft before publishing." : !hasPublishedChanges ? "The draft matches the published transport data." : undefined}>Publish</button>
          </div>
          </div> : null}
        </section>
        <section className="admin-card workflow-card history-card" aria-labelledby="history-heading">
          <div className="section-heading"><div><p className="eyebrow">Audit</p><h2 id="history-heading">Publication history</h2></div><button type="button" className="secondary-action action-button" aria-expanded={historyExpanded} aria-controls="publication-history" onClick={historyExpanded ? () => setHistoryExpanded(false) : loadPublications}>{historyExpanded ? "Hide history" : "Load history"}</button></div>
          {historyExpanded ? <div id="publication-history"><p className="muted-copy">The latest three changes are shown first. Scroll to view older publication records from the 30-day retention period.</p><div className="publication-list" role="region" aria-label="Publication history records" tabIndex={0}>{publications.map((publication) => <div className="publication" key={publication.change_set_id}><span>{new Date(publication.published_at).toLocaleString()}</span><span>{publication.publisher}</span><button type="button" className="secondary-action" onClick={() => recover(publication.change_set_id)}>Recover</button></div>)}</div></div> : null}
        </section>
        <section className="admin-card workflow-card protected-card" aria-labelledby="publish-heading">
          <p className="eyebrow">Protected publication</p>
          <h2 id="publish-heading">Review before publishing</h2>
          <ol>
            <li>Save routes, buses, assignments, and PKT schedule changes to the draft.</li>
            <li>Publishing warns only when a route has no recurring schedule entry.</li>
            <li>Accepting that warning publishes the current working draft.</li>
          </ol>
          <p className="muted-copy">Saving never changes public transport data. Save and publish requests receive a temporary operation number in their execution order.</p>
        </section>
        <section className="admin-card workflow-card announcement-card" aria-labelledby="announcement-heading">
          <div className="section-heading"><div><p className="eyebrow">Direct publication</p><h2 id="announcement-heading">Announcements</h2></div><button type="button" className="secondary-action action-button" onClick={() => setShowAnnouncementEditor((open) => !open)}>Announcement</button></div>
          <p className="muted-copy">Announcements publish directly. The message is optional. Urgent announcements also create a separate persistent banner.</p>
          {showAnnouncementEditor ? <div className="announcement-form">
            <label>Title<input aria-label="Title" value={announcementTitle} onChange={(event) => setAnnouncementTitle(event.target.value)} /></label>
            <label>Message (optional)<textarea aria-label="Message" value={announcementContent} onChange={(event) => setAnnouncementContent(event.target.value)} /></label>
            <label>Expiry in PKT (optional)<input aria-label="Expiry in PKT" type="datetime-local" value={announcementExpiry} onChange={(event) => setAnnouncementExpiry(event.target.value)} /></label>
            <label><input aria-label="Urgent" type="checkbox" checked={announcementUrgent} onChange={(event) => setAnnouncementUrgent(event.target.checked)} /> Urgent</label>
            <button type="button" onClick={publishAnnouncement}>Publish announcement</button>
          </div> : null}
        </section>
        <section className="admin-card workflow-card announcement-lifecycle-card" aria-labelledby="announcement-lifecycle-heading">
          <div className="section-heading"><div><p className="eyebrow">Lifecycle</p><h2 id="announcement-lifecycle-heading">Current announcements and banners</h2></div><button type="button" className="secondary-action action-button" aria-expanded={lifecycleExpanded} aria-controls="announcement-lifecycle-content" onClick={lifecycleExpanded ? () => setLifecycleExpanded(false) : loadCurrentAnnouncements}>{lifecycleExpanded ? "Hide current items" : "Load current items"}</button></div>
          {lifecycleExpanded ? <div id="announcement-lifecycle-content" className="announcement-lifecycle"><div><h3>Announcements</h3>{currentAnnouncements.length ? currentAnnouncements.map((item) => <div className="lifecycle-item" key={item.id}><strong>{item.title}</strong><button type="button" className="secondary-action" onClick={() => lifecycleAction(`announcements/${item.id}/remove`, "Announcement removed from public display.")}>Remove announcement</button></div>) : <p className="muted-copy">No current announcements.</p>}</div><div><h3>Urgent banners</h3>{currentBanners.length ? currentBanners.map((item) => <div className="lifecycle-item" key={item.id}><strong>{item.title ?? "Urgent banner"}</strong><span><button type="button" className="secondary-action" onClick={() => lifecycleAction(`urgent-banners/${item.id}/remove`, "Urgent banner removed without resolving the issue.")}>Remove banner</button><button type="button" onClick={() => lifecycleAction(`urgent-banners/${item.id}/resolve`, "Urgent banner resolved and removed from public display.")}>Resolve banner</button></span></div>) : <p className="muted-copy">No active urgent banners.</p>}</div></div> : null}
        </section>
        </> : null}
      </div>
    </main>
  );
}
