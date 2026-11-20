import { SignInForm } from "../components/sign-in-form";

export default function AdminHome() {
  return (
    <main className="mx-auto max-w-xl p-6">
      <h1 className="text-3xl font-bold">Transport Management sign in</h1>
      <p className="mt-3">Authentication is provided by self-hosted Supabase Auth.</p>
      <SignInForm />
    </main>
  );
}
