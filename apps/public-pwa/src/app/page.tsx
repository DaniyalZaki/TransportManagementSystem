"use client";

import { useEffect, useState } from "react";

type CurrentDeparture = { route_id: string; bus_identifier: string; status: "scheduled" | "no_further_departures_today"; scheduled_departure_at: string | null };
type ScheduleEntry = { route_id: string; origin: string; destination: string; direction: "RETURN" | "PICK-UP"; bus_identifiers: string[]; scheduled_departure_at: string };
type CurrentDeparturesResponse = { service_date: string; published_at: string; departures: CurrentDeparture[] };
type ScheduleResponse = { service_date: string; service_status: "operating" | "no_service"; published_at: string; entries: ScheduleEntry[] };

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function formatTime(instant: string): string {
  return new Intl.DateTimeFormat("en-PK", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Karachi" }).format(new Date(instant));
}

function formatDate(serviceDate: string): string {
  return new Intl.DateTimeFormat("en-PK", { weekday: "long", day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Karachi" }).format(new Date(`${serviceDate}T00:00:00+05:00`));
}

export default function PublicHome() {
  const [current, setCurrent] = useState<CurrentDeparturesResponse | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [isUnavailable, setUnavailable] = useState(false);

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
    return () => { active = false; };
  }, []);

  return <main className="public-shell">
    <header className="public-header"><p className="public-eyebrow">Official transport information</p><h1>Uzair Transport Service</h1><p>Published transport information for the university community, shown in Pakistan Standard Time.</p></header>
    {isUnavailable ? <section aria-live="polite" className="public-notice"><h2>Transport information unavailable</h2><p>Please try again shortly.</p></section> : null}
    {current ? <section className="public-card" aria-labelledby="current-departures-heading"><div className="section-title"><div><p className="public-eyebrow">Live timetable</p><h2 id="current-departures-heading">Next departures</h2></div><time dateTime={current.service_date}>{formatDate(current.service_date)}</time></div><ul className="departure-list" aria-label="Current published departures">{current.departures.map((departure) => <li key={`${departure.route_id}-${departure.bus_identifier}`}><div><strong>{departure.route_id}</strong><span>{departure.bus_identifier}</span></div>{departure.status === "scheduled" && departure.scheduled_departure_at ? <time dateTime={departure.scheduled_departure_at}>{formatTime(departure.scheduled_departure_at)} <small>PKT</small></time> : <p>No further departures today</p>}</li>)}</ul></section> : null}
    {schedule ? <section className="public-card" aria-labelledby="schedule-heading"><div className="section-title"><div><p className="public-eyebrow">Published timetable</p><h2 id="schedule-heading">Today&apos;s schedule</h2></div><time dateTime={schedule.service_date}>{formatDate(schedule.service_date)}</time></div>{schedule.service_status === "no_service" ? <p className="empty-state">No service is scheduled today.</p> : <div className="schedule-table-wrap"><table className="public-schedule"><thead><tr><th>Time</th><th>Route</th><th>Buses</th><th>Direction</th></tr></thead><tbody>{schedule.entries.map((entry) => <tr key={`${entry.route_id}-${entry.scheduled_departure_at}`}><td><time dateTime={entry.scheduled_departure_at}>{formatTime(entry.scheduled_departure_at)}</time></td><td><strong>{entry.route_id}</strong><span>{entry.origin} → {entry.destination}</span></td><td>{entry.bus_identifiers.join(", ") || "No buses assigned"}</td><td>{entry.direction}</td></tr>)}</tbody></table></div>}</section> : null}
  </main>;
}
