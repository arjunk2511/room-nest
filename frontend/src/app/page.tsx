"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, MapPin, Home, CreditCard, ShieldCheck, Headphones, ArrowRight, Star } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Search form state
  const [city, setCity] = useState("mysore");
  const [type, setType] = useState("1BHK");
  const [maxPrice, setMaxPrice] = useState("");

  useEffect(() => {
    fetch("/api/listings/")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setListings(data.slice(0, 3)); // Grab first 3 listings as featured
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load listings:", err);
        setLoading(false);
      });
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (city) params.append("city", city);
    if (type) params.append("type", type);
    if (maxPrice) params.append("max_price", maxPrice);
    router.push(`/search?${params.toString()}`);
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative w-full h-[650px] flex items-center justify-center overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center transition-transform duration-1000 scale-100 hover:scale-105"
          style={{ 
            backgroundImage: "url('https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1280&q=80')",
            filter: "brightness(0.65)"
          }}
        />
        <div className="relative z-10 w-full max-w-7xl px-4 text-center text-white">
          <h1 className="text-4xl md:text-6xl font-extrabold font-plus-jakarta mb-6 tracking-tight drop-shadow-md">
            Find Your Perfect Home <br className="hidden md:inline" />Without the Stress
          </h1>
          <p className="text-lg md:text-xl font-medium text-white/95 mb-8 max-w-2xl mx-auto">
            Zero brokerage, verified properties, and digital documentation support.
          </p>

          {/* Search Box */}
          <form onSubmit={handleSearch} className="bg-white p-4 rounded-2xl shadow-2xl max-w-4xl mx-auto flex flex-col md:flex-row gap-4 items-center border border-outline-variant/30 text-on-surface">
            <div className="flex-1 w-full border-b md:border-b-0 md:border-r border-outline-variant/50 pb-2 md:pb-0 md:pr-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Location</label>
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-primary shrink-0" />
                <select 
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold bg-transparent"
                >
                  <option value="mysore">Mysore</option>
                  <option value="bangalore">Bangalore</option>
                </select>
              </div>
            </div>

            <div className="flex-1 w-full border-b md:border-b-0 md:border-r border-outline-variant/50 pb-2 md:pb-0 md:pr-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Stay Type</label>
              <div className="flex items-center gap-2">
                <Home className="w-5 h-5 text-primary shrink-0" />
                <select 
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold bg-transparent"
                >
                  <option value="1BHK">1 BHK Flat</option>
                  <option value="2BHK">2 BHK Flat</option>
                  <option value="3BHK">3 BHK Flat</option>
                  <option value="Single Room">Single Room</option>
                  <option value="PG (Men)">PG (Men)</option>
                  <option value="PG (Women)">PG (Women)</option>
                  <option value="Co-living">Co-living</option>
                </select>
              </div>
            </div>

            <div className="flex-1 w-full pb-2 md:pb-0 md:pr-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Max Budget (₹)</label>
              <div className="flex items-center gap-2">
                <span className="text-primary font-bold text-sm shrink-0">₹</span>
                <input 
                  type="number"
                  placeholder="Max Price"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold placeholder:text-outline-variant/80 bg-transparent"
                />
              </div>
            </div>

            <button type="submit" className="w-full md:w-auto bg-primary hover:bg-primary-container text-white p-3.5 rounded-xl flex items-center justify-center transition-all active:scale-95 shadow-md shadow-primary/20 shrink-0">
              <Search className="w-6 h-6" />
            </button>
          </form>

          <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
            <span className="text-white/80 text-sm font-semibold">Popular Areas:</span>
            <Link href="/search?city=mysore&area=gokulam" className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-white text-xs font-semibold border border-white/20 hover:bg-white/20 transition-all">Gokulam</Link>
            <Link href="/search?city=mysore&area=vijayanagar" className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-white text-xs font-semibold border border-white/20 hover:bg-white/20 transition-all">Vijayanagar</Link>
            <Link href="/search?city=mysore&area=hebbal" className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-white text-xs font-semibold border border-white/20 hover:bg-white/20 transition-all">Hebbal</Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-surface-container-low border-b border-outline-variant/30">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div>
            <div className="text-3xl md:text-4xl font-extrabold text-primary font-plus-jakarta">500+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Verified Rooms</div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-extrabold text-primary font-plus-jakarta">100+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Happy Owners</div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-extrabold text-primary font-plus-jakarta">2+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Major Cities</div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-extrabold text-primary font-plus-jakarta">10k+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Renters Served</div>
          </div>
        </div>
      </section>

      {/* Explore Categories */}
      <section className="py-20 max-w-7xl mx-auto px-4 w-full">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">Explore by Stay Type</h2>
          <div className="w-12 h-1 bg-primary rounded-full mx-auto"></div>
        </div>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-6">
          {[
            { type: "1BHK", label: "1 BHK Flats", desc: "Private student living", icon: "🏢" },
            { type: "2BHK", label: "2 BHK Flats", desc: "Perfect for roommates", icon: "🏡" },
            { type: "Single Room", label: "Single Rooms", desc: "Budget friendly spaces", icon: "🛏️" },
            { type: "PG (Men)", label: "Boys PG", desc: "Shared student living", icon: "👨‍🎓" },
            { type: "PG (Women)", label: "Girls PG", desc: "Secure housing", icon: "👩‍🎓" }
          ].map((cat, idx) => (
            <Link 
              key={idx}
              href={`/search?type=${cat.type}`}
              className="bg-white p-6 rounded-2xl text-center property-card-shadow transition-all duration-300 hover:-translate-y-2 border border-outline-variant/30 flex flex-col items-center group cursor-pointer"
            >
              <div className="w-14 h-14 bg-surface-container rounded-full flex items-center justify-center text-2xl mb-4 group-hover:bg-primary-container transition-colors">
                {cat.icon}
              </div>
              <h3 className="text-sm font-bold text-on-surface mb-1">{cat.label}</h3>
              <p className="text-[11px] text-on-surface-variant">{cat.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured Properties */}
      <section className="py-20 bg-surface-container-lowest border-t border-b border-outline-variant/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
            <div>
              <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">Featured Premium Properties</h2>
              <p className="text-sm text-on-surface-variant">Handpicked spaces verified by our operations team.</p>
            </div>
            <Link href="/search" className="text-primary font-bold text-sm flex items-center gap-2 hover:underline">
              View All Listings <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((n) => (
                <div key={n} className="bg-white rounded-2xl h-80 animate-pulse border border-outline-variant/20" />
              ))}
            </div>
          ) : listings.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {listings.map((l) => (
                <Link href={`/listing/${l.id}`} key={l.id} className="bg-white rounded-2xl overflow-hidden property-card-shadow group border border-outline-variant/30 transition-all duration-300 hover:-translate-y-1">
                  <div className="relative h-56 w-full bg-surface-container-high overflow-hidden">
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
                  <div className="p-5">
                    <div className="flex justify-between items-start mb-2 gap-2">
                      <h3 className="text-sm font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">{l.title}</h3>
                      <div className="text-primary font-bold text-sm shrink-0">₹{parseFloat(l.price).toLocaleString('en-IN')}<span className="text-[10px] text-on-surface-variant font-normal">/mo</span></div>
                    </div>
                    <p className="text-xs text-on-surface-variant flex items-center gap-1 mb-4">
                      <MapPin className="w-3.5 h-3.5" /> {l.area?.name || l.location}, {l.city?.name || 'Mysore'}
                    </p>
                    <div className="flex items-center gap-4 py-3 border-t border-outline-variant/30 text-[11px] font-semibold text-text-muted">
                      <span>{l.type}</span>
                      <span>•</span>
                      <span>Deposit: ₹{parseFloat(l.deposit).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-on-surface-variant font-medium">
              No featured listings found. List your property to get started!
            </div>
          )}
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="py-20 max-w-7xl mx-auto px-4 w-full">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">Why Renters Choose RoomNest</h2>
          <p className="text-sm text-on-surface-variant">We make property finding seamless, transparent, and direct.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-8 bg-surface-container-low rounded-2xl border border-transparent hover:border-primary-container/15 transition-all text-center">
            <div className="mb-6 inline-flex p-4 rounded-xl bg-primary/10 text-primary">
              <CreditCard className="w-8 h-8" />
            </div>
            <h3 className="text-md font-bold mb-3">Zero Brokerage</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">Deal directly with verified property owners. Save thousands by skipping agency fees and hidden middleman commissions.</p>
          </div>
          
          <div className="p-8 bg-surface-container-low rounded-2xl border border-transparent hover:border-primary-container/15 transition-all text-center">
            <div className="mb-6 inline-flex p-4 rounded-xl bg-secondary-container/10 text-secondary-container">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <h3 className="text-md font-bold mb-3">Ground Verified Spaces</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">Our operations team personally visits and audits listing details (amenities, location, photos) to guarantee what you see is what you get.</p>
          </div>

          <div className="p-8 bg-surface-container-low rounded-2xl border border-transparent hover:border-primary-container/15 transition-all text-center">
            <div className="mb-6 inline-flex p-4 rounded-xl bg-tertiary/10 text-tertiary">
              <Headphones className="w-8 h-8" />
            </div>
            <h3 className="text-md font-bold mb-3">KYC & E-Agreements</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">Sign digital rental contracts and submit tenant details securely from the dashboard. Easy, paperless execution within minutes.</p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-surface-container-low border-t border-outline-variant/30">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface text-center mb-12">Hear from Our Residents</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex gap-0.5 text-secondary-container mb-4">
                {[1, 2, 3, 4, 5].map((n) => <Star key={n} className="w-4 h-4 fill-secondary-container text-transparent" />)}
              </div>
              <p className="text-xs font-semibold text-on-surface italic mb-6">
                &quot;Found a beautiful 2BHK in Indiranagar in just 2 days. The e-agreement signature process was so smooth and easy.&quot;
              </p>
              <div>
                <h5 className="text-xs font-bold">Ananya Sharma</h5>
                <p className="text-[10px] text-on-surface-variant mt-0.5">Software Engineer</p>
              </div>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex gap-0.5 text-secondary-container mb-4">
                {[1, 2, 3, 4, 5].map((n) => <Star key={n} className="w-4 h-4 fill-secondary-container text-transparent" />)}
              </div>
              <p className="text-xs font-semibold text-on-surface italic mb-6">
                &quot;Highly recommend RoomNest for PG rooms. I verified the curfew times and food choices on the site and booked it instantly.&quot;
              </p>
              <div>
                <h5 className="text-xs font-bold">Rahul Varma</h5>
                <p className="text-[10px] text-on-surface-variant mt-0.5">IIT Student</p>
              </div>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex gap-0.5 text-secondary-container mb-4">
                {[1, 2, 3, 4, 5].map((n) => <Star key={n} className="w-4 h-4 fill-secondary-container text-transparent" />)}
              </div>
              <p className="text-xs font-semibold text-on-surface italic mb-6">
                &quot;As a property owner, managing listings and tracking visitor leads is extremely transparent. Direct whatsapp button is great.&quot;
              </p>
              <div>
                <h5 className="text-xs font-bold">Sanjay K.</h5>
                <p className="text-[10px] text-on-surface-variant mt-0.5">Property Owner</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
