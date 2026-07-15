"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAuthHeader } from "@/lib/supabase";
import { Wallet, Bell, Gift, PlusCircle, User, CreditCard, ChevronRight, Settings } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [profileData, setProfileData] = useState<any>(null);
  
  // Dashboard Tabs
  const [activeTab, setActiveTab] = useState<"wallet" | "referral" | "notifs" | "settings">("wallet");

  // Profile Update Form
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState("");
  const [updateError, setUpdateError] = useState("");

  // Withdrawal Request Form
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [withdrawUpi, setWithdrawUpi] = useState("");
  const [withdrawSuccess, setWithdrawSuccess] = useState("");
  const [withdrawError, setWithdrawError] = useState("");

  // Property Referral Form
  const [citiesList, setCitiesList] = useState<any[]>([]);
  const [refName, setRefName] = useState("");
  const [refMobile, setRefMobile] = useState("");
  const [refOwnerName, setRefOwnerName] = useState("");
  const [refOwnerMobile, setRefOwnerMobile] = useState("");
  const [refPropType, setRefPropType] = useState("Room");
  const [refPropAddress, setRefPropAddress] = useState("");
  const [refCityId, setRefCityId] = useState("");
  const [refNotes, setRefNotes] = useState("");
  const [refSuccess, setRefSuccess] = useState("");
  const [refError, setRefError] = useState("");

  const fetchProfile = async () => {
    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    try {
      const res = await fetch("/api/profile/", {
        headers: { "Authorization": authHeader }
      });
      const data = await res.json();
      if (data && !data.error) {
        setProfileData(data);
        setFirstName(data.first_name || "");
        setLastName(data.last_name || "");
        setPhone(data.phone || "");
      } else {
        router.push("/login");
      }
      setLoading(false);
    } catch (err) {
      console.error("Error fetching profile:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    
    // Load cities for referral form
    fetch("/api/cities-areas/")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCitiesList(data);
          if (data.length > 0) setRefCityId(data[0].id.toString());
        }
      });
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdateSuccess("");
    setUpdateError("");

    const authHeader = await getAuthHeader();
    if (!authHeader) return;

    try {
      const res = await fetch("/api/profile/update/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader
        },
        body: JSON.stringify({ first_name: firstName, last_name: lastName, phone })
      });
      const data = await res.json();
      if (data.success) {
        setUpdateSuccess("Profile updated successfully!");
        fetchProfile();
      } else {
        setUpdateError(data.error || "Failed to update profile.");
      }
    } catch (err) {
      setUpdateError("An unexpected error occurred.");
    }
  };

  const handleWithdrawal = async (e: React.FormEvent) => {
    e.preventDefault();
    setWithdrawSuccess("");
    setWithdrawError("");

    const authHeader = await getAuthHeader();
    if (!authHeader) return;

    try {
      const res = await fetch("/api/wallet/withdraw/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader
        },
        body: JSON.stringify({ amount: withdrawAmount, upi_id: withdrawUpi })
      });
      const data = await res.json();
      if (data.success) {
        setWithdrawSuccess("Withdrawal request submitted successfully!");
        setWithdrawAmount("");
        fetchProfile();
      } else {
        setWithdrawError(data.error || "Failed to submit request.");
      }
    } catch (err) {
      setWithdrawError("An unexpected error occurred.");
    }
  };

  const handlePostReferral = async (e: React.FormEvent) => {
    e.preventDefault();
    setRefSuccess("");
    setRefError("");

    const authHeader = await getAuthHeader();
    if (!authHeader) return;

    try {
      const res = await fetch("/api/listings/refer/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader
        },
        body: JSON.stringify({
          submitted_by_name: refName,
          submitted_by_mobile: refMobile,
          owner_name: refOwnerName,
          owner_mobile: refOwnerMobile,
          property_type: refPropType,
          property_address: refPropAddress,
          city: refCityId,
          notes: refNotes,
          permission_confirmed: true
        })
      });
      const data = await res.json();
      if (data.success) {
        setRefSuccess("Referral property submitted successfully!");
        setRefName("");
        setRefMobile("");
        setRefOwnerName("");
        setRefOwnerMobile("");
        setRefPropAddress("");
        setRefNotes("");
        fetchProfile();
      } else {
        setRefError(data.error || "Failed to submit referral.");
      }
    } catch (err) {
      setRefError("An unexpected error occurred.");
    }
  };

  if (loading) {
    return <div className="p-12 text-center animate-pulse font-semibold">Loading tenant dashboard...</div>;
  }

  if (!profileData) {
    return <div className="p-12 text-center text-error font-semibold">Unable to fetch profile details.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full flex-1 flex flex-col md:flex-row gap-8">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 shrink-0 bg-white border border-outline-variant rounded-2xl p-5 shadow-sm h-fit">
        <div className="flex items-center gap-3 pb-5 border-b border-outline-variant/30 mb-6">
          <div className="w-12 h-12 bg-primary-container text-white rounded-full flex items-center justify-center font-bold text-lg">
            {profileData.email.charAt(0).toUpperCase()}
          </div>
          <div>
            <h4 className="text-xs font-bold text-on-surface">{profileData.first_name ? `${profileData.first_name} ${profileData.last_name}` : "RoomNest Member"}</h4>
            <p className="text-[10px] text-on-surface-variant mt-0.5">{profileData.email}</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1 text-xs font-bold text-on-surface-variant">
          <button
            onClick={() => setActiveTab("wallet")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-xl transition-all text-left ${
              activeTab === "wallet" ? "bg-primary text-white" : "hover:bg-surface-container-low"
            }`}
          >
            <Wallet className="w-4 h-4" /> Wallet & Rewards
          </button>
          <button
            onClick={() => setActiveTab("referral")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-xl transition-all text-left ${
              activeTab === "referral" ? "bg-primary text-white" : "hover:bg-surface-container-low"
            }`}
          >
            <Gift className="w-4 h-4" /> Refer & Earn ₹50
          </button>
          <button
            onClick={() => setActiveTab("notifs")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-xl transition-all text-left ${
              activeTab === "notifs" ? "bg-primary text-white" : "hover:bg-surface-container-low"
            }`}
          >
            <Bell className="w-4 h-4" /> Notifications ({profileData.notifications?.filter((n: any) => !n.is_read).length || 0})
          </button>
          <button
            onClick={() => setActiveTab("settings")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-xl transition-all text-left ${
              activeTab === "settings" ? "bg-primary text-white" : "hover:bg-surface-container-low"
            }`}
          >
            <Settings className="w-4 h-4" /> Profile Settings
          </button>
        </nav>
      </aside>

      {/* Main Content Area */}
      <section className="flex-1 bg-white border border-outline-variant rounded-2xl p-6 md:p-8 shadow-sm">
        
        {/* Wallet & Rewards Tab */}
        {activeTab === "wallet" && (
          <div className="space-y-8">
            <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30">
              <h2 className="text-md font-bold text-on-surface flex items-center gap-2"><Wallet className="w-5 h-5 text-primary" /> Wallet Details</h2>
              <span className="text-[10px] uppercase tracking-wider font-bold text-outline">Balance Status</span>
            </div>

            {/* Wallet Stats Card */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="bg-primary/5 p-6 rounded-2xl border border-primary/10 text-center">
                <div className="text-[10px] font-bold text-primary uppercase">Available Balance</div>
                <div className="text-2xl font-extrabold text-primary mt-2">₹{profileData.wallet.available_balance.toLocaleString('en-IN')}</div>
              </div>
              <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/20 text-center">
                <div className="text-[10px] font-bold text-outline-variant uppercase">Total Earned</div>
                <div className="text-xl font-extrabold text-on-surface mt-2">₹{profileData.wallet.total_earned.toLocaleString('en-IN')}</div>
              </div>
              <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/20 text-center">
                <div className="text-[10px] font-bold text-outline-variant uppercase">Withdrawn</div>
                <div className="text-xl font-extrabold text-on-surface mt-2">₹{profileData.wallet.withdrawn_amount.toLocaleString('en-IN')}</div>
              </div>
            </div>

            {/* Withdrawal form */}
            <form onSubmit={handleWithdrawal} className="bg-surface-container-low border border-outline-variant/50 p-6 rounded-2xl space-y-4">
              <h4 className="text-xs font-bold text-on-surface flex items-center gap-1.5"><CreditCard className="w-4 h-4 text-primary" /> Request Balance Payout</h4>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-on-surface-variant mb-2">Withdraw Amount (₹)</label>
                  <input
                    type="number"
                    placeholder="e.g. 50"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    className="w-full bg-white border border-outline-variant rounded-xl p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-on-surface-variant mb-2">UPI ID (GooglePay/PhonePe)</label>
                  <input
                    type="text"
                    placeholder="username@okaxis"
                    value={withdrawUpi}
                    onChange={(e) => setWithdrawUpi(e.target.value)}
                    className="w-full bg-white border border-outline-variant rounded-xl p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              {withdrawError && <p className="text-xs text-error font-medium">{withdrawError}</p>}
              {withdrawSuccess && <p className="text-xs text-primary font-medium">{withdrawSuccess}</p>}

              <button type="submit" className="px-6 py-2 bg-primary text-white rounded-xl text-xs font-bold hover:opacity-90 active:scale-95 transition-all">
                Submit Request
              </button>
            </form>

            {/* Withdrawal History List */}
            <div>
              <h3 className="text-xs font-bold text-on-surface mb-4">Payout Transaction Logs</h3>
              <div className="border border-outline-variant rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-surface-container text-on-surface-variant font-bold">
                    <tr>
                      <th className="p-3">Amount</th>
                      <th className="p-3">UPI ID</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Date Requested</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/30">
                    {profileData.withdrawals && profileData.withdrawals.map((w: any) => (
                      <tr key={w.id}>
                        <td className="p-3 font-bold">₹{w.amount}</td>
                        <td className="p-3 text-on-surface-variant">{w.upi_id}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            w.status === 'Paid' ? 'bg-primary/10 text-primary' : w.status === 'Pending' ? 'bg-secondary-container/10 text-secondary-container' : 'bg-error-container/20 text-error'
                          }`}>
                            {w.status}
                          </span>
                        </td>
                        <td className="p-3 text-outline">{new Date(w.requested_date).toLocaleDateString()}</td>
                      </tr>
                    ))}
                    {(!profileData.withdrawals || profileData.withdrawals.length === 0) && (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-text-muted">No withdrawal requests found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Refer & Earn Tab */}
        {activeTab === "referral" && (
          <div className="space-y-8">
            <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30">
              <h2 className="text-md font-bold text-on-surface flex items-center gap-2"><Gift className="w-5 h-5 text-primary" /> Refer Properties & Earn ₹50</h2>
              <span className="text-[10px] uppercase tracking-wider font-bold text-outline">Referral Program</span>
            </div>

            <form onSubmit={handlePostReferral} className="space-y-4 max-w-xl">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Referrer Name</label>
                  <input
                    type="text"
                    placeholder="Your Name"
                    value={refName}
                    onChange={(e) => setRefName(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Referrer Mobile</label>
                  <input
                    type="text"
                    placeholder="Your Contact"
                    value={refMobile}
                    onChange={(e) => setRefMobile(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Owner Name</label>
                  <input
                    type="text"
                    placeholder="Property Owner Name"
                    value={refOwnerName}
                    onChange={(e) => setRefOwnerName(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Owner Mobile</label>
                  <input
                    type="text"
                    placeholder="Owner Contact"
                    value={refOwnerMobile}
                    onChange={(e) => setRefOwnerMobile(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Property Type</label>
                  <select
                    value={refPropType}
                    onChange={(e) => setRefPropType(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs font-semibold focus:outline-none"
                  >
                    <option value="Room">Single Room</option>
                    <option value="PG">PG</option>
                    <option value="Flat">Flat</option>
                    <option value="House">Independent House</option>
                    <option value="Commercial">Commercial</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">City</label>
                  <select
                    value={refCityId}
                    onChange={(e) => setRefCityId(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs font-semibold focus:outline-none"
                  >
                    {citiesList.map((c) => (
                      <option key={c.id} value={c.id.toString()}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface-variant mb-2">Property Address</label>
                <textarea
                  rows={3}
                  placeholder="Enter full address of the referred property..."
                  value={refPropAddress}
                  onChange={(e) => setRefPropAddress(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface-variant mb-2">Referral Notes</label>
                <textarea
                  rows={2}
                  placeholder="Any additional details or preferred contact time..."
                  value={refNotes}
                  onChange={(e) => setRefNotes(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              {refError && <p className="text-xs text-error font-medium">{refError}</p>}
              {refSuccess && <p className="text-xs text-primary font-medium">{refSuccess}</p>}

              <button type="submit" className="px-6 py-3 bg-primary text-white rounded-xl text-xs font-bold hover:opacity-90 active:scale-95 transition-all">
                Submit Referral
              </button>
            </form>

            {/* Submissions queue history */}
            <div>
              <h3 className="text-xs font-bold text-on-surface mb-4">Your Property Referrals Queue</h3>
              <div className="border border-outline-variant rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-surface-container text-on-surface-variant font-bold">
                    <tr>
                      <th className="p-3">Property</th>
                      <th className="p-3">Owner Contact</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">City</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant/30">
                    {profileData.submissions && profileData.submissions.map((s: any) => (
                      <tr key={s.id}>
                        <td className="p-3 font-semibold">{s.property_type}</td>
                        <td className="p-3 text-on-surface-variant">{s.owner_mobile}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            s.status === 'Published' ? 'bg-primary/10 text-primary' : s.status === 'Pending' ? 'bg-secondary-container/10 text-secondary-container' : 'bg-error-container/20 text-error'
                          }`}>
                            {s.status}
                          </span>
                        </td>
                        <td className="p-3 text-outline">{s.city}</td>
                      </tr>
                    ))}
                    {(!profileData.submissions || profileData.submissions.length === 0) && (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-text-muted">No referrals made yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === "notifs" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30">
              <h2 className="text-md font-bold text-on-surface flex items-center gap-2"><Bell className="w-5 h-5 text-primary" /> Notifications</h2>
              <button className="text-[10px] font-bold text-primary hover:underline">Mark all as read</button>
            </div>

            <div className="space-y-3">
              {profileData.notifications && profileData.notifications.map((n: any) => (
                <div key={n.id} className={`p-4 rounded-xl border flex flex-col gap-1 transition-all ${
                  n.is_read ? 'bg-white border-outline-variant/30' : 'bg-primary/5 border-primary/15'
                }`}>
                  <div className="flex justify-between items-center">
                    <h4 className="text-xs font-bold text-on-surface">{n.title}</h4>
                    <span className="text-[9px] text-text-muted">{new Date(n.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="text-xs text-on-surface-variant leading-relaxed">{n.message}</p>
                </div>
              ))}
              {(!profileData.notifications || profileData.notifications.length === 0) && (
                <div className="text-center py-12 text-xs text-text-muted font-medium">You have no notification logs.</div>
              )}
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === "settings" && (
          <div className="space-y-8">
            <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30">
              <h2 className="text-md font-bold text-on-surface flex items-center gap-2"><User className="w-5 h-5 text-primary" /> Profile Settings</h2>
            </div>

            <form onSubmit={handleUpdateProfile} className="space-y-4 max-w-md">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">First Name</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Last Name</label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface-variant mb-2">Phone Number</label>
                <input
                  type="text"
                  placeholder="Enter contact number"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              {updateError && <p className="text-xs text-error font-medium">{updateError}</p>}
              {updateSuccess && <p className="text-xs text-primary font-medium">{updateSuccess}</p>}

              <button type="submit" className="px-6 py-2.5 bg-primary text-white rounded-xl text-xs font-bold hover:opacity-90 active:scale-95 transition-all">
                Save Profile
              </button>
            </form>
          </div>
        )}

      </section>
    </div>
  );
}
