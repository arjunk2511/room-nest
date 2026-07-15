"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getAuthHeader } from "@/lib/supabase";
import { 
  Building, Eye, MessageSquare, PhoneCall, Share2, 
  ToggleLeft, ToggleRight, Download, Users, PlusCircle 
} from "lucide-react";

export default function OwnerDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);

  const fetchDashboard = async () => {
    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    try {
      const res = await fetch("/api/owner/dashboard/", {
        headers: { "Authorization": authHeader }
      });
      const data = await res.json();
      if (data && !data.error) {
        setDashboardData(data);
      } else {
        router.push("/login");
      }
      setLoading(false);
    } catch (err) {
      console.error("Error loading dashboard data:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleToggleSold = async (id: number) => {
    const authHeader = await getAuthHeader();
    if (!authHeader) return;

    try {
      const res = await fetch(`/api/owner/toggle-sold/${id}/`, {
        method: "POST",
        headers: { "Authorization": authHeader }
      });
      const data = await res.json();
      if (data.success) {
        fetchDashboard(); // reload
      }
    } catch (err) {
      console.error("Error toggling status:", err);
    }
  };

  const handleExportCSV = async () => {
    const authHeader = await getAuthHeader();
    if (!authHeader) return;
    
    // In production this will trigger a browser download of the export CSV API
    window.location.href = `/api/leads/export-csv/`;
  };

  if (loading) {
    return <div className="p-12 text-center animate-pulse font-semibold">Loading owner dashboard...</div>;
  }

  if (!dashboardData) {
    return <div className="p-12 text-center text-error font-semibold">Unable to fetch dashboard details.</div>;
  }

  const { stats, listings, leads } = dashboardData;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full flex-1 flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-4 border-b border-outline-variant/30 gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold font-plus-jakarta text-on-surface">Owner Dashboard</h1>
          <p className="text-xs text-on-surface-variant mt-1">Manage your active property listings and track visitor leads.</p>
        </div>
        <button
          onClick={handleExportCSV}
          className="px-5 py-2.5 bg-primary text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-primary/10"
        >
          <Download className="w-4 h-4" /> Export Leads CSV
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-primary/10 text-primary rounded-xl mb-3"><Building className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Listings</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.properties_count}</div>
        </div>
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-primary/10 text-primary rounded-xl mb-3"><Eye className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Total Views</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.total_views}</div>
        </div>
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-secondary-container/10 text-secondary-container rounded-xl mb-3"><MessageSquare className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">WhatsApp Clicks</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.total_whatsapp}</div>
        </div>
        <div className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm text-center">
          <div className="inline-flex p-2.5 bg-tertiary/10 text-tertiary rounded-xl mb-3"><PhoneCall className="w-5 h-5" /></div>
          <div className="text-[10px] font-bold text-outline uppercase">Phone Leads</div>
          <div className="text-xl font-extrabold text-on-surface mt-1">{stats.total_calls}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Properties list */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-sm font-bold text-on-surface">Listed Properties</h2>
          
          <div className="space-y-4">
            {listings && listings.map((l: any) => (
              <div key={l.id} className="bg-white border border-outline-variant rounded-2xl p-4 flex gap-4 items-center justify-between shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-xl bg-surface-container-high overflow-hidden shrink-0">
                    {l.image ? <img src={l.image} alt={l.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-xl">🏢</div>}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-on-surface line-clamp-1">{l.title}</h3>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">{l.location} • ₹{parseFloat(l.price).toLocaleString('en-IN')}/mo</p>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs font-bold">
                  <span className={`px-2 py-0.5 rounded-full text-[9px] ${l.is_sold ? 'bg-error-container/20 text-error' : 'bg-primary/10 text-primary'}`}>
                    {l.is_sold ? "Sold/Rented" : "Active"}
                  </span>
                  <button
                    onClick={() => handleToggleSold(l.id)}
                    className="p-1.5 hover:bg-surface-container rounded-lg text-on-surface-variant"
                    title={l.is_sold ? "Mark as Active" : "Mark as Sold"}
                  >
                    {l.is_sold ? <ToggleRight className="w-6 h-6 text-primary" /> : <ToggleLeft className="w-6 h-6 text-text-muted" />}
                  </button>
                </div>
              </div>
            ))}
            {(!listings || listings.length === 0) && (
              <div className="text-center py-12 bg-white border border-outline-variant rounded-2xl">
                <p className="text-xs text-on-surface-variant">You have not listed any properties yet.</p>
                <Link href="/add-property" className="mt-4 px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold inline-flex items-center gap-1.5 hover:opacity-90 active:scale-95 transition-all">
                  <PlusCircle className="w-4 h-4" /> Post Your First Property
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Leads queue list */}
        <div className="space-y-6">
          <h2 className="text-sm font-bold text-on-surface">Recent Visitor Leads ({leads?.length || 0})</h2>
          
          <div className="space-y-4">
            {leads && leads.map((lead: any) => (
              <div key={lead.id} className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-xs font-bold text-on-surface">{lead.name}</h4>
                    <span className="text-[9px] text-text-muted mt-0.5 block">{lead.lead_type} Lead • {new Date(lead.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                    lead.lead_type === 'WhatsApp' ? 'bg-secondary-container/10 text-secondary-container' : 'bg-primary/10 text-primary'
                  }`}>
                    {lead.lead_type}
                  </span>
                </div>
                <div className="text-[10px] text-on-surface-variant space-y-1 bg-surface-container-low p-2 rounded-lg">
                  <div>📞 {lead.phone || 'No phone provided'}</div>
                  <div>✉️ {lead.email}</div>
                  <div className="text-text-muted italic mt-1 font-medium">Re: {lead.listing_title}</div>
                </div>
              </div>
            ))}
            {(!leads || leads.length === 0) && (
              <div className="text-center py-12 text-xs text-text-muted font-medium bg-white border border-outline-variant rounded-2xl">No visitor inquiries received yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
