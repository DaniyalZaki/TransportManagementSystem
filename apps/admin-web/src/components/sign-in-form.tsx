"use client";

import { Button, Field, Input, Label } from "@headlessui/react";
import { FormEvent, useState } from "react";

const apiBaseUrl = process.env.NEXT_PUBLIC_UTS_API_BASE_URL ?? "http://localhost:8000";

export function SignInForm() {
  const [message, setMessage] = useState<string>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage(undefined);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiBaseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
    });
    const payload = (await response.json()) as { access_token?: string; detail?: string };
    if (!response.ok || !payload.access_token) {
      setMessage(payload.detail ?? "Sign-in could not be completed. Please try again.");
      setIsSubmitting(false);
      return;
    }
    sessionStorage.setItem("uts.access-token", payload.access_token);
    setMessage("Signed in. Transport management features will be available here.");
    setIsSubmitting(false);
  }

  return (
    <form className="mt-6 space-y-4" onSubmit={submit}>
      <Field>
        <Label className="block font-semibold" htmlFor="email">
          Email address
        </Label>
        <Input
          className="mt-1 block w-full rounded border border-slate-400 bg-white px-3 py-2"
          id="email"
          name="email"
          required
          type="email"
        />
      </Field>
      <Field>
        <Label className="block font-semibold" htmlFor="password">
          Password
        </Label>
        <Input
          className="mt-1 block w-full rounded border border-slate-400 bg-white px-3 py-2"
          id="password"
          name="password"
          required
          type="password"
        />
      </Field>
      <Button
        className="rounded bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Signing in…" : "Sign in"}
      </Button>
      {message ? <p aria-live="polite">{message}</p> : null}
    </form>
  );
}
