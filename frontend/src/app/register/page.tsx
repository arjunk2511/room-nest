"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase, isMockAuth, setMockUser } from "@/lib/supabase";
import { Lock, Mail, User, ChevronRight } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    if (isMockAuth) {
      // Mock Sign Up Fallback
      setMockUser(email);
      setSuccess("Account registered successfully (Dev Mode)!");
      setTimeout(() => {
        router.push("/");
        router.refresh();
      }, 1000);
      return;
    }

    try {
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      });

      if (signUpError) {
        setError(signUpError.message);
        setLoading(false);
      } else {
        setSuccess("Check your email for confirmation link!");
        setLoading(false);
      }
    } catch (err: any) {
      setError("An unexpected error occurred.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-20 w-full flex-1 flex flex-col justify-center">
      <div className="bg-white border border-outline-variant rounded-2xl p-6 md:p-8 shadow-md">
        <h1 className="text-xl md:text-2xl font-extrabold font-plus-jakarta text-on-surface mb-2 text-center">Create account</h1>
        <p className="text-xs text-on-surface-variant text-center mb-8">Join RoomNest and start searching or listing today.</p>

        {isMockAuth && (
          <div className="mb-6 p-4 bg-primary/10 rounded-xl text-xs text-primary font-semibold leading-relaxed border border-primary/20">
            ℹ️ <strong>Dev Mode Active</strong>: Enter any email and password to mock register. A matching User profile will be generated automatically in the database.
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-2">Email Address</label>
            <div className="flex items-center gap-2 bg-surface-container-low border border-outline-variant rounded-xl p-3 focus-within:ring-1 focus-within:ring-primary">
              <Mail className="w-4 h-4 text-primary shrink-0" />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border-none focus:outline-none text-xs text-on-surface bg-transparent"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-2">Password</label>
            <div className="flex items-center gap-2 bg-surface-container-low border border-outline-variant rounded-xl p-3 focus-within:ring-1 focus-within:ring-primary">
              <Lock className="w-4 h-4 text-primary shrink-0" />
              <input
                type="password"
                placeholder="Minimum 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border-none focus:outline-none text-xs text-on-surface bg-transparent"
                required
              />
            </div>
          </div>

          {error && <p className="text-xs text-error font-medium text-center">{error}</p>}
          {success && <p className="text-xs text-primary font-medium text-center">{success}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-primary text-white rounded-xl text-xs font-extrabold hover:opacity-90 active:scale-95 transition-all shadow-md shadow-primary/15 disabled:opacity-50"
          >
            {loading ? "Registering..." : "Sign Up"}
          </button>
        </form>

        <div className="mt-8 text-center border-t border-outline-variant/30 pt-6">
          <p className="text-xs text-on-surface-variant">
            Already have an account?{" "}
            <Link href="/login" className="text-primary font-bold hover:underline inline-flex items-center gap-0.5">
              Sign In <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
