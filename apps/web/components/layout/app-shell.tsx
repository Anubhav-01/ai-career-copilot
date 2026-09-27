"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BrainCircuit,
  FileText,
  GraduationCap,
  KanbanSquare,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  Search,
  Settings,
  Sparkles,
  User as UserIcon,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, tokenStore } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { User } from "@/types/api";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/resume", label: "Resumes", icon: FileText },
  { href: "/jobs", label: "Jobs", icon: Search },
  { href: "/skills", label: "Skills & Gaps", icon: BrainCircuit },
  { href: "/learning", label: "Learning", icon: GraduationCap },
  { href: "/interview", label: "Interviews", icon: MessageSquareText },
  { href: "/applications", label: "Applications", icon: KanbanSquare },
];

const secondary = [
  { href: "/profile", label: "Profile", icon: UserIcon },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!tokenStore.access) {
      router.replace("/auth/login");
    } else {
      setReady(true);
    }
  }, [router]);

  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: () => api<User>("/api/auth/me"),
    enabled: ready,
  });

  const logout = async () => {
    const refresh = tokenStore.refresh;
    if (refresh) {
      try {
        await api("/api/auth/logout", { method: "POST", body: { refresh_token: refresh } });
      } catch {
        // best-effort; local tokens are cleared regardless
      }
    }
    tokenStore.clear();
    router.push("/auth/login");
  };

  if (!ready) return null;

  const navLinks = (
    <>
      <nav className="flex-1 space-y-1 px-3">
        {navigation.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
              )}
            >
              <item.icon className="h-4 w-4" aria-hidden />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="space-y-1 border-t border-slate-200 px-3 py-3">
        {secondary.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setSidebarOpen(false)}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
              pathname.startsWith(item.href)
                ? "bg-brand-50 text-brand-700"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
            )}
          >
            <item.icon className="h-4 w-4" aria-hidden />
            {item.label}
          </Link>
        ))}
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
        >
          <LogOut className="h-4 w-4" aria-hidden />
          Log out
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="flex h-16 items-center gap-2 px-6 font-semibold text-slate-900">
          <Sparkles className="h-5 w-5 text-brand-600" aria-hidden />
          Career Copilot
        </div>
        {navLinks}
      </aside>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setSidebarOpen(false)} aria-hidden />
          <aside className="absolute inset-y-0 left-0 flex w-64 flex-col bg-white">
            <div className="flex h-16 items-center justify-between px-4">
              <span className="flex items-center gap-2 font-semibold">
                <Sparkles className="h-5 w-5 text-brand-600" aria-hidden />
                Career Copilot
              </span>
              <button onClick={() => setSidebarOpen(false)} aria-label="Close menu">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>
            {navLinks}
          </aside>
        </div>
      )}

      <div className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-8">
          <button
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden lg:block" />
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-slate-500 sm:block">{user?.email}</span>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
              {user?.full_name?.charAt(0).toUpperCase() ?? "?"}
            </span>
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
