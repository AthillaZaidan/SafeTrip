import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-cloud px-4 py-12">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-navy">
          Safe Trip
        </h1>
        <p className="mt-2 text-sm font-medium text-muted">
          AI-powered safety for public transportation
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
