"use client";

import { useEffect, useState } from "react";

type CurrentDeparture = { route_id: string; bus_identifier: string; status: "scheduled" | "no_further_departures_today"; scheduled_departure_at: string | null };
type ScheduleEntry = { route_id: string; origin: string; destination: string; direction: "RETURN" | "PICK-UP"; bus_identifiers: string[]; scheduled_departure_at: string };
type CurrentDeparturesResponse = { service_date: string; published_at: string; departures: CurrentDeparture[] };
type ScheduleResponse = { service_date: string; service_status: "operating" | "no_service"; published_at: string; entries: ScheduleEntry[] };
type Announcement = { id: string; title: string; content: string; published_at: string; expires_at: string | null };
type UrgentBanner = { id: string; announcement_id: string; title: string; content: string; created_at: string };

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function formatTime(instant: string): string {
  return new Intl.DateTimeFormat("en-PK", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Karachi" }).format(new Date(instant));
}

function formatDate(serviceDate: string): string {
  return new Intl.DateTimeFormat("en-PK", { weekday: "long", day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Karachi" }).format(new Date(`${serviceDate}T00:00:00+05:00`));
}

function groupDepartures(departures: CurrentDeparture[]) {
  const groups = new Map<string, CurrentDeparture[]>();
  for (const departure of departures) {
    const key = `${departure.route_id}|${departure.status}|${departure.scheduled_departure_at ?? ""}`;
    groups.set(key, [...(groups.get(key) ?? []), departure]);
  }
  return [...groups.values()];
}

export default function PublicHome() {
  const [current, setCurrent] = useState<CurrentDeparturesResponse | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [banners, setBanners] = useState<UrgentBanner[]>([]);
  const [isUnavailable, setUnavailable] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [isSendingFeedback, setSendingFeedback] = useState(false);

  async function submitFeedback(form: HTMLFormElement) {
    const data = new FormData(form);
    setFeedbackMessage(null); setFeedbackError(null); setSendingFeedback(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/public/feedback`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: data.get("content"), name: data.get("name") || null, contact: data.get("contact") || null, honeypot: data.get("honeypot") || "" }) });
      const body = await response.json() as { message?: string };
      if (!response.ok) throw new Error(body.message ?? "Feedback could not be delivered now. Please try again later.");
      setFeedbackMessage(body.message ?? "Feedback received. Thank you."); form.reset();
    } catch (error) { setFeedbackError(error instanceof Error ? error.message : "Feedback could not be delivered now. Please try again later."); }
    finally { setSendingFeedback(false); }
  }

  useEffect(() => {
    let active = true;
    void Promise.all([
      fetch(`${apiBaseUrl}/api/v1/public/transport/current-departures`),
      fetch(`${apiBaseUrl}/api/v1/public/transport/schedule`),
    ]).then(async ([currentResponse, scheduleResponse]) => {
      if (!currentResponse.ok || !scheduleResponse.ok) throw new Error("Published transport information is unavailable");
      const [currentData, scheduleData] = await Promise.all([currentResponse.json(), scheduleResponse.json()]) as [CurrentDeparturesResponse, ScheduleResponse];
      if (active) { setCurrent(currentData); setSchedule(scheduleData); }
    }).catch(() => { if (active) setUnavailable(true); });
    void Promise.all([
      fetch(`${apiBaseUrl}/api/v1/public/announcements`),
      fetch(`${apiBaseUrl}/api/v1/public/urgent-banners`),
    ]).then(async ([announcementResponse, bannerResponse]) => {
      if (!announcementResponse.ok || !bannerResponse.ok) return;
      const [announcementData, bannerData] = await Promise.all([announcementResponse.json(), bannerResponse.json()]) as [{ announcements: Announcement[] }, { banners: UrgentBanner[] }];
      if (active) { setAnnouncements(announcementData.announcements); setBanners(bannerData.banners); }
    });
    return () => { active = false; };
  }, []);

  return <main className="public-shell">
    <header className="public-header"><p className="public-eyebrow">Official transport information</p><h1>Uzair Transport Service</h1><p>Published transport information for the university community, shown in Pakistan Standard Time.</p></header>
    {isUnavailable ? <section aria-live="polite" className="public-notice"><h2>Transport information unavailable</h2><p>Please try again shortly.</p></section> : null}
    {banners.length ? <section className="urgent-banner-list" aria-labelledby="urgent-notices-heading"><h2 id="urgent-notices-heading">Urgent notices</h2>{banners.map((banner) => <article className="urgent-banner" key={banner.id}><strong>{banner.title}</strong><p>{banner.content}</p></article>)}</section> : null}
    {current ? <section className="public-card" aria-labelledby="current-departures-heading"><div className="section-title"><div><p className="public-eyebrow">Live timetable</p><h2 id="current-departures-heading">Next departures</h2></div><time dateTime={current.service_date}>{formatDate(current.service_date)}</time></div><ul className="departure-list" aria-label="Current published departures">{groupDepartures(current.departures).map((departures) => { const departure = departures[0]; return <li key={`${departure.route_id}-${departure.status}-${departure.scheduled_departure_at}`}><div><strong>{departure.route_id}</strong><span>{departures.map((item) => item.bus_identifier).join(", ")}</span></div>{departure.status === "scheduled" && departure.scheduled_departure_at ? <time dateTime={departure.scheduled_departure_at}>{formatTime(departure.scheduled_departure_at)} <small>PKT</small></time> : <p>No further departures today</p>}</li>; })}</ul></section> : null}
    {schedule ? <section className="public-card" aria-labelledby="schedule-heading"><div className="section-title"><div><p className="public-eyebrow">Published timetable</p><h2 id="schedule-heading">Today&apos;s schedule</h2></div><time dateTime={schedule.service_date}>{formatDate(schedule.service_date)}</time></div>{schedule.service_status === "no_service" ? <p className="empty-state">No service is scheduled today.</p> : <div className="schedule-table-wrap"><table className="public-schedule"><thead><tr><th>Time</th><th>Route</th><th>Buses</th><th>Direction</th></tr></thead><tbody>{schedule.entries.map((entry) => <tr key={`${entry.route_id}-${entry.scheduled_departure_at}`}><td><time dateTime={entry.scheduled_departure_at}>{formatTime(entry.scheduled_departure_at)}</time></td><td><strong>{entry.route_id}</strong><span>{entry.origin} → {entry.destination}</span></td><td>{entry.bus_identifiers.join(", ") || "No buses assigned"}</td><td>{entry.direction}</td></tr>)}</tbody></table></div>}</section> : null}
    {announcements.length ? <section className="public-card" aria-labelledby="announcements-heading"><div className="section-title"><div><p className="public-eyebrow">Published notices</p><h2 id="announcements-heading">Announcements</h2></div></div><ul className="announcement-list">{announcements.map((announcement) => <li key={announcement.id}><strong>{announcement.title}</strong><p>{announcement.content}</p><time dateTime={announcement.published_at}>{formatTime(announcement.published_at)} PKT</time></li>)}</ul></section> : null}
    <section className="public-card feedback-card" aria-labelledby="feedback-heading"><p className="public-eyebrow">Contact transport management</p><h2 id="feedback-heading">Send feedback</h2><p>Share a transport issue or suggestion. Name and contact details are optional.</p><form onSubmit={(event) => { event.preventDefault(); void submitFeedback(event.currentTarget); }}><label htmlFor="feedback-content">Feedback</label><textarea id="feedback-content" name="content" required maxLength={4000} /><label htmlFor="feedback-name">Name <span>(optional)</span></label><input id="feedback-name" name="name" maxLength={180} /><label htmlFor="feedback-contact">Contact details <span>(optional)</span></label><input id="feedback-contact" name="contact" maxLength={320} /><div className="honeypot-field" aria-hidden="true"><label htmlFor="feedback-website">Website</label><input id="feedback-website" name="honeypot" tabIndex={-1} autoComplete="off" /></div><button type="submit" disabled={isSendingFeedback}>{isSendingFeedback ? "Sending feedback…" : "Send feedback"}</button></form>{feedbackMessage ? <p role="status" className="feedback-success">{feedbackMessage}</p> : null}{feedbackError ? <p role="alert" className="feedback-error">{feedbackError}</p> : null}</section>
  </main>;
}
