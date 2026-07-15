"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAuthHeader } from "@/lib/supabase";
import { 
  ShieldAlert, Settings, Gift, Wallet, Check, X, 
  Layers, UserCheck, Eye, ClipboardList, Download
} from "lucide-react";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);

  // Verification Form notes
  const [actionNotes, setActionNotes] = useState("");
  const [utrTransaction, setUtrTransaction] = useState("");
  const [activeItem, setActiveItem] = useState<number | null>(null);

  const fetchDashboard = async () => {
    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    try {
      const res = await fetch("/api/admin/dashboard/", {
        headers: { "Authorization": authHeader }
      });
      const data = await res.json();
      if (data && !data.error) {
        setDashboardData(data);
      } else {
        router.push("/");
      }
      setLoading(false);
    } catch (err) {
      console.error("Error loading admin dashboard:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleVerifyProperty = async (submissionId: number, action: "Approve" | "Reject" | "Publish") => {
    const authHeader = await getAuthHeader();
    if (!authHeader) return;

    try {
      const res = await fetch("/api/admin/verify-property/", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": authHeader
        },
        body: JSON.stringify({ submission_id: submissionId, action, notes: actionNotes })
      });
      const data = await res.json();
      if (data.success) {
        setActionNotes("");
        setActiveItem(null);
        fetchDashboard(); // reload
      } else {
        alert(data.error || "Failed to complete verification action.");
      }
    } catch (err) {
      console.error("Verification failed:", err);
    }
  };

  const handleVerifyWithdrawal = async (withdrawalId: number, action: "Pay" | "Reject") => {
    const authHeader = await getAuthHeader();
    if (!authHeader) return;

    if (action === "Pay" && !utrTransaction) {
      alert("UTR Transaction Reference is required to pay.");
      return;
    }

    try {
      const res = await fetch("/api/admin/verify-withdrawal/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader
        },
        body: JSON.stringify({ withdrawal_id: withdrawalId, action, notes: actionNotes, utr: utrTransaction })
      });
      const data = await res.json();
      if (data.success) {
        setActionNotes("");
        setUtrTransaction("");
        setActiveItem(null);
        fetchDashboard(); // reload
      } else {
        alert(data.error || "Failed to process withdrawal action.");
      }
    } catch (err) {
      console.error("Payout failed:", err);
    }
  };

  if (loading) {
    return <div className="p-12 text-center animate-pulse font-semibold">Loading admin dashboard...</div>;
  }

  if (!dashboardData) {
    return <div className="p-12 text-center text-error font-semibold">Access Denied. Staff privilege required.</div>;
  }

  const { stats, submissions, withdrawals } = dashboardData;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full flex-1 flex flex-col gap-8">
      {/* Header */}
      <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold font-plus-jakarta text-on-surface flex items-center gap-2"><Settings className="w-6 h-6 text-primary" /> Admin Operations Panel</h1>
          <p className="text-xs text-on-surface-variant mt-1">Review referral properties queue, approve reward wallets withdrawals, and analyze analytics.</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-primary/10 text-primary rounded-xl mb-3"><ClipboardList className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Active Listings</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.listings_count}</div>
        </div>
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-primary/10 text-primary rounded-xl mb-3"><UserCheck className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Total Users</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.users_count}</div>
        </div>
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-secondary-container/10 text-secondary-container rounded-xl mb-3"><Gift className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Pending Referrals</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.pending_referrals}</div>
        </div>
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-tertiary/10 text-tertiary rounded-xl mb-3"><Wallet className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Pending Payouts</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.pending_withdrawals}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Referrals section */}
        <div className="space-y-6">
          <h2 className="text-sm font-bold text-on-surface flex items-center gap-1.5"><Gift className="w-4 h-4 text-primary" /> Property Referrals Queue</h2>
          
          <div className="space-y-4">
            {submissions && submissions.map((sub: any) => (
              <div key={sub.id} className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xs font-bold text-on-surface">{sub.property_type} Referral</h3>
                    <span className="text-[9px] text-text-muted mt-0.5 block">By {sub.submitter} • {new Date(sub.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className="px-2 py-0.5 bg-secondary-container/10 text-secondary-container rounded-full text-[9px] font-bold">Pending Review</span>
                </div>

                <div className="text-[10px] text-on-surface-variant space-y-1 bg-surface-container-low p-3 rounded-lg leading-relaxed">
                  <div>📍 <strong>Address:</strong> {sub.property_address}, {sub.city}</div>
                  <div>👤 <strong>Owner Name:</strong> {sub.owner_name}</div>
                  <div>📞 <strong>Owner Mobile:</strong> {sub.owner_mobile}</div>
                  {sub.notes && <div className="text-text-muted italic border-t border-outline-variant/30 pt-1 mt-1">📝 Notes: {sub.notes}</div>}
                </div>

                {activeItem === sub.id ? (
                  <div className="space-y-3 pt-2 border-t border-outline-variant/30">
                    <input
                      type="text"
                      placeholder="Add administrative notes/rejection notes..."
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleVerifyProperty(sub.id, "Approve")}
                        className="w-1/3 py-2 bg-primary text-white text-[10px] font-bold rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" /> Approve
                      </button>
                      <button
                        onClick={() => handleVerifyProperty(sub.id, "Publish")}
                        className="w-1/3 py-2 bg-secondary-container text-white text-[10px] font-bold rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-1"
                      >
                        <Layers className="w-3.5 h-3.5" /> Publish
                      </button>
                      <button
                        onClick={() => handleVerifyProperty(sub.id, "Reject")}
                        className="w-1/3 py-2 bg-error text-white text-[10px] font-bold rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-1"
                      >
                        <X className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => { setActiveItem(sub.id); setActionNotes(""); }}
                    className="w-full py-2 bg-surface-container hover:bg-outline-variant/30 text-on-surface rounded-xl text-[10px] font-bold transition-all text-center"
                  >
                    Action Verification
                  </button>
                )}
              </div>
            ))}
            {(!submissions || submissions.length === 0) && (
              <div className="text-center py-12 text-xs text-text-muted font-medium bg-white border border-outline-variant rounded-2xl">Property referral queue is empty.</div>
            )}
          </div>
        </div>

        {/* Withdrawals section */}
        <div className="space-y-6">
          <h2 className="text-sm font-bold text-on-surface flex items-center gap-1.5"><Wallet className="w-4 h-4 text-primary" /> Pending Wallet Payouts</h2>
          
          <div className="space-y-4">
            {withdrawals && withdrawals.map((w: any) => (
              <div key={w.id} className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xs font-bold text-on-surface">₹{w.amount} Request</h3>
                    <span className="text-[9px] text-text-muted mt-0.5 block">By {w.username} • {new Date(w.requested_date).toLocaleDateString()}</span>
                  </div>
                  <span className="px-2 py-0.5 bg-tertiary/10 text-tertiary rounded-full text-[9px] font-bold">Unpaid</span>
                </div>

                <div className="text-[10px] text-on-surface-variant space-y-1 bg-surface-container-low p-3 rounded-lg font-semibold">
                  <div>📱 UPI Address: {w.upi_id}</div>
                </div>

                {activeItem === w.id ? (
                  <div className="space-y-3 pt-2 border-t border-outline-variant/30">
                    <input
                      type="text"
                      placeholder="Enter Bank Transaction Reference / UTR (Required to Pay)"
                      value={utrTransaction}
                      onChange={(e) => setUtrTransaction(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <input
                      type="text"
                      placeholder="Add administrative notes..."
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleVerifyWithdrawal(w.id, "Pay")}
                        className="w-1/2 py-2 bg-primary text-white text-[10px] font-bold rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" /> Pay Payout
                      </button>
                      <button
                        onClick={() => handleVerifyWithdrawal(w.id, "Reject")}
                        className="w-1/2 py-2 bg-error text-white text-[10px] font-bold rounded-lg hover:opacity-90 transition-all flex items-center justify-center gap-1"
                      >
                        <X className="w-3.5 h-3.5" /> Reject Request
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => { setActiveItem(w.id); setActionNotes(""); setUtrTransaction(""); }}
                    className="w-full py-2 bg-surface-container hover:bg-outline-variant/30 text-on-surface rounded-xl text-[10px] font-bold transition-all text-center"
                  >
                    Action Payout
                  </button>
                )}
              </div>
            ))}
            {(!withdrawals || withdrawals.length === 0) && (
              <div className="text-center py-12 text-xs text-text-muted font-medium bg-white border border-outline-variant rounded-2xl">No pending payout requests found.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
