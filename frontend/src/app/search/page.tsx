"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Search, MapPin, Filter, X, ShieldCheck } from "lucide-react";

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
  const [minPrice, setMinPrice] = useState(searchParams.get("min_price") || "");
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price") || "");
  const [gender, setGender] = useState(searchParams.get("gender") || "");
  const [furnishing, setFurnishing] = useState(searchParams.get("furnishing") || "");

  const [showMobileFilters, setShowMobileFilters] = useState(false);

  // Load cities & areas
  useEffect(() => {
    fetch("/api/cities-areas/")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCitiesData(data);
          // If no city is selected, default to first available
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
    if (minPrice) params.append("min_price", minPrice);
    if (maxPrice) params.append("max_price", maxPrice);
    if (gender) params.append("gender", gender);
    if (furnishing) params.append("furnishing", furnishing);

    // Sync URL
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
  }, [city, area, type, minPrice, maxPrice, gender, furnishing]);

  const activeCityData = citiesData.find((c) => c.slug === city);
  const areas = activeCityData ? activeCityData.areas : [];

  const handleQuerySearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchListings();
  };

  const clearFilters = () => {
    setQuery("");
    setArea("");
    setType("");
    setMinPrice("");
    setMaxPrice("");
    setGender("");
    setFurnishing("");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full flex-1 flex flex-col">
      {/* Search Header */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <form onSubmit={handleQuerySearch} className="w-full md:max-w-md bg-white border border-outline-variant rounded-xl flex items-center px-3 py-2 shadow-sm focus-within:ring-2 focus-within:ring-primary/20">
          <input
            type="text"
            placeholder="Search by title, facilities, or landmarks..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 border-none focus:outline-none text-sm text-on-surface bg-transparent"
          />
          <button type="submit" className="text-primary-container p-1.5 hover:bg-surface-container rounded-lg transition-colors">
            <Search className="w-4 h-4" />
          </button>
        </form>

        <div className="flex items-center justify-between w-full md:w-auto gap-4">
          <h2 className="text-sm font-semibold text-on-surface-variant">
            Found <span className="text-primary font-bold">{listings.length}</span> properties
          </h2>
          <button 
            onClick={() => setShowMobileFilters(true)}
            className="flex items-center gap-1 px-4 py-2 border border-outline-variant rounded-xl text-xs font-bold md:hidden hover:bg-surface-container transition-colors"
          >
            <Filter className="w-4 h-4" /> Filters
          </button>
        </div>
      </div>

      <div className="flex flex-1 gap-8 items-start relative">
        {/* Filter Sidebar (Desktop) */}
        <aside className="hidden md:block w-64 shrink-0 bg-white border border-outline-variant rounded-2xl p-5 sticky top-20 shadow-sm">
          <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30 mb-5">
            <h3 className="text-sm font-bold text-on-surface flex items-center gap-1.5"><Filter className="w-4 h-4 text-primary" /> Filters</h3>
            <button onClick={clearFilters} className="text-[11px] font-bold text-primary hover:underline">Clear all</button>
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
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Stay Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
              >
                <option value="">All Types</option>
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
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Budget Range (₹)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="w-1/2 bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 text-center focus:outline-none"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="w-1/2 bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 text-center focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Gender Preference</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
              >
                <option value="">Any</option>
                <option value="Any">Co-ed / Any</option>
                <option value="Boys Only">Boys Only</option>
                <option value="Girls Only">Girls Only</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Furnishing</label>
              <select
                value={furnishing}
                onChange={(e) => setFurnishing(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
              >
                <option value="">Any</option>
                <option value="Unfurnished">Unfurnished</option>
                <option value="Semi-Furnished">Semi-Furnished</option>
                <option value="Fully Furnished">Fully Furnished</option>
              </select>
            </div>
          </div>
        </aside>

        {/* Listings Catalog */}
        <section className="flex-1 w-full">
          {loading ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="bg-white rounded-2xl h-64 animate-pulse border border-outline-variant/20" />
              ))}
            </div>
          ) : listings.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {listings.map((l) => (
                <Link href={`/listing/${l.id}`} key={l.id} className="bg-white rounded-2xl overflow-hidden property-card-shadow group border border-outline-variant/30 flex flex-col transition-all duration-300 hover:-translate-y-1">
                  <div className="relative h-48 w-full bg-surface-container-high overflow-hidden shrink-0">
                    {l.image ? (
                      <img 
                        src={l.image} 
                        alt={l.title} 
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-4xl">🏢</div>
                    )}
                    {l.is_verified && (
                      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur text-primary px-3 py-1 rounded-full text-[10px] font-bold flex items-center gap-1 shadow-md">
                        <ShieldCheck className="w-3.5 h-3.5 fill-primary text-white" /> Verified
                      </div>
                    )}
                  </div>
                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-2 gap-2">
                        <h3 className="text-sm font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">{l.title}</h3>
                        <div className="text-primary font-bold text-sm shrink-0">₹{parseFloat(l.price).toLocaleString('en-IN')}<span className="text-[10px] text-on-surface-variant font-normal">/mo</span></div>
                      </div>
                      <p className="text-xs text-on-surface-variant flex items-center gap-1 mb-3">
                        <MapPin className="w-3.5 h-3.5" /> {l.area?.name || l.location}, {l.city?.name || 'Mysore'}
                      </p>
                      <p className="text-xs text-on-surface-variant line-clamp-2 mb-4 leading-relaxed">{l.description}</p>
                    </div>
                    <div className="flex items-center justify-between py-3 border-t border-outline-variant/30 text-[11px] font-semibold text-text-muted">
                      <span>{l.type}</span>
                      <span>Deposit: ₹{parseFloat(l.deposit).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 bg-white border border-outline-variant rounded-2xl">
              <h3 className="text-md font-bold text-on-surface mb-2">No Properties Found</h3>
              <p className="text-xs text-on-surface-variant max-w-md mx-auto">We couldn&apos;t find any active listings matching your filters. Try clearing some criteria or expanding your price range.</p>
              <button onClick={clearFilters} className="mt-4 px-6 py-2 bg-primary text-white rounded-xl text-xs font-bold hover:opacity-90 active:scale-95 transition-all">Reset Filters</button>
            </div>
          )}
        </section>
      </div>

      {/* Mobile Filters Drawer */}
      {showMobileFilters && (
        <div className="fixed inset-0 bg-black/50 z-50 flex justify-end md:hidden">
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
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Stay Type</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
                  >
                    <option value="">All Types</option>
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
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Budget Range (₹)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      className="w-1/2 bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 text-center focus:outline-none"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      className="w-1/2 bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 text-center focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Gender Preference</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
                  >
                    <option value="">Any</option>
                    <option value="Any">Co-ed / Any</option>
                    <option value="Boys Only">Boys Only</option>
                    <option value="Girls Only">Girls Only</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Furnishing</label>
                  <select
                    value={furnishing}
                    onChange={(e) => setFurnishing(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl text-xs font-semibold p-2.5 focus:outline-none"
                  >
                    <option value="">Any</option>
                    <option value="Unfurnished">Unfurnished</option>
                    <option value="Semi-Furnished">Semi-Furnished</option>
                    <option value="Fully Furnished">Fully Furnished</option>
                  </select>
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
    <Suspense fallback={<div className="p-8 text-center animate-pulse">Loading search platform...</div>}>
      <SearchContent />
    </Suspense>
  );
}
