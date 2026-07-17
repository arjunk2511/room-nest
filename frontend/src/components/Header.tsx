"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase, isMockAuth, getMockUser, clearMockUser } from "@/lib/supabase";
import { User, Menu, X, LogOut, ChevronDown } from "lucide-react";

export default function Header() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    if (isMockAuth) {
      setUser(getMockUser());
    } else {
      supabase.auth.getUser().then(({ data: { user } }) => {
        setUser(user);
      });

      const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
        setUser(session?.user ?? null);
      });

      return () => subscription.unsubscribe();
    }
  }, []);

  const handleLogout = async () => {
    if (isMockAuth) {
      clearMockUser();
      setUser(null);
      router.push("/");
    } else {
      await supabase.auth.signOut();
      setUser(null);
      router.push("/");
    }
    setDropdownOpen(false);
  };

  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : "U";

  return (
    <header className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-10 h-16 glass-nav bg-white/80 border-b border-outline-variant shadow-sm transition-all duration-300">
      <div className="flex items-center gap-6">
        <Link href="/" className="text-xl font-bold font-plus-jakarta text-primary tracking-tight">
          RoomNest
        </Link>
        <nav className="hidden md:flex gap-6 ml-6">
          <Link href="/" className="text-sm font-semibold text-primary hover:text-primary-container transition-colors">
            Home
          </Link>
          <Link href="/search" className="text-sm font-semibold text-on-surface-variant hover:text-primary transition-colors">
            Properties
          </Link>
          <Link href="/blog" className="text-sm font-semibold text-on-surface-variant hover:text-primary transition-colors">
            Blog
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <Link href="/add-property" className="hidden sm:inline-block px-4 py-1.5 rounded-full text-xs font-semibold text-primary border border-primary hover:bg-primary/5 transition-all">
          Post Property
        </Link>

        {user ? (
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-1.5 focus:outline-none p-1 rounded-full hover:bg-surface-container transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-primary-container text-white flex items-center justify-center font-bold text-sm">
                {userInitial}
              </div>
              <ChevronDown className="w-4 h-4 text-on-surface-variant" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-outline-variant rounded-xl shadow-lg py-1 z-50">
                <Link
                  href="/profile"
                  onClick={() => setDropdownOpen(false)}
                  className="block px-4 py-2 text-sm text-on-surface hover:bg-surface-container-low transition-colors"
                >
                  Dashboard & Wallet
                </Link>
                {user.email === "admin@roomnest.online" && (
                  <Link
                    href="/admin/dashboard"
                    onClick={() => setDropdownOpen(false)}
                    className="block px-4 py-2 text-sm font-medium text-primary hover:bg-surface-container-low transition-colors"
                  >
                    Admin Operations
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="w-full text-left flex items-center gap-2 px-4 py-2 text-sm text-error hover:bg-error-container/20 transition-colors border-t border-outline-variant/30"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link href="/login" className="px-4 py-1.5 rounded-full text-xs font-semibold bg-primary-container text-white hover:opacity-95 transition-all">
              Login
            </Link>
          </div>
        )}

        <button onClick={() => setMenuOpen(!menuOpen)} className="inline-block md:hidden text-on-surface p-1">
          {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu Drawer */}
      {menuOpen && (
        <div className="absolute top-16 left-0 w-full bg-white border-b border-outline-variant flex flex-col p-6 gap-4 z-40 shadow-md md:hidden">
          <Link href="/" onClick={() => setMenuOpen(false)} className="text-sm font-semibold text-on-surface">Home</Link>
          <Link href="/search" onClick={() => setMenuOpen(false)} className="text-sm font-semibold text-on-surface">Properties</Link>
          <Link href="/blog" onClick={() => setMenuOpen(false)} className="text-sm font-semibold text-on-surface">Blog</Link>
          <Link href="/add-property" onClick={() => setMenuOpen(false)} className="w-full text-center py-2 rounded-full border border-primary text-primary text-sm font-semibold">Post Property</Link>
          
          {user ? (
            <>
              <div className="border-t border-outline-variant/30 my-1"></div>
              <Link
                href="/profile"
                onClick={() => setMenuOpen(false)}
                className="text-sm font-semibold text-on-surface flex items-center gap-2"
              >
                <User className="w-4 h-4 text-on-surface-variant" />
                Profile Settings
              </Link>
              <button
                onClick={() => {
                  if (confirm("Are you sure you want to log out?")) {
                    handleLogout();
                    setMenuOpen(false);
                  }
                }}
                className="text-sm font-semibold text-error flex items-center gap-2 text-left focus:outline-none"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </>
          ) : (
            <>
              <div className="border-t border-outline-variant/30 my-1"></div>
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                className="text-sm font-semibold text-primary flex items-center gap-2"
              >
                <User className="w-4 h-4" />
                Login
              </Link>
            </>
          )}
        </div>
      )}
    </header>
  );
}
