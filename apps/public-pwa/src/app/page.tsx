"use client";

import { useEffect, useState } from "react";

type CurrentDeparture = {
  route_id: string;
  bus_identifier: string;
  status: "scheduled" | "no_further_departures_today";
  scheduled_departure_at: string | null;
};

type ScheduleEntry = {
  route_id: string;
  origin: string;
  destination: string;
  direction: string;
  bus_identifier: string;
  scheduled_departure_at: string;
};

type CurrentDeparturesResponse = {
  service_date: string;
  published_at: string;
  departures: CurrentDeparture[];
};

type ScheduleResponse = {
  service_date: string;
  service_status: "operating" | "no_service";
  published_at: string;
  entries: ScheduleEntry[];
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function formatTime(instant: string): string {
  return new Intl.DateTimeFormat("en-PK", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Karachi",
  }).format(new Date(instant));
}

export default function PublicHome() {
  const [current, setCurrent] = useState<CurrentDeparturesResponse | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [isUnavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    const loadPublishedTransport = async () => {
      try {
        const [currentResponse, scheduleResponse] = await Promise.all([
          fetch(`${apiBaseUrl}/api/v1/public/transport/current-departures`),
          fetch(`${apiBaseUrl}/api/v1/public/transport/schedule`),
        ]);
        if (!currentResponse.ok || !scheduleResponse.ok) {
          throw new Error("Published transport information is unavailable");
        }
        const [currentData, scheduleData] = (await Promise.all([
          currentResponse.json(),
          scheduleResponse.json(),
        ])) as [CurrentDeparturesResponse, ScheduleResponse];
        if (active) {
          setCurrent(currentData);
          setSchedule(scheduleData);
        }
      } catch {
        if (active) {
          setUnavailable(true);
        }
      }
    };
    void loadPublishedTransport();
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="mx-auto max-w-3xl space-y-8 p-6">
      <header>
        <h1 className="text-3xl font-bold">Uzair Transport Service</h1>
        <p className="mt-2 text-slate-700">
          Official published transport information for the university community.
        </p>
      </header>

      {isUnavailable ? (
        <section aria-live="polite" className="rounded border border-amber-700 p-4">
          <h2 className="text-xl font-semibold">Transport information unavailable</h2>
          <p className="mt-1">Please try again shortly.</p>
        </section>
      ) : null}

      {current ? (
        <section aria-labelledby="current-departures-heading">
          <h2 id="current-departures-heading" className="text-2xl font-semibold">
            Next departures
          </h2>
          <ul className="mt-3 space-y-3" aria-label="Current published departures">
            {current.departures.map((departure) => (
              <li
                className="rounded border border-slate-300 bg-white p-4"
                key={`${departure.route_id}-${departure.bus_identifier}`}
              >
                <div className="flex items-baseline justify-between gap-4">
                  <p className="font-semibold">
                    {departure.route_id} · {departure.bus_identifier}
                  </p>
                  {departure.status === "scheduled" && departure.scheduled_departure_at ? (
                    <time dateTime={departure.scheduled_departure_at}>
                      {formatTime(departure.scheduled_departure_at)} PKT
                    </time>
                  ) : null}
                </div>
                {departure.status === "no_further_departures_today" ? (
                  <p className="mt-1">No further departures today</p>
                ) : (
                  <p className="mt-1 text-slate-700">Scheduled departure</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {schedule ? (
        <section aria-labelledby="schedule-heading">
          <h2 id="schedule-heading" className="text-2xl font-semibold">
            Today&apos;s schedule
          </h2>
          {schedule.service_status === "no_service" ? (
            <p className="mt-3">No service is scheduled today.</p>
          ) : (
            <ul className="mt-3 divide-y rounded border border-slate-300 bg-white">
              {schedule.entries.map((entry) => (
                <li
                  className="grid gap-1 p-4 sm:grid-cols-[7rem_1fr]"
                  key={`${entry.route_id}-${entry.bus_identifier}-${entry.scheduled_departure_at}`}
                >
                  <time className="font-semibold" dateTime={entry.scheduled_departure_at}>
                    {formatTime(entry.scheduled_departure_at)} PKT
                  </time>
                  <div>
                    <p className="font-semibold">
                      {entry.route_id} · {entry.bus_identifier}
                    </p>
                    <p>{entry.origin} → {entry.destination}</p>
                    <p className="text-slate-700">{entry.direction}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}
    </main>
  );
}
