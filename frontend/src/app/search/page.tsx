"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Search, MapPin, Filter, X, ShieldCheck, Heart, 
  ChevronRight, Wifi, Shield, Car, Bolt, SlidersHorizontal, ArrowUpDown, CheckCircle2
} from "lucide-react";
import { getAuthHeader } from "@/lib/supabase";

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [citiesData, setCitiesData] = useState<any[]>([]);

  // Filter States
  const [query, setQuery] = useState(searchParams.get("query") || "");
  const [city, setCity] = useState(searchParams.get("city") || "");
  const [area, setArea] = useState(searchParams.get("area") || "");
  const [type, setType] = useState(searchParams.get("type") || "");
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price") || "75000");
  const [gender, setGender] = useState(searchParams.get("gender") || "");
  const [furnishing, setFurnishing] = useState(searchParams.get("furnishing") || "");
  
  // Sort State
  const [sortBy, setSortBy] = useState("Newest First");
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Load cities & areas
  useEffect(() => {
    fetch("/api/cities-areas/")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCitiesData(data);
          // If no city is selected, default to the first one available
          if (!city && data.length > 0) {
            setCity(data[0].slug);
          }
        }
      })
      .catch((err) => console.error("Error loading cities:", err));
  }, []);

  // Fetch listings based on parameters
  const fetchListings = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (query) params.append("query", query);
    if (city) params.append("city", city);
    if (area) params.append("area", area);
    if (type) params.append("type", type);
    if (maxPrice) params.append("max_price", maxPrice);
    if (gender) params.append("gender", gender);
    if (furnishing) params.append("furnishing", furnishing);

    // Sync browser URL
    router.replace(`/search?${params.toString()}`);

    fetch(`/api/listings/?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setListings(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching search listings:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchListings();
  }, [city, area, type, maxPrice, gender, furnishing]);

  const activeCityData = citiesData.find((c) => c.slug === city);
  const areas = activeCityData ? activeCityData.areas : [];

  const handleQuerySearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchListings();
  };

  const handleToggleWishlist = async (listingId: number) => {
    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    fetch(`/api/listings/${listingId}/toggle-wishlist/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": authHeader
      }
    }).then((res) => res.json()).then((data) => {
      if (data.status === "success") {
        alert(data.saved ? "Added to Wishlist!" : "Removed from Wishlist!");
      }
    });
  };

  const clearFilters = () => {
    setQuery("");
    setArea("");
    setType("");
    setMaxPrice("75000");
    setGender("");
    setFurnishing("");
  };

  // Client-side sorting
  const sortedListings = [...listings].sort((a, b) => {
    if (sortBy === "Price: Low to High") {
      return a.price - b.price;
    }
    if (sortBy === "Price: High to Low") {
      return b.price - a.price;
    }
    // Newest First (default)
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-8 w-full flex-1 flex flex-col min-h-screen">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 mb-6 text-on-surface-variant text-xs">
        <Link href="/" className="hover:text-primary transition-colors">Home</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link href="/search" className="hover:text-primary transition-colors">Properties</Link>
        {activeCityData && (
          <>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="font-semibold text-on-surface">{activeCityData.name}</span>
          </>
        )}
      </nav>

      {/* Top Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface">
            {sortedListings.length} Results for {activeCityData?.name || "Bangalore"}
          </h1>
          <p className="text-xs text-on-surface-variant mt-1">Showing premium properties with high-intent verified tags</p>
        </div>

        <div className="flex items-center gap-3 bg-white p-1 rounded-xl border border-outline-variant shadow-sm w-full md:w-auto">
          <span className="text-xs pl-3 text-on-surface-variant font-bold flex items-center gap-1"><ArrowUpDown className="w-3.5 h-3.5" /> Sort by:</span>
          <select 
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-transparent border-none focus:ring-0 text-xs font-semibold text-on-surface cursor-pointer pr-8 py-1.5 focus:outline-none"
          >
            <option value="Newest First">Newest First</option>
            <option value="Price: Low to High">Price: Low to High</option>
            <option value="Price: High to Low">Price: High to Low</option>
          </select>
        </div>
      </div>

      {/* Search bar inside header */}
      <div className="mb-8 w-full md:max-w-lg">
        <form onSubmit={handleQuerySearch} className="bg-white border border-outline-variant rounded-xl flex items-center px-4 py-2.5 shadow-sm focus-within:ring-2 focus-within:ring-primary/25">
          <input
            type="text"
            placeholder="Search by title, location, or landmarks..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 border-none focus:outline-none text-xs text-on-surface bg-transparent"
          />
          <button type="submit" className="text-primary p-1.5 hover:bg-surface-container rounded-lg transition-colors">
            <Search className="w-4 h-4" />
          </button>
        </form>
      </div>

      <div className="flex flex-1 gap-8 items-start relative">
        {/* Filter Sidebar (Desktop) */}
        <aside className="hidden lg:block w-72 shrink-0 bg-white border border-outline-variant rounded-2xl p-6 sticky top-20 shadow-md">
          <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30 mb-6">
            <h2 className="text-sm font-bold text-on-surface flex items-center gap-2"><SlidersHorizontal className="w-4 h-4 text-primary" /> Filters</h2>
            <button onClick={clearFilters} className="text-xs font-bold text-primary hover:underline">Clear All</button>
          </div>

          <div className="space-y-6">
            {/* City Selection */}
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">City</label>
              <select
                value={city}
                onChange={(e) => { setCity(e.target.value); setArea(""); }}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-3 focus:outline-none"
              >
                {citiesData.map((c) => (
                  <option key={c.id} value={c.slug}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Area Selector */}
            {areas.length > 0 && (
              <div>
                <label className="block text-xs font-bold text-on-surface-variant mb-2">Area / Locality</label>
                <select
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-3 focus:outline-none"
                >
                  <option value="">All Localities</option>
                  {areas.map((a: any) => (
                    <option key={a.id} value={a.slug}>{a.name}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Budget Range */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-on-surface-variant">Budget Limit</label>
                <span className="text-xs font-extrabold text-primary">₹{parseInt(maxPrice).toLocaleString('en-IN')}</span>
              </div>
              <input
                type="range"
                min="5000"
                max="100000"
                step="2500"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                className="w-full h-2 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary"
              />
              <div className="flex justify-between text-[10px] text-text-muted mt-2 font-bold">
                <span>₹5,000</span>
                <span>₹1,00,000+</span>
              </div>
            </div>

            {/* Stay Type */}
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Stay Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-3 focus:outline-none"
              >
                <option value="">All Types</option>
                <option value="Apartment">Apartment</option>
                <option value="1BHK">1 BHK Flat</option>
                <option value="2BHK">2 BHK Flat</option>
                <option value="3BHK">3 BHK Flat</option>
                <option value="Single Room">Single Room</option>
                <option value="PG (Men)">PG (Men)</option>
                <option value="PG (Women)">PG (Women)</option>
                <option value="Co-living">Co-living</option>
              </select>
            </div>

            {/* Furnished Status */}
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Furnished Status</label>
              <div className="flex flex-wrap gap-2">
                {["Unfurnished", "Semi-Furnished", "Fully Furnished"].map((f) => (
                  <button
                    type="button"
                    key={f}
                    onClick={() => setFurnishing(furnishing === f ? "" : f)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold border transition-all ${
                      furnishing === f 
                        ? "bg-primary border-primary text-white" 
                        : "border-outline text-on-surface-variant hover:border-primary"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {/* Gender Preference */}
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Gender Preference</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: "Any", label: "Co-ed" },
                  { value: "Boys Only", label: "Boys" },
                  { value: "Girls Only", label: "Girls" }
                ].map((g) => (
                  <button
                    type="button"
                    key={g.value}
                    onClick={() => setGender(gender === g.value ? "" : g.value)}
                    className={`py-2 rounded-lg text-xs font-bold border text-center transition-all ${
                      gender === g.value 
                        ? "bg-primary border-primary text-white" 
                        : "border-outline text-on-surface-variant hover:bg-surface-container"
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Listings Catalog */}
        <section className="flex-1 w-full">
          {/* Mobile Filter Trigger */}
          <div className="flex justify-between items-center mb-6 lg:hidden">
            <span className="text-xs text-on-surface-variant font-semibold">Found {sortedListings.length} listings</span>
            <button 
              onClick={() => setShowMobileFilters(true)}
              className="flex items-center gap-1.5 px-4 py-2 border border-outline rounded-xl text-xs font-bold hover:bg-surface-container transition-colors"
            >
              <Filter className="w-4 h-4 text-primary" /> Filters
            </button>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="bg-white rounded-2xl h-64 animate-pulse border border-outline-variant/20" />
              ))}
            </div>
          ) : sortedListings.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {sortedListings.map((l) => (
                <div key={l.id} className="group bg-white rounded-2xl overflow-hidden property-card-shadow transition-all duration-300 border border-outline-variant relative flex flex-col">
                  {/* Top badges */}
                  <div className="absolute top-4 left-4 z-10 flex gap-2">
                    {l.is_verified && (
                      <span className="bg-primary text-white px-3 py-1 rounded-full text-[10px] font-bold flex items-center gap-1 shadow-md">
                        <ShieldCheck className="w-3.5 h-3.5 fill-white text-primary" /> Verified
                      </span>
                    )}
                    {new Date(l.created_at).getTime() > Date.now() - 7 * 24 * 60 * 60 * 1000 && (
                      <span className="bg-secondary-container text-white px-3 py-1 rounded-full text-[10px] font-bold shadow-md">
                        New Listing
                      </span>
                    )}
                  </div>

                  <div className="relative h-56 overflow-hidden bg-surface-container-high shrink-0">
                    {l.image ? (
                      <img 
                        src={l.image} 
                        alt={l.title} 
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-4xl bg-surface-container-high">🏢</div>
                    )}
                    <button 
                      onClick={() => handleToggleWishlist(l.id)} 
                      className="absolute top-4 right-4 p-2 bg-white/80 backdrop-blur rounded-full text-on-surface-variant hover:text-error transition-colors shadow-md"
                    >
                      <Heart className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-2 gap-2">
                        <div>
                          <h3 className="text-sm font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">{l.title}</h3>
                          <p className="text-[11px] text-on-surface-variant mt-0.5">{l.area?.name || l.location}, {l.city?.name || 'Mysore'}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 my-4 py-3 border-y border-outline-variant/30 text-center">
                        <div className="border-r border-outline-variant/20">
                          <p className="text-primary text-sm font-bold">₹{parseFloat(l.price).toLocaleString('en-IN')}</p>
                          <p className="text-[9px] text-on-surface-variant uppercase font-semibold">Monthly Rent</p>
                        </div>
                        <div className="border-r border-outline-variant/20">
                          <p className="text-on-surface text-sm font-bold">₹{parseFloat(l.deposit).toLocaleString('en-IN')}</p>
                          <p className="text-[9px] text-on-surface-variant uppercase font-semibold">Deposit</p>
                        </div>
                        <div>
                          <p className="text-on-surface text-sm font-bold">{l.type}</p>
                          <p className="text-[9px] text-on-surface-variant uppercase font-semibold">Stay Type</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-outline-variant/10">
                      <div className="flex gap-2">
                        {l.facilities && l.facilities.slice(0, 3).map((facility: string, idx: number) => {
                          const iconMap: { [key: string]: any } = {
                            wifi: <Wifi className="w-3.5 h-3.5 text-tertiary" />,
                            parking: <Car className="w-3.5 h-3.5 text-tertiary" />,
                            ac: <Bolt className="w-3.5 h-3.5 text-tertiary" />,
                            security: <Shield className="w-3.5 h-3.5 text-tertiary" />
                          };
                          const lower = facility.toLowerCase();
                          let icon = <CheckCircle2 className="w-3.5 h-3.5 text-tertiary" />;
                          for (const key in iconMap) {
                            if (lower.includes(key)) {
                              icon = iconMap[key];
                              break;
                            }
                          }
                          return (
                            <div key={idx} className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center" title={facility}>
                              {icon}
                            </div>
                          );
                        })}
                      </div>
                      <Link href={`/listing/${l.id}`} className="bg-on-surface text-white px-4 py-2 rounded-xl text-xs font-bold hover:bg-primary transition-all active:scale-95 shadow-sm">
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 bg-white border border-outline-variant rounded-2xl shadow-sm">
              <h3 className="text-sm font-bold text-on-surface mb-2">No Properties Found</h3>
              <p className="text-xs text-on-surface-variant max-w-md mx-auto">We couldn&apos;t find any active listings matching your filters. Try clearing some criteria or expanding your price range.</p>
              <button onClick={clearFilters} className="mt-4 px-6 py-2 bg-primary text-white rounded-xl text-xs font-bold hover:opacity-90 active:scale-95 transition-all">Reset Filters</button>
            </div>
          )}
        </section>
      </div>

      {/* Mobile Filters Drawer */}
      {showMobileFilters && (
        <div className="fixed inset-0 bg-black/50 z-50 flex justify-end lg:hidden">
          <div className="w-80 bg-white h-full p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30 mb-6">
                <h3 className="text-sm font-bold text-on-surface flex items-center gap-1.5"><Filter className="w-4 h-4 text-primary" /> Filters</h3>
                <button onClick={() => setShowMobileFilters(false)} className="p-1 hover:bg-surface-container rounded-lg"><X className="w-5 h-5" /></button>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">City</label>
                  <select
                    value={city}
                    onChange={(e) => { setCity(e.target.value); setArea(""); }}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
                  >
                    {citiesData.map((c) => (
                      <option key={c.id} value={c.slug}>{c.name}</option>
                    ))}
                  </select>
                </div>

                {areas.length > 0 && (
                  <div>
                    <label className="block text-xs font-bold text-on-surface-variant mb-2">Area / Locality</label>
                    <select
                      value={area}
                      onChange={(e) => setArea(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
                    >
                      <option value="">All Localities</option>
                      {areas.map((a: any) => (
                        <option key={a.id} value={a.slug}>{a.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-bold text-on-surface-variant">Budget Limit</label>
                    <span className="text-xs font-extrabold text-primary">₹{parseInt(maxPrice).toLocaleString('en-IN')}</span>
                  </div>
                  <input
                    type="range"
                    min="5000"
                    max="100000"
                    step="2500"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    className="w-full h-2 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Stay Type</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
                  >
                    <option value="">All Types</option>
                    <option value="Apartment">Apartment</option>
                    <option value="1BHK">1 BHK Flat</option>
                    <option value="2BHK">2 BHK Flat</option>
                    <option value="3BHK">3 BHK Flat</option>
                    <option value="Single Room">Single Room</option>
                    <option value="PG (Men)">PG (Men)</option>
                    <option value="PG (Women)">PG (Women)</option>
                    <option value="Co-living">Co-living</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Furnished Status</label>
                  <div className="flex flex-wrap gap-2">
                    {["Unfurnished", "Semi-Furnished", "Fully Furnished"].map((f) => (
                      <button
                        type="button"
                        key={f}
                        onClick={() => setFurnishing(furnishing === f ? "" : f)}
                        className={`px-3 py-1.5 rounded-full text-xs font-bold border transition-all ${
                          furnishing === f 
                            ? "bg-primary border-primary text-white" 
                            : "border-outline text-on-surface-variant hover:border-primary"
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Gender Preference</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { value: "Any", label: "Co-ed" },
                      { value: "Boys Only", label: "Boys" },
                      { value: "Girls Only", label: "Girls" }
                    ].map((g) => (
                      <button
                        type="button"
                        key={g.value}
                        onClick={() => setGender(gender === g.value ? "" : g.value)}
                        className={`py-2 rounded-lg text-xs font-bold border text-center transition-all ${
                          gender === g.value 
                            ? "bg-primary border-primary text-white" 
                            : "border-outline text-on-surface-variant hover:bg-surface-container"
                        }`}
                      >
                        {g.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-6 border-t border-outline-variant/30 mt-6">
              <button 
                onClick={clearFilters}
                className="w-1/2 py-3 rounded-xl border border-outline-variant text-xs font-bold hover:bg-surface-container-low transition-colors"
              >
                Reset
              </button>
              <button 
                onClick={() => setShowMobileFilters(false)}
                className="w-1/2 py-3 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center animate-pulse font-semibold">Loading search platform...</div>}>
      <SearchContent />
    </Suspense>
  );
}
